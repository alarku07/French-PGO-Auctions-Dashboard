/**
 * T006/T007 — Unit tests for AuctionEventList component (US1).
 * T019 — Status badge tests and cancelled-toggle tests (US3).
 * Verifies rendering of events, nested auctions, status badges, and empty state.
 */
import { describe, it, expect } from "vitest";
import { mount } from "@vue/test-utils";
import AuctionEventList from "@/components/AuctionEventList.vue";
import type { AuctionEventRecord } from "@/services/api";

// ─── Fixtures ────────────────────────────────────────────────────────────────

const today = new Date();
const futureDate = new Date(today);
futureDate.setDate(today.getDate() + 30);
const pastDate = new Date(today);
pastDate.setDate(today.getDate() - 30);

function isoDate(d: Date): string {
  return d.toISOString().split("T")[0];
}

const upcomingEvent: AuctionEventRecord = {
  id: 1,
  event_date: isoDate(futureDate),
  status: "upcoming",
  is_cancelled: false,
  auctioning_month: "March 2026",
  production_month: "March 2026",
  order_book_open: null,
  cash_trading_limits_modification: null,
  order_book_close: null,
  order_matching: null,
  auctions: [
    {
      id: 10,
      auction_date: isoDate(futureDate),
      region: "Grand Est",
      production_period: "2026-03",
      technology: "Wind",
      status: "upcoming",
    },
    {
      id: 11,
      auction_date: isoDate(futureDate),
      region: "Bretagne",
      production_period: "2026-03",
      technology: "Solar",
      status: "upcoming",
    },
  ],
};

const completedEvent: AuctionEventRecord = {
  id: 2,
  event_date: isoDate(pastDate),
  status: "completed",
  is_cancelled: false,
  auctioning_month: null,
  production_month: null,
  order_book_open: null,
  cash_trading_limits_modification: null,
  order_book_close: null,
  order_matching: null,
  auctions: [],
};

const cancelledEvent: AuctionEventRecord = {
  id: 3,
  event_date: isoDate(futureDate),
  status: "upcoming",
  is_cancelled: true,
  auctioning_month: null,
  production_month: null,
  order_book_open: null,
  cash_trading_limits_modification: null,
  order_book_close: null,
  order_matching: null,
  auctions: [],
};

// ─── Tests ───────────────────────────────────────────────────────────────────

