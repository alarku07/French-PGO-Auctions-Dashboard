<template>
  <div id="pgo-dashboard">
    <!-- Header -->
    <header class="site-header" role="banner">
      <div class="container">
        <div>
          <h1 class="site-header__title">French PGO Auctions Dashboard</h1>
          <p class="site-header__subtitle">
            Power Guarantees of Origin — Auction Results &amp; Calendar
          </p>
        </div>
        <LastUpdated :timestamp="stats?.last_updated ?? null" />
      </div>
    </header>

    <!-- Main content -->
    <main class="container" style="padding-top: 24px; padding-bottom: 48px;" role="main">
      <!-- Empty database state -->
      <div v-if="!isLoading && isEmpty" class="empty-state">
        <div class="empty-state__icon">📊</div>
        <h2 class="empty-state__title">No Data Available</h2>
        <p class="empty-state__body">
          The database is empty. Run the initial data sync to populate auction
          results from the EEX website.
        </p>
        <pre class="empty-state__code">cd src/backend
python -m app.services.sync --backfill</pre>
      </div>

      <template v-else>
        <!-- Stats Panel -->
        <StatsPanel :stats="stats" :is-loading="isLoading" />

        <!-- Shared Filters for Charts (US2) -->
        <div class="section-white" aria-label="Chart Filters">
          <div class="filter-bar">
            <RegionFilter
              :regions="regions"
              :model-value="chartFilters.region"
              @update:model-value="updateChartRegion"
            />
            <DateRangeFilter
              :start-date="chartFilters.startDate"
              :end-date="chartFilters.endDate"
              @change="updateChartDates"
              label-prefix="Chart"
            />
          </div>
        </div>

        <!-- Charts Section -->
        <div class="section-white">
          <h2 class="section-title">Price Trends</h2>
          <PriceChart
            :data="chartPrices"
            :is-loading="isChartLoading"
            :filters="chartFilters"
          />
        </div>

        <div class="section-white">
          <h2 class="section-title">Volume Trends</h2>
          <VolumeChart
            :data="chartVolumes"
            :is-loading="isChartLoading"
            :filters="chartFilters"
            @aggregation-change="updateChartAggregation"
          />
        </div>

        <!-- Auction Table & Upcoming Auctions -->
        <div class="section-white auctions-layout-grid">
          <!-- Past Auctions Table -->
          <div>
            <h2 class="section-title">Recent Auctions</h2>
            <AuctionTable
              :auctions="auctions"
              :pagination="auctionPagination"
              :is-loading="isLoading"
              @filter-change="updateAuctionFilter"
              @page-change="updateAuctionPage"
            />
          </div>

          <!-- Calendar -->
          <div>
            <h2 class="section-title">Calendar</h2>
            <AuctionEventList :events="auctionEvents" :is-loading="isLoading" />
          </div>
        </div>
      </template>

      <!-- Global error -->
      <div v-if="error" class="error-message" role="alert">
        {{ error }}
      </div>
    </main>

    <!-- Footer -->
    <footer
      style="background: var(--color-bg-header); color: rgba(255,255,255,0.6); text-align: center; padding: 16px; font-size: 12px;"
      role="contentinfo"
    >
      Data sourced from
      <a
        href="https://www.eex.com/en/markets/energy-certificates/french-auctions-power"
        target="_blank"
        rel="noopener noreferrer"
        style="color: var(--color-accent-light);"
      >EEX French Auctions Power</a>.
      Read-only dashboard — no personal data collected.
    </footer>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted } from "vue";
import { useAuctions } from "@/composables/useAuctions";
import { useChartData } from "@/composables/useChartData";
import AuctionEventList from "@/components/AuctionEventList.vue";
import AuctionTable from "@/components/AuctionTable.vue";
import DateRangeFilter from "@/components/DateRangeFilter.vue";
import LastUpdated from "@/components/LastUpdated.vue";
import PriceChart from "@/components/PriceChart.vue";
import RegionFilter from "@/components/RegionFilter.vue";
import StatsPanel from "@/components/StatsPanel.vue";
import VolumeChart from "@/components/VolumeChart.vue";

// US1: Dashboard data
const {
  auctions,
  auctionPagination,
  upcoming,
  auctionEvents,
  stats,
  regions,
  isLoading,
  error,
  fetchAll,
  updateAuctionFilter,
  updateAuctionPage,
} = useAuctions();

// US2: Chart data
const {
  chartPrices,
  chartVolumes,
  chartFilters,
  isChartLoading,
  updateRegion: updateChartRegion,
  updateDates: updateChartDates,
  updateAggregation: updateChartAggregation,
} = useChartData();

const isEmpty = computed(
  () =>
    !isLoading.value &&
    auctions.value.length === 0 &&
    upcoming.value.length === 0 &&
    stats.value?.total_auctions_held === 0,
);

onMounted(() => {
  fetchAll();
});
</script>
