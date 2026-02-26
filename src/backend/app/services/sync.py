"""EEX sync orchestrator service.

Usage (CLI — FR-018, FR-020):
    python -m app.services.sync --backfill   # one-time historical backfill
    python -m app.services.sync --manual     # incremental daily sync
"""
from __future__ import annotations

import argparse
import asyncio
import sys
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

import httpx
import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.models.auction import Auction
from app.models.auction_event import AuctionEvent
from app.models.sync_log import SyncLog
from app.services.parser import (
    parse_zip_archive,
    scrape_auction_calendar,
    scrape_auction_events,
    scrape_latest_results,
)

logger = structlog.get_logger("sync")

# Known EEX ZIP archive URLs for historical backfill
_BACKFILL_ZIPS = [
    "/fileadmin/EEX/Downloads/Registry_Services/French_Auctions_for_Guarantees_of_Origin/GO_2019-2023_Global_Results.zip",
    "/fileadmin/EEX/Downloads/Registry_Services/French_Auctions_for_Guarantees_of_Origin/20251119_GO_2024_2025_GLOBAL_Results.zip",
    "/fileadmin/EEX/Downloads/Registry_Services/French_Auctions_for_Guarantees_of_Origin/20260220_GO_2026_GLOBAL_Results.zip",
]

_DOWNLOADS_DIR = Path("data/downloads")


