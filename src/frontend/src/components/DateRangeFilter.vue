<template>
  <div class="date-range-filter" role="group" :aria-label="`${labelPrefix} date range filter`">
    <div class="filter-group">
      <label :for="`${uid}-start`" class="form-label">From</label>
      <input
        :id="`${uid}-start`"
        v-model="localStart"
        type="date"
        class="form-control"
        :aria-label="`${labelPrefix} start date`"
        @change="emitChange"
      />
    </div>
    <div class="filter-group">
      <label :for="`${uid}-end`" class="form-label">To</label>
      <input
        :id="`${uid}-end`"
        v-model="localEnd"
        type="date"
        class="form-control"
        :aria-label="`${labelPrefix} end date`"
        @change="emitChange"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from "vue";

interface Props {
  startDate?: string | null;
  endDate?: string | null;
  labelPrefix?: string;
}

interface ChangeEvent {
  start_date: string | undefined;
  end_date: string | undefined;
}

const props = withDefaults(defineProps<Props>(), {
  startDate: null,
  endDate: null,
  labelPrefix: "Date",
});

const emit = defineEmits<{
  change: [ChangeEvent];
}>();

// Stable UID for label/input association
const uid = `date-range-${Math.random().toString(36).slice(2, 9)}`;

const localStart = ref(props.startDate ?? "");
const localEnd = ref(props.endDate ?? "");

watch(() => props.startDate, (v) => { localStart.value = v ?? ""; });
watch(() => props.endDate, (v) => { localEnd.value = v ?? ""; });

function emitChange() {
  emit("change", {
    start_date: localStart.value || undefined,
    end_date: localEnd.value || undefined,
  });
}
</script>
