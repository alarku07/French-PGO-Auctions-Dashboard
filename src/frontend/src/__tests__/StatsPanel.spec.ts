/**
 * T048 — Smoke tests for StatsPanel component.
 * Verifies loading state, null data fallback, and data rendering.
 */
import { describe, it, expect } from "vitest";
import { mount } from "@vue/test-utils";
import StatsPanel from "@/components/StatsPanel.vue";
import type { StatsResponse } from "@/services/api";

const mockStats: StatsResponse = {
  total_auctions_held: 42,
  total_volume_awarded_mwh: 1_500_000,
  overall_weighted_avg_price_eur: 0.3125,
  last_updated: "2026-02-20T10:00:00Z",
};

describe("StatsPanel", () => {
  it("renders loading dashes when isLoading is true", () => {
    const wrapper = mount(StatsPanel, {
      props: { stats: null, isLoading: true },
    });
    const dashes = wrapper.findAll(".text-muted");
    expect(dashes.length).toBeGreaterThan(0);
    expect(dashes[0].text()).toBe("—");
  });

  it("renders N/A when stats is null and not loading", () => {
    const wrapper = mount(StatsPanel, {
      props: { stats: null, isLoading: false },
    });
    // total_auctions_held renders 0 (not N/A), but volume and price show N/A
    const naItems = wrapper.findAll(".text-muted");
    expect(naItems.some((el) => el.text() === "N/A")).toBe(true);
  });

  it("renders total auctions held", () => {
    const wrapper = mount(StatsPanel, {
      props: { stats: mockStats, isLoading: false },
    });
    expect(wrapper.text()).toContain("42");
  });

  it("renders volume with M suffix for millions", () => {
    const wrapper = mount(StatsPanel, {
      props: { stats: mockStats, isLoading: false },
    });
    expect(wrapper.text()).toContain("1.5M");
  });

  it("renders price value", () => {
    const wrapper = mount(StatsPanel, {
      props: { stats: mockStats, isLoading: false },
    });
    expect(wrapper.text()).toContain("0.3125");
  });

  it("has accessible region roles on stat cards", () => {
    const wrapper = mount(StatsPanel, {
      props: { stats: mockStats, isLoading: false },
    });
    const regions = wrapper.findAll("[role='region']");
    expect(regions.length).toBe(3);
  });
});