class SyncService:
    """Orchestrates EEX data synchronisation."""

    def __init__(
        self,
        database_url: str | None = None,
        eex_base_url: str | None = None,
    ) -> None:
        from app.config import settings

        self._database_url = database_url or settings.database_url
        self._eex_base_url = (eex_base_url or settings.eex_base_url).rstrip("/")
        _DOWNLOADS_DIR.mkdir(parents=True, exist_ok=True)

    def _make_engine(self) -> AsyncEngine:
        return create_async_engine(self._database_url, pool_pre_ping=True)

    # ─── Upsert logic ────────────────────────────────────────────────────────

    async def _upsert_record(
        self,
        session: AsyncSession,
        data: dict[str, Any],
    ) -> str:
        """Upsert one auction record. Returns 'added' | 'updated' | 'skipped'."""
        stmt = select(Auction).where(
            Auction.auction_date == data.get("auction_date"),
            Auction.region == data.get("region"),
            Auction.production_period == data.get("production_period"),
            Auction.technology == data.get("technology"),
        )
        result = await session.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing is None:
            session.add(Auction(**data))
            return "added"

        # Fill NULL fields only — never overwrite non-NULL values
        changed = False
        skip_fields = {
            "id", "auction_date", "region", "production_period",
            "technology", "created_at", "updated_at",
        }
        for field, value in data.items():
            if field in skip_fields:
                continue
            current = getattr(existing, field, None)
            if current is None and value is not None:
                setattr(existing, field, value)
                changed = True

        return "updated" if changed else "skipped"

    async def _bulk_upsert(
        self,
        session: AsyncSession,
        records: list[dict[str, Any]],
    ) -> tuple[int, int, int]:
        """Upsert a batch of records, flushing in chunks.

        Returns (added, updated, skipped).
        """
        added = updated = skipped = 0
        chunk_size = 200

        for i in range(0, len(records), chunk_size):
            chunk = records[i : i + chunk_size]
            for record in chunk:
                outcome = await self._upsert_record(session, record)
                if outcome == "added":
                    added += 1
                elif outcome == "updated":
                    updated += 1
                else:
                    skipped += 1
            await session.flush()

        return added, updated, skipped

    # ─── Transition upcoming → past ──────────────────────────────────────────

    async def _transition_upcoming_to_past(
        self,
        session: AsyncSession,
        result_records: list[dict[str, Any]],
    ) -> int:
        """Transition upcoming auction records to past when results arrive."""
        transitioned = 0
        result_dates = {
            r["auction_date"] for r in result_records if r.get("auction_date")
        }

        for auction_date in result_dates:
            stmt = select(Auction).where(
                Auction.auction_date == auction_date,
                Auction.status == "upcoming",
            )
            result = await session.execute(stmt)
            upcoming_records = result.scalars().all()

            for record in upcoming_records:
                record.status = "past"
                transitioned += 1

        if transitioned:
            await session.flush()
        return transitioned

    # ─── Remove vanished upcoming auctions ───────────────────────────────────

    async def _remove_vanished_calendar_entries(
        self,
        session: AsyncSession,
        calendar_dates: set[date],
    ) -> int:
        """Remove upcoming records whose dates no longer appear on the calendar."""
        stmt = select(Auction).where(
            Auction.status == "upcoming",
            Auction.auction_date >= date.today(),
        )
        result = await session.execute(stmt)
        current_upcoming = result.scalars().all()

        removed = 0
        for record in current_upcoming:
            if record.auction_date not in calendar_dates:
                await session.delete(record)
                removed += 1

        if removed:
            await session.flush()
        return removed

    # ─── AuctionEvent upsert ─────────────────────────────────────────────────

    async def _upsert_auction_event(
        self,
        session: AsyncSession,
        event_dict: dict[str, Any],
    ) -> str:
        """Upsert one AuctionEvent by event_date. Returns 'added' | 'skipped'."""
        event_date = event_dict["event_date"]
        stmt = select(AuctionEvent).where(AuctionEvent.event_date == event_date)
        result = await session.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing is None:
            session.add(AuctionEvent(
                event_date=event_date,
                is_cancelled=event_dict.get("is_cancelled", False),
                auctioning_month=event_dict.get("auctioning_month"),
                production_month=event_dict.get("production_month"),
                order_book_open=event_dict.get("order_book_open"),
                cash_trading_limits_modification=event_dict.get("cash_trading_limits_modification"),
                order_book_close=event_dict.get("order_book_close"),
                order_matching=event_dict.get("order_matching"),
            ))
            return "added"

        # Update nullable detail fields if new values are available
        _detail_fields = (
            "auctioning_month",
            "production_month",
            "order_book_open",
            "cash_trading_limits_modification",
            "order_book_close",
            "order_matching",
        )
        for field in _detail_fields:
            new_val = event_dict.get(field)
            if new_val is not None:
                setattr(existing, field, new_val)

        return "skipped"

    async def _bulk_upsert_auction_events(
        self,
        session: AsyncSession,
        event_dicts: list[dict[str, Any]],
    ) -> tuple[int, int]:
        """Upsert a batch of AuctionEvents. Returns (added, skipped)."""
        added = skipped = 0
        for event_dict in event_dicts:
            outcome = await self._upsert_auction_event(session, event_dict)
            if outcome == "added":
                added += 1
            else:
                skipped += 1
        if added:
            await session.flush()
        return added, skipped

    async def _link_auctions_to_events(
        self,
        session: AsyncSession,
    ) -> int:
        """Set auction_event_id on Auction rows that match an AuctionEvent by date.

        Only updates rows where auction_event_id IS NULL to avoid re-linking.
        Returns the number of rows linked.
        """
        # Fetch all AuctionEvents to build a date → id lookup
        events_result = await session.execute(select(AuctionEvent))
        event_by_date: dict[date, int] = {
            e.event_date: e.id for e in events_result.scalars().all()
        }
        if not event_by_date:
            return 0

        # Fetch Auction rows with no event link whose date is in the event map
        unlinked_stmt = select(Auction).where(
            Auction.auction_event_id.is_(None),
            Auction.auction_date.in_(list(event_by_date.keys())),
        )
        unlinked_result = await session.execute(unlinked_stmt)
        unlinked = unlinked_result.scalars().all()

        linked = 0
        for auction in unlinked:
            event_id = event_by_date.get(auction.auction_date)
            if event_id is not None:
                auction.auction_event_id = event_id
                linked += 1

        if linked:
            await session.flush()
        return linked

    async def _mark_cancelled_events(
        self,
        session: AsyncSession,
        live_event_dates: set[date],
    ) -> int:
        """Mark future AuctionEvents as cancelled when absent from the live calendar.

        Only considers events with event_date >= today; past events are expected
        not to appear on the live calendar and must not be auto-cancelled.
        Already-cancelled events are excluded from the count.
        Returns the number of events newly marked as cancelled.
        """
        stmt = select(AuctionEvent).where(
            AuctionEvent.event_date >= date.today(),
            AuctionEvent.is_cancelled.is_(False),
        )
        result = await session.execute(stmt)
        upcoming_events = result.scalars().all()

        cancelled = 0
        for event in upcoming_events:
            if event.event_date not in live_event_dates:
                event.is_cancelled = True
                cancelled += 1

        if cancelled:
            await session.flush()
            logger.info("auction_events_cancelled", count=cancelled)
        return cancelled

    # ─── SyncLog helpers ─────────────────────────────────────────────────────

    async def _create_sync_log(
        self, session: AsyncSession, sync_type: str
    ) -> SyncLog:
        log = SyncLog(
            run_timestamp=datetime.now(tz=UTC),
            outcome="running",
            sync_type=sync_type,
        )
        session.add(log)
        await session.flush()
        return log

    async def _finish_sync_log(
        self,
        session: AsyncSession,
        log: SyncLog,
        outcome: str,
        added: int = 0,
        updated: int = 0,
        skipped: int = 0,
        error_message: str | None = None,
    ) -> None:
        log.completed_at = datetime.now(tz=UTC)
        log.outcome = outcome
        log.records_added = added
        log.records_updated = updated
        log.records_skipped = skipped
        log.error_message = error_message
        await session.flush()

    # ─── Download helper ─────────────────────────────────────────────────────

    async def _download_zip(
        self, http_client: httpx.AsyncClient, path: str
    ) -> Path | None:
        """Download a ZIP file to the downloads cache. Returns local path."""
        filename = Path(path).name
        local_path = _DOWNLOADS_DIR / filename

        if local_path.exists():
            logger.info("zip_cache_hit", filename=filename)
            return local_path

        url = f"{self._eex_base_url}{path}"
        logger.info("downloading_zip", url=url)
        try:
            async with http_client.stream(
                "GET", url, follow_redirects=True, timeout=120.0
            ) as r:
                r.raise_for_status()
                with open(local_path, "wb") as f:
                    async for chunk in r.aiter_bytes(chunk_size=8192):
                        f.write(chunk)
            logger.info(
                "zip_downloaded", filename=filename, size=local_path.stat().st_size
            )
            return local_path
        except Exception as exc:
            logger.error("zip_download_failed", url=url, error=str(exc))
            # Remove incomplete file
            if local_path.exists():
                local_path.unlink()
            return None

    # ─── Public sync methods ──────────────────────────────────────────────────

    async def run_backfill(self) -> tuple[int, int, int]:
        """Download all historical ZIP archives and parse them into the DB.

        Returns (added, updated, skipped).
        """
        engine = self._make_engine()
        session_factory = async_sessionmaker(engine, expire_on_commit=False)
        total_added = total_updated = total_skipped = 0

        async with session_factory() as session:
            sync_log = await self._create_sync_log(session, "backfill")
            await session.commit()

            try:
                async with httpx.AsyncClient() as http_client:
                    for zip_path in _BACKFILL_ZIPS:
                        local = await self._download_zip(http_client, zip_path)
                        if local is None:
                            continue

                        records = await parse_zip_archive(local)
                        logger.info(
                            "backfill_zip_parsed",
                            filename=local.name,
                            records=len(records),
                        )

                        async with session_factory() as inner_session:
                            added, updated, skipped = await self._bulk_upsert(
                                inner_session, records
                            )
                            await inner_session.commit()

                        total_added += added
                        total_updated += updated
                        total_skipped += skipped
                        logger.info(
                            "backfill_zip_done",
                            filename=local.name,
                            added=added,
                            updated=updated,
                            skipped=skipped,
                        )

                async with session_factory() as final_session:
                    log_stmt = select(SyncLog).where(SyncLog.id == sync_log.id)
                    result = await final_session.execute(log_stmt)
                    log_record = result.scalar_one()
                    await self._finish_sync_log(
                        final_session,
                        log_record,
                        "success",
                        total_added,
                        total_updated,
                        total_skipped,
                    )
                    await final_session.commit()

            except Exception as exc:
                error_msg = str(exc)
                logger.error("backfill_failed", error=error_msg)
                async with session_factory() as err_session:
                    log_stmt = select(SyncLog).where(SyncLog.id == sync_log.id)
                    err_result = await err_session.execute(log_stmt)
                    err_log: SyncLog | None = err_result.scalar_one_or_none()
                    if err_log:
                        await self._finish_sync_log(
                            err_session, err_log, "failure", error_message=error_msg
                        )
                    await err_session.commit()
                raise

        await engine.dispose()
        return total_added, total_updated, total_skipped

    async def run_daily(self) -> tuple[int, int, int]:
        """Run the incremental daily sync: latest results + calendar update.

        Returns (added, updated, skipped).
        """
        engine = self._make_engine()
        session_factory = async_sessionmaker(engine, expire_on_commit=False)
        total_added = total_updated = total_skipped = 0

        async with session_factory() as session:
            sync_log = await self._create_sync_log(session, "daily")
            await session.commit()

        try:
            async with httpx.AsyncClient() as http_client:
                # 1. Scrape latest results
                result_records = await scrape_latest_results(
                    self._eex_base_url, http_client
                )

                # 2. Scrape calendar
                calendar_records = await scrape_auction_calendar(
                    self._eex_base_url, http_client
                )

                # 3. Scrape auction events from EEX calendar
                event_dicts = await scrape_auction_events(
                    self._eex_base_url, http_client
                )

            async with session_factory() as session:
                # 4. Transition upcoming → past for dates with new results
                transitions = await self._transition_upcoming_to_past(
                    session, result_records
                )
                if transitions:
                    logger.info("transitioned_to_past", count=transitions)

                # 5. Upsert result records
                added, updated, skipped = await self._bulk_upsert(
                    session, result_records
                )
                total_added += added
                total_updated += updated
                total_skipped += skipped

                # 6. Upsert calendar records
                cal_added, cal_updated, cal_skipped = await self._bulk_upsert(
                    session, calendar_records
                )
                total_added += cal_added
                total_updated += cal_updated
                total_skipped += cal_skipped

                # 7. Remove vanished upcoming entries
                calendar_dates = {
                    r["auction_date"]
                    for r in calendar_records
                    if isinstance(r.get("auction_date"), date)
                }
                removed = await self._remove_vanished_calendar_entries(
                    session, calendar_dates
                )
                if removed:
                    logger.info("removed_vanished_upcoming", count=removed)

                # 8. Upsert auction events
                live_event_dates = {d["event_date"] for d in event_dicts}
                ev_added, ev_skipped = await self._bulk_upsert_auction_events(
                    session, event_dicts
                )

                # 9. Link existing auctions to their events by date
                linked = await self._link_auctions_to_events(session)

                # 10. Mark cancelled events (future dates absent from live calendar)
                cancelled = await self._mark_cancelled_events(
                    session, live_event_dates
                )

                logger.info(
                    "auction_events_synced",
                    added=ev_added,
                    skipped=ev_skipped,
                    linked=linked,
                    cancelled=cancelled,
                )

                # 11. Finalize sync log
                log_stmt = select(SyncLog).where(SyncLog.id == sync_log.id)
                result = await session.execute(log_stmt)
                log_record = result.scalar_one()
                await self._finish_sync_log(
                    session,
                    log_record,
                    "success",
                    total_added,
                    total_updated,
                    total_skipped,
                )
                await session.commit()

        except Exception as exc:
            error_msg = str(exc)
            logger.error("daily_sync_failed", error=error_msg)
            # FR-017: Do not update last_updated on failure
            async with session_factory() as err_session:
                log_stmt = select(SyncLog).where(SyncLog.id == sync_log.id)
                err_result = await err_session.execute(log_stmt)
                err_log: SyncLog | None = err_result.scalar_one_or_none()
                if err_log:
                    await self._finish_sync_log(
                        err_session, err_log, "failure", error_message=error_msg
                    )
                await err_session.commit()
            raise

        await engine.dispose()
        return total_added, total_updated, total_skipped

    async def run_manual(self) -> tuple[int, int, int]:
        """Manual trigger — runs the same logic as run_daily with sync_type='manual'."""
        engine = self._make_engine()
        session_factory = async_sessionmaker(engine, expire_on_commit=False)

        async with session_factory() as session:
            await self._create_sync_log(session, "manual")
            await session.commit()

        await engine.dispose()

        # Reuse daily logic
        result = await self.run_daily()
        return result


