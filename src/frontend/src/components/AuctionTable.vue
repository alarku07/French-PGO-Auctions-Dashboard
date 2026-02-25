<template>
  <div class="auction-table-wrapper">
    <!-- Date range filter -->
    <DateRangeFilter
      :start-date="localStartDate"
      :end-date="localEndDate"
      label-prefix="Auction"
      @change="onDateChange"
    />

    <!-- Loading -->
    <div v-if="isLoading" class="loading-spinner" aria-live="polite" aria-busy="true">Loading…</div>

    <!-- Empty state -->
    <div v-else-if="auctions.length === 0" class="empty-state" style="padding: 32px 16px;">
      <p style="color: var(--color-text-secondary); font-style: italic;">
        No auction results for the selected period.
      </p>
    </div>

    <!-- Table -->
    <div v-else>
      <div class="table-wrapper">
        <table class="data-table data-table--responsive" aria-label="Past auction results">
          <thead>
            <tr>
              <th scope="col">Auction Date</th>
              <th scope="col">Region</th>
              <th scope="col" class="text-right">Vol. Offered (MWh)</th>
              <th scope="col" class="text-right">Vol. Awarded (MWh)</th>
              <th scope="col" class="text-right">Avg. Price (EUR/MWh)</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="a in auctions" :key="a.id">
              <td data-label="Auction Date">{{ formatDate(a.auction_date) }}</td>
              <td data-label="Region">{{ a.region }}</td>
              <td data-label="Vol. Offered (MWh)" class="text-right">
                {{ formatNumber(a.volume_offered_mwh) }}
              </td>
              <td data-label="Vol. Awarded (MWh)" class="text-right">
                {{ formatNumber(a.volume_allocated_mwh) }}
              </td>
              <td data-label="Avg. Price (EUR/MWh)" class="text-right">
                <span v-if="a.weighted_avg_price_eur != null">
                  {{ formatPrice(a.weighted_avg_price_eur) }}
                </span>
                <span v-else class="text-muted">Not yet published</span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Pagination -->
      <div
        v-if="pagination && pagination.total_pages > 1"
        class="pagination"
        role="navigation"
        aria-label="Table pagination"
        style="display: flex; gap: 8px; align-items: center; margin-top: 12px; flex-wrap: wrap;"
      >
        <button
          class="btn"
          :disabled="pagination.page <= 1"
          aria-label="Previous page"
          @click="emit('page-change', pagination.page - 1)"
        >
          ‹ Prev
        </button>
        <span style="font-size: 13px; color: var(--color-text-secondary);">
          Page {{ pagination.page }} of {{ pagination.total_pages }}
          ({{ pagination.total_items }} results)
        </span>
        <button
          class="btn"
          :disabled="pagination.page >= pagination.total_pages"
          aria-label="Next page"
          @click="emit('page-change', pagination.page + 1)"
        >
          Next ›
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from "vue";
import type { AuctionRecord, Pagination } from "@/services/api";
import DateRangeFilter from "@/components/DateRangeFilter.vue";

interface Props {
  auctions: AuctionRecord[];
  pagination: Pagination | null;
  isLoading: boolean;
}

interface FilterChange {
  start_date?: string;
  end_date?: string;
}

defineProps<Props>();

const emit = defineEmits<{
  "filter-change": [FilterChange];
  "page-change": [number];
}>();

// Default: previous calendar month
const today = new Date();
const firstOfThisMonth = new Date(today.getFullYear(), today.getMonth(), 1);
const lastOfPrev = new Date(firstOfThisMonth.getTime() - 86_400_000);
const firstOfPrev = new Date(lastOfPrev.getFullYear(), lastOfPrev.getMonth(), 1);

const localStartDate = ref(firstOfPrev.toISOString().slice(0, 10));
const localEndDate = ref(lastOfPrev.toISOString().slice(0, 10));

function onDateChange(event: FilterChange) {
  localStartDate.value = event.start_date ?? "";
  localEndDate.value = event.end_date ?? "";
  emit("filter-change", event);
}

function formatDate(dateStr: string): string {
  return new Date(dateStr + "T00:00:00Z").toLocaleDateString("en-GB", {
    day: "2-digit",
    month: "short",
    year: "numeric",
    timeZone: "UTC",
  });
}

function formatNumber(value: number | null): string {
  if (value == null) return "—";
  return new Intl.NumberFormat("en-GB", { maximumFractionDigits: 0 }).format(value);
}

function formatPrice(value: number): string {
  return new Intl.NumberFormat("en-GB", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 4,
  }).format(value);
}
</script>

<style scoped>
.text-muted {
  color: var(--color-text-muted);
  font-style: italic;
}

.auction-table-wrapper :deep(.date-range-filter) {
  margin-bottom: var(--space-4);
}
</style>
