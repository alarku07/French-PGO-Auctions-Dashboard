<template>
  <div class="last-updated" :title="absoluteTime ?? undefined" aria-label="Data freshness">
    <span class="last-updated__dot" :class="{ 'last-updated__dot--stale': isStale }" aria-hidden="true"></span>
    <span v-if="timestamp">{{ relativeTime }}</span>
    <span v-else>No data synced yet — run initial sync</span>
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";

interface Props {
  timestamp: string | null;
}

const props = defineProps<Props>();

const parsed = computed(() =>
  props.timestamp ? new Date(props.timestamp) : null,
);

const relativeTime = computed(() => {
  if (!parsed.value) return null;
  const diffMs = Date.now() - parsed.value.getTime();
  const diffH = Math.floor(diffMs / 3_600_000);
  const diffMin = Math.floor(diffMs / 60_000);
  if (diffMin < 1) return "Updated just now";
  if (diffMin < 60) return `Updated ${diffMin}m ago`;
  if (diffH < 24) return `Updated ${diffH}h ago`;
  const diffD = Math.floor(diffH / 24);
  return `Updated ${diffD}d ago`;
});

const absoluteTime = computed(() => {
  if (!parsed.value) return null;
  return parsed.value.toLocaleString("en-GB", {
    dateStyle: "medium",
    timeStyle: "short",
    timeZone: "UTC",
  }) + " UTC";
});

/** Flag as stale if last sync was > 25 hours ago (slightly over daily cadence). */
const isStale = computed(() => {
  if (!parsed.value) return true;
  return Date.now() - parsed.value.getTime() > 25 * 3_600_000;
});
</script>
