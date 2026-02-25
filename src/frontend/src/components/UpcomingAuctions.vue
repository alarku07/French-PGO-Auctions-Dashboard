<template>
  <div class="upcoming-auctions" aria-label="Upcoming auctions">
    <div v-if="isLoading" class="loading-spinner" aria-live="polite" aria-busy="true">
      Loading…
    </div>

    <div v-else-if="auctions.length === 0" class="empty-state" style="padding: 32px 16px;">
      <p style="color: var(--color-text-secondary); font-style: italic;">
        No auctions currently scheduled.
      </p>
    </div>

    <ul v-else class="upcoming-list" role="list">
      <li
        v-for="auction in auctions"
        :key="auction.id"
        class="upcoming-item"
      >
        <span class="upcoming-item__date">{{ formatDate(auction.auction_date) }}</span>
        <div class="upcoming-item__region">{{ auction.region }}</div>
        <div v-if="auction.order_book_open" class="upcoming-item__details">
          OB: {{ formatDate(auction.order_book_open.split("T")[0]) }}
        </div>
      </li>
    </ul>
  </div>
</template>

<script setup lang="ts">
import type { UpcomingAuction } from "@/services/api";

interface Props {
  auctions: UpcomingAuction[];
  isLoading: boolean;
}

defineProps<Props>();

function formatDate(dateStr: string): string {
  return new Date(dateStr + "T00:00:00Z").toLocaleDateString("en-GB", {
    day: "2-digit",
    month: "short",
    year: "numeric",
    timeZone: "UTC",
  });
}
</script>
