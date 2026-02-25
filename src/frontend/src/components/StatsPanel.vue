<template>
  <div class="section-white stats-section" aria-label="Aggregate Statistics">
    <div class="stats-grid">
      <div class="stat-card" role="region" aria-label="Total Auctions Held">
        <div class="stat-card__label">Total Auctions Held</div>
        <div class="stat-card__value">
          <span v-if="isLoading" class="text-muted">—</span>
          <span v-else>{{ formatNumber(stats?.total_auctions_held ?? 0) }}</span>
        </div>
      </div>

      <div class="stat-card" role="region" aria-label="Total Volume Awarded">
        <div class="stat-card__label">Total Volume Awarded</div>
        <div class="stat-card__value">
          <span v-if="isLoading" class="text-muted">—</span>
          <span v-else-if="stats?.total_volume_awarded_mwh != null">
            {{ formatVolume(stats.total_volume_awarded_mwh) }}
            <span class="stat-card__unit">MWh</span>
          </span>
          <span v-else class="text-muted">N/A</span>
        </div>
      </div>

      <div class="stat-card" role="region" aria-label="Overall Average Price">
        <div class="stat-card__label">Overall Avg. Clearing Price</div>
        <div class="stat-card__value">
          <span v-if="isLoading" class="text-muted">—</span>
          <span v-else-if="stats?.overall_weighted_avg_price_eur != null">
            {{ formatPrice(stats.overall_weighted_avg_price_eur) }}
            <span class="stat-card__unit">EUR/MWh</span>
          </span>
          <span v-else class="text-muted">N/A</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { StatsResponse } from "@/services/api";

interface Props {
  stats: StatsResponse | null;
  isLoading: boolean;
}

defineProps<Props>();

function formatNumber(value: number): string {
  return new Intl.NumberFormat("en-GB").format(value);
}

function formatVolume(value: number): string {
  if (value >= 1_000_000) {
    return new Intl.NumberFormat("en-GB", { maximumFractionDigits: 1 }).format(value / 1_000_000) + "M";
  }
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
.stats-section {
  margin-bottom: 24px;
}
.text-muted {
  color: var(--color-text-muted);
  font-size: var(--font-size-xl);
}
</style>
