/**
 * T006/T007 — Unit tests for AuctionEventList component (US1).
 * Verifies rendering of events, status badges, sorting, and empty state.
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

  it("shows 'Cancelled' badge for a cancelled event", () => {
    const wrapper = mount(AuctionEventList, {
      props: { events: [cancelledEvent], isLoading: false },
    });
    const badge = wrapper.find(".event-item__status-badge");
    expect(badge.text()).toBe("Cancelled");
    expect(badge.classes()).toContain("event-item__status-badge--cancelled");
  });

  it("renders multiple events with different statuses", () => {
    const wrapper = mount(AuctionEventList, {
      props: { events: [upcomingEvent, completedEvent, cancelledEvent], isLoading: false },
    });
    expect(wrapper.findAll(".event-item").length).toBe(3);
  });

  it("has accessible aria-label on container", () => {
    const wrapper = mount(AuctionEventList, {
      props: { events: [], isLoading: false },
    });
    expect(wrapper.attributes("aria-label")).toBe("Auction events");
  });

  it("orders events by event_date ascending", () => {
    const wrapper = mount(AuctionEventList, {
      props: { events: [upcomingEvent, completedEvent], isLoading: false },
    });
    const titles = wrapper.findAll(".event-item__title").map((el) => el.text());
    // completedEvent has pastDate (earlier), upcomingEvent has futureDate (later)
    expect(titles[0]).toContain(completedEvent.event_date.slice(0, 4));
    expect(titles[1]).toContain("March 2026");
  });
});