describe("AuctionEventList", () => {
  it("shows loading spinner when isLoading is true", () => {
    const wrapper = mount(AuctionEventList, {
      props: { events: [], isLoading: true },
    });
    expect(wrapper.find(".loading-spinner").exists()).toBe(true);
  });

  it("shows empty state when no events and not loading", () => {
    const wrapper = mount(AuctionEventList, {
      props: { events: [], isLoading: false },
    });
    expect(wrapper.find(".empty-state").exists()).toBe(true);
    expect(wrapper.text()).toContain("No auction events found");
  });

  it("renders the event list when events are provided", () => {
    const wrapper = mount(AuctionEventList, {
      props: { events: [upcomingEvent], isLoading: false },
    });
    expect(wrapper.find(".event-list").exists()).toBe(true);
    expect(wrapper.findAll(".event-item").length).toBe(1);
  });

  it("displays the event title (auctioning_month or date)", () => {
    const wrapper = mount(AuctionEventList, {
      props: { events: [upcomingEvent], isLoading: false },
    });
    expect(wrapper.find(".event-item__title").exists()).toBe(true);
    expect(wrapper.find(".event-item__title").text()).toContain("March 2026");
  });

  it("shows 'Upcoming' badge for a future event", () => {
    const wrapper = mount(AuctionEventList, {
      props: { events: [upcomingEvent], isLoading: false },
    });
    const badge = wrapper.find(".event-item__status-badge");
    expect(badge.exists()).toBe(true);
    expect(badge.text()).toBe("Upcoming");
    expect(badge.classes()).toContain("event-item__status-badge--upcoming");
  });

  it("shows 'Completed' badge for a past event", () => {
    const wrapper = mount(AuctionEventList, {
      props: { events: [completedEvent], isLoading: false },
    });
    const badge = wrapper.find(".event-item__status-badge");
    expect(badge.text()).toBe("Completed");
    expect(badge.classes()).toContain("event-item__status-badge--completed");
  });

  it("shows 'Cancelled' badge for a cancelled event when showCancelled is on", async () => {
    const wrapper = mount(AuctionEventList, {
      props: { events: [cancelledEvent], isLoading: false },
    });
    const toggle = wrapper.find('input[type="checkbox"]');
    await toggle.setValue(true);
    await toggle.trigger("change");

    const badge = wrapper.find(".event-item__status-badge");
    expect(badge.text()).toBe("Cancelled");
    expect(badge.classes()).toContain("event-item__status-badge--cancelled");
  });

  it("renders nested auction rows", () => {
    const wrapper = mount(AuctionEventList, {
      props: { events: [upcomingEvent], isLoading: false },
    });
    expect(wrapper.findAll(".auction-row").length).toBe(2);
    expect(wrapper.text()).toContain("Grand Est");
    expect(wrapper.text()).toContain("Bretagne");
  });

  it("shows 'no auctions' message when event has no auctions", () => {
    const wrapper = mount(AuctionEventList, {
      props: { events: [completedEvent], isLoading: false },
    });
    expect(wrapper.find(".event-item__no-auctions").exists()).toBe(true);
  });

  it("renders multiple events when showCancelled is on", async () => {
    const wrapper = mount(AuctionEventList, {
      props: {
        events: [upcomingEvent, completedEvent, cancelledEvent],
        isLoading: false,
      },
    });
    const toggle = wrapper.find('input[type="checkbox"]');
    await toggle.setValue(true);
    await toggle.trigger("change");

    expect(wrapper.findAll(".event-item").length).toBe(3);
  });

  it("has accessible aria-label on container", () => {
    const wrapper = mount(AuctionEventList, {
      props: { events: [], isLoading: false },
    });
    expect(wrapper.attributes("aria-label")).toBe("Auction events");
  });

  // ─── T019: Toggle-cancelled tests (US3) ──────────────────────────────────

  it("excludes cancelled events by default (showCancelled=false)", () => {
    const wrapper = mount(AuctionEventList, {
      props: {
        events: [upcomingEvent, cancelledEvent],
        isLoading: false,
      },
    });
    // Only the non-cancelled event should appear
    expect(wrapper.findAll(".event-item").length).toBe(1);
    const badges = wrapper.findAll(".event-item__status-badge");
    expect(badges.every((b) => b.text() !== "Cancelled")).toBe(true);
  });

  it("renders the 'Show cancelled' toggle checkbox", () => {
    const wrapper = mount(AuctionEventList, {
      props: { events: [], isLoading: false },
    });
    const toggle = wrapper.find('input[type="checkbox"]');
    expect(toggle.exists()).toBe(true);
    expect(toggle.attributes("aria-label")).toBe("Show cancelled events");
  });

  it("shows cancelled events after toggling 'Show cancelled' on", async () => {
    const wrapper = mount(AuctionEventList, {
      props: {
        events: [upcomingEvent, cancelledEvent],
        isLoading: false,
      },
    });

    const toggle = wrapper.find('input[type="checkbox"]');
    await toggle.setValue(true);
    await toggle.trigger("change");

    expect(wrapper.findAll(".event-item").length).toBe(2);
    const badges = wrapper.findAll(".event-item__status-badge");
    const texts = badges.map((b) => b.text());
    expect(texts).toContain("Cancelled");
  });

  it("emits 'toggle-cancelled' with true when toggled on", async () => {
    const wrapper = mount(AuctionEventList, {
      props: { events: [cancelledEvent], isLoading: false },
    });

    const toggle = wrapper.find('input[type="checkbox"]');
    await toggle.setValue(true);
    await toggle.trigger("change");

    expect(wrapper.emitted("toggle-cancelled")).toBeTruthy();
    expect(wrapper.emitted("toggle-cancelled")![0]).toEqual([true]);
  });

  it("emits 'toggle-cancelled' with false when toggled off", async () => {
    const wrapper = mount(AuctionEventList, {
      props: { events: [cancelledEvent], isLoading: false },
    });

    // Toggle on, then off
    const toggle = wrapper.find('input[type="checkbox"]');
    await toggle.setValue(true);
    await toggle.trigger("change");
    await toggle.setValue(false);
    await toggle.trigger("change");

    const emitted = wrapper.emitted("toggle-cancelled")!;
    expect(emitted[emitted.length - 1]).toEqual([false]);
  });
});
