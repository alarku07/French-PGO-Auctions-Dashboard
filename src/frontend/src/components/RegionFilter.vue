<template>
  <div class="filter-group">
    <label :for="uid" class="form-label">Region</label>
    <select
      :id="uid"
      class="form-control"
      :value="modelValue ?? ''"
      aria-label="Filter by region"
      @change="onChange"
    >
      <option value="">All Regions</option>
      <option v-for="region in regions" :key="region" :value="region">
        {{ region }}
      </option>
    </select>
  </div>
</template>

<script setup lang="ts">
interface Props {
  regions: string[];
  modelValue: string | null;
}

defineProps<Props>();

const emit = defineEmits<{
  "update:modelValue": [string | null];
}>();

const uid = `region-filter-${Math.random().toString(36).slice(2, 9)}`;

function onChange(event: Event) {
  const target = event.target as HTMLSelectElement;
  emit("update:modelValue", target.value || null);
}
</script>
