<template>
  <div class="auction-event-list" aria-label="Auction events">
    <div v-if="isLoading" class="loading-spinner" aria-live="polite" aria-busy="true">
      Loading…
    </div>

    <div v-else-if="sortedEvents.length === 0" class="empty-state" style="padding: 32px 16px;">
      <p style="color: var(--color-text-secondary); font-style: italic;">
        No auction events found.
      </p>
    </div>

    <ul v-else class="event-list" role="list">
      <li
        v-for="event in sortedEvents"
        :key="event.id"
        class="event-item"
        :class="{ 'event-item--cancelled': event.is_cancelled }"
      >
        <!-- Clickable header row -->
        <div
          class="event-item__header"
          role="button"
          :tabindex="0"
          :aria-expanded="expandedIds.has(event.id)"
          @click="toggleExpanded(event.id)"
          @keydown.enter="toggleExpanded(event.id)"
          @keydown.space.prevent="toggleExpanded(event.id)"
        >
          <span class="event-item__title">
            {{ event.auctioning_month ?? formatDate(event.event_date) }}
          </span>
          <div class="event-item__header-right">
            <span
              class="event-item__status-badge"
              :class="statusBadgeClass(event)"
              aria-label="Event status"
            >
              {{ event.is_cancelled ? "Cancelled" : capitalize(event.status) }}
            </span>
            <span
              class="event-item__chevron"
              :class="{ 'event-item__chevron--open': expandedIds.has(event.id) }"
              aria-hidden="true"
            >▾</span>
          </div>
        </div>

        <!-- Expanded details -->
        <div v-show="expandedIds.has(event.id)" class="event-item__expanded">
          <dl class="event-item__details-list">
            <template v-if="event.production_month">
              <dt>Production month</dt>
              <dd>{{ event.production_month }}</dd>
            </template>
            <template v-if="event.order_book_open">
              <dt>Opening of Order Book</dt>
              <dd>{{ formatDatetime(event.order_book_open) }}</dd>
            </template>
            <template v-if="event.cash_trading_limits_modification">
              <dt>Modification of cash trading limits</dt>
              <dd>{{ formatDatetime(event.cash_trading_limits_modification) }}</dd>
            </template>
            <template v-if="event.order_book_close">
              <dt>Closure of Order Book</dt>
              <dd>{{ formatDatetime(event.order_book_close) }}</dd>
            </template>
            <template v-if="event.order_matching">
              <dt>Order Matching</dt>
              <dd>{{ formatDatetime(event.order_matching) }}</dd>
            </template>
          </dl>
        </div>
      </li>
    </ul>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from "vue";
import type { AuctionEventRecord } from "@/services/api";

interface Props {
  events: AuctionEventRecord[];
  isLoading: boolean;
}

const props = defineProps<Props>();

const expandedIds = ref(new Set<number>());

const sortedEvents = computed(() =>
  [...props.events].sort((a, b) => a.event_date.localeCompare(b.event_date)),
);

function toggleExpanded(id: number): void {
  const next = new Set(expandedIds.value);
  if (next.has(id)) {
    next.delete(id);
  } else {
    next.add(id);
  }
  expandedIds.value = next;
}

function formatDate(dateStr: string): string {
  return new Date(dateStr + "T00:00:00Z").toLocaleDateString("en-GB", {
    day: "2-digit",
    month: "short",
    year: "numeric",
    timeZone: "UTC",
  });
}

function formatDatetime(isoStr: string): string {
  const d = new Date(isoStr);
  return d.toLocaleString("en-GB", {
    day: "2-digit",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function capitalize(s: string): string {
  return s.charAt(0).toUpperCase() + s.slice(1);
}

function statusBadgeClass(event: AuctionEventRecord): string {
  if (event.is_cancelled) return "event-item__status-badge--cancelled";
  return event.status === "upcoming"
    ? "event-item__status-badge--upcoming"
    : "event-item__status-badge--completed";
}
</script>

<style scoped>
.auction-event-list {
  width: 100%;
}

.event-list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.event-item {
  border: 1px solid var(--color-border, #e0e0e0);
  border-radius: 6px;
  background: var(--color-surface, #fff);
  overflow: hidden;
}

.event-item--cancelled {
  opacity: 0.7;
  border-color: var(--color-danger, #d32f2f);
}

/* Clickable header row */
.event-item__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 16px;
  cursor: pointer;
  user-select: none;
  gap: 12px;
  transition: background 0.15s;
}

.event-item__header:hover {
  background: var(--color-table-row-hover, #f0f7f0);
}

.event-item__header:focus-visible {
  outline: 2px solid var(--color-accent, #1976d2);
  outline-offset: -2px;
}

.event-item__header-right {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-shrink: 0;
}

.event-item__title {
  font-weight: 600;
  font-size: 1rem;
}

.event-item__chevron {
  font-size: 1.1rem;
  color: var(--color-text-secondary, #757575);
  transition: transform 0.2s ease;
  display: inline-block;
  line-height: 1;
}

.event-item__chevron--open {
  transform: rotate(180deg);
}

/* Expanded section */
.event-item__expanded {
  border-top: 1px solid var(--color-border, #e0e0e0);
  padding: 16px;
}

.event-item__details-list {
  display: grid;
  grid-template-columns: auto 1fr;
  gap: 6px 16px;
  margin: 0;
  font-size: 0.875rem;
}

.event-item__details-list dt {
  color: var(--color-text-secondary, #757575);
  font-weight: 500;
}

.event-item__details-list dd {
  margin: 0;
}

.event-item__status-badge {
  display: inline-block;
  padding: 2px 10px;
  border-radius: 12px;
  font-size: 0.8rem;
  font-weight: 500;
}

.event-item__status-badge--upcoming {
  background: #e8f5e9;
  color: #2e7d32;
}

.event-item__status-badge--completed {
  background: #f5f5f5;
  color: #616161;
}

.event-item__status-badge--cancelled {
  background: #fdecea;
  color: #d32f2f;
}

</style>
