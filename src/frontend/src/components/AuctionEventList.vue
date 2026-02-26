<template>
  <div class="auction-event-list" aria-label="Auction events">
    <div class="auction-event-list__toolbar">
      <label class="toggle-cancelled">
        <input
          type="checkbox"
          :checked="showCancelled"
          @change="toggleCancelled"
          aria-label="Show cancelled events"
        />
        Show cancelled
      </label>
    </div>

    <div v-if="isLoading" class="loading-spinner" aria-live="polite" aria-busy="true">
      Loading…
    </div>

    <div v-else-if="visibleEvents.length === 0" class="empty-state" style="padding: 32px 16px;">
      <p style="color: var(--color-text-secondary); font-style: italic;">
        No auction events found.
      </p>
    </div>

    <ul v-else class="event-list" role="list">
      <li
        v-for="event in visibleEvents"
        :key="event.id"
        class="event-item"
        :class="{ 'event-item--cancelled': event.is_cancelled }"
      >
        <div class="event-item__header">
          <span class="event-item__title">
            {{ event.auctioning_month ?? formatDate(event.event_date) }}
          </span>
          <span
            class="event-item__status-badge"
            :class="statusBadgeClass(event)"
            aria-label="Event status"
          >
            {{ event.is_cancelled ? "Cancelled" : capitalize(event.status) }}
          </span>
        </div>

        <p class="event-item__subtitle">
          Closure: {{ formatDate(event.event_date) }}
        </p>

        <details class="event-item__details">
          <summary class="event-item__details-summary">Calendar details</summary>
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
        </details>

        <table
          v-if="event.auctions.length > 0"
          class="event-item__auctions"
          aria-label="Auctions in this event"
        >
          <thead>
            <tr>
              <th scope="col">Region</th>
              <th scope="col">Production Period</th>
              <th scope="col">Technology</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="auction in event.auctions"
              :key="auction.id"
              class="auction-row"
            >
              <td>{{ auction.region }}</td>
              <td>{{ auction.production_period }}</td>
              <td>{{ auction.technology ?? "—" }}</td>
            </tr>
          </tbody>
        </table>

        <p v-else class="event-item__no-auctions">
          No individual auctions scheduled yet.
        </p>
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

const emit = defineEmits<{
  "toggle-cancelled": [showCancelled: boolean];
}>();

const showCancelled = ref(false);

const visibleEvents = computed(() =>
  showCancelled.value
    ? props.events
    : props.events.filter((e) => !e.is_cancelled),
);

function toggleCancelled(event: Event): void {
  showCancelled.value = (event.target as HTMLInputElement).checked;
  emit("toggle-cancelled", showCancelled.value);
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

.auction-event-list__toolbar {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
  flex-wrap: wrap;
}

.toggle-cancelled {
  display: flex;
  align-items: center;
  gap: 6px;
  cursor: pointer;
  font-size: 0.875rem;
  color: var(--color-text-secondary, #757575);
  user-select: none;
}

.toggle-cancelled input[type="checkbox"] {
  cursor: pointer;
}

.event-list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.event-item {
  border: 1px solid var(--color-border, #e0e0e0);
  border-radius: 6px;
  padding: 16px;
  background: var(--color-surface, #fff);
}

.event-item--cancelled {
  opacity: 0.7;
  border-color: var(--color-danger, #d32f2f);
}

.event-item__header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
  flex-wrap: wrap;
}

.event-item__title {
  font-weight: 600;
  font-size: 1rem;
}

.event-item__subtitle {
  font-size: 0.8rem;
  color: var(--color-text-secondary, #757575);
  margin: 0 0 8px;
}

.event-item__details {
  margin-bottom: 12px;
}

.event-item__details-summary {
  cursor: pointer;
  font-size: 0.8rem;
  color: var(--color-text-secondary, #757575);
  user-select: none;
}

.event-item__details-list {
  display: grid;
  grid-template-columns: auto 1fr;
  gap: 4px 12px;
  margin: 8px 0 0;
  font-size: 0.8rem;
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

.event-item__auctions {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.875rem;
}

.event-item__auctions th,
.event-item__auctions td {
  text-align: left;
  padding: 6px 8px;
  border-bottom: 1px solid var(--color-border, #e0e0e0);
}

.event-item__auctions th {
  color: var(--color-text-secondary, #757575);
  font-weight: 500;
}

.event-item__no-auctions {
  font-size: 0.875rem;
  color: var(--color-text-secondary, #757575);
  font-style: italic;
  margin: 0;
}

/* ─── Responsive (mobile-first) ─────────────────────────────────────────── */
@media (max-width: 480px) {
  .event-item__auctions thead {
    display: none;
  }

  .event-item__auctions tbody,
  .event-item__auctions tr,
  .event-item__auctions td {
    display: block;
    width: 100%;
  }

  .event-item__auctions td::before {
    content: attr(data-label) ": ";
    font-weight: 500;
    color: var(--color-text-secondary, #757575);
  }
}
</style>