# ─── CLI entry point (FR-018, FR-020) ────────────────────────────────────────


def _cli_main() -> None:
    """Command-line entry point for manual sync trigger.

    Usage:
        python -m app.services.sync --backfill
        python -m app.services.sync --manual
    """
    # Configure logging for CLI use
    from app.middleware import configure_logging

    configure_logging("INFO")

    parser = argparse.ArgumentParser(
        description="EEX French PGO Auctions sync utility",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m app.services.sync --backfill   # Download all historical ZIP archives
  python -m app.services.sync --manual     # Incremental sync of latest data
        """,
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--backfill",
        action="store_true",
        help="Download and parse all historical EEX ZIP archives (one-time operation)",
    )
    group.add_argument(
        "--manual",
        action="store_true",
        help="Incremental sync: fetch latest results and calendar from EEX",
    )
    args = parser.parse_args()

    service = SyncService()

    try:
        if args.backfill:
            print("Starting full historical backfill…")
            added, updated, skipped = asyncio.run(service.run_backfill())
        else:
            print("Starting manual incremental sync…")
            added, updated, skipped = asyncio.run(service.run_manual())

        print(
            f"Sync complete — added: {added}, updated: {updated}, skipped: {skipped}"
        )
        sys.exit(0)
    except Exception as exc:
        print(f"Sync failed: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    _cli_main()
