/**
 * T050 — Smoke tests for UpcomingAuctions component.
 * Verifies empty state and list rendering.
 */
import { describe, it, expect } from "vitest";
import { mount } from "@vue/test-utils";
import UpcomingAuctions from "@/components/UpcomingAuctions.vue";
import type { UpcomingAuction } from "@/services/api";

const mockAuctions: UpcomingAuction[] = [
  {
    id: 1,
    auction_date: "2026-03-18",
    region: "Bretagne",
    production_period: "2025-12",
    order_book_open: "2026-03-16T08:00:00Z",
    order_book_close: "2026-03-17T18:00:00Z",
    order_matching: "2026-03-18T10:00:00Z",
  },
];

describe("UpcomingAuctions", () => {
  it("shows loading spinner when isLoading is true", () => {
    const wrapper = mount(UpcomingAuctions, {
      props: { auctions: [], isLoading: true },
    });
    expect(wrapper.find(".loading-spinner").exists()).toBe(true);
  });

  it("shows empty state message when no auctions and not loading", () => {
    const wrapper = mount(UpcomingAuctions, {
      props: { auctions: [], isLoading: false },
    });
    expect(wrapper.find(".empty-state").exists()).toBe(true);
    expect(wrapper.text()).toContain("No auctions currently scheduled");
  });

  it("renders auction list when auctions are provided", () => {
    const wrapper = mount(UpcomingAuctions, {
      props: { auctions: mockAuctions, isLoading: false },
    });
    expect(wrapper.find(".upcoming-list").exists()).toBe(true);
    expect(wrapper.findAll(".upcoming-item").length).toBe(1);
  });

  it("displays the auction region", () => {
    const wrapper = mount(UpcomingAuctions, {
      props: { auctions: mockAuctions, isLoading: false },
    });
    expect(wrapper.text()).toContain("Bretagne");
  });

  it("displays OB date when order_book_open is set", () => {
    const wrapper = mount(UpcomingAuctions, {
      props: { auctions: mockAuctions, isLoading: false },
    });
    expect(wrapper.find(".upcoming-item__details").exists()).toBe(true);
    expect(wrapper.text()).toContain("OB:");
  });

  it("has accessible aria-label", () => {
    const wrapper = mount(UpcomingAuctions, {
      props: { auctions: [], isLoading: false },
    });
    expect(wrapper.attributes("aria-label")).toBe("Upcoming auctions");
  });
});
