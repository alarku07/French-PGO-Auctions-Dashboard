<template>
  <div class="volume-chart">
    <!-- Aggregation toggle -->
    <div class="chart-controls" role="group" aria-label="Volume aggregation view">
      <button
        v-for="option in aggregationOptions"
        :key="option.value"
        class="btn"
        :class="{ 'btn--active': activeAggregation === option.value }"
        :aria-pressed="activeAggregation === option.value"
        @click="setAggregation(option.value)"
      >
        {{ option.label }}
      </button>
    </div>

    <div v-if="!isLoading && data.length === 0" style="text-align: center; padding: 48px; color: var(--color-text-muted);">
      No volume data available for the selected filters.
    </div>
    <v-chart
      v-else
      class="chart-container"
      :option="chartOption"
      :loading="isLoading"
      :autoresize="true"
      aria-label="Volume awarded over time chart"
    />
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from "vue";
import VChart from "vue-echarts";
import { use } from "echarts/core";
import { BarChart, ScatterChart } from "echarts/charts";
import {
  GridComponent,
  TooltipComponent,
  DataZoomComponent,
  LegendComponent,
} from "echarts/components";
import { CanvasRenderer } from "echarts/renderers";
import type { VolumeDataPoint } from "@/services/api";

use([BarChart, ScatterChart, GridComponent, TooltipComponent, DataZoomComponent, LegendComponent, CanvasRenderer]);

interface Props {
  data: VolumeDataPoint[];
  isLoading: boolean;
  filters: {
    region: string | null;
    technology: string | null;
    aggregation?: string;
  };
}

const props = defineProps<Props>();

type Aggregation = "per_auction" | "monthly" | "yearly";

const emit = defineEmits<{
  "aggregation-change": [Aggregation];
}>();

const aggregationOptions: { value: Aggregation; label: string }[] = [
  { value: "per_auction", label: "Per Auction" },
  { value: "monthly", label: "Monthly" },
  { value: "yearly", label: "Yearly" },
];

const activeAggregation = ref<Aggregation>(
  (props.filters.aggregation as Aggregation) ?? "monthly",
);

function setAggregation(value: Aggregation) {
  activeAggregation.value = value;
  emit("aggregation-change", value);
}

const colours = [
  "#2196f3", "#e53935", "#ff9800", "#9c27b0",
  "#00bcd4", "#f06292", "#8bc34a", "#ff5722",
  "#607d8b", "#ffd600", "#00897b", "#7e57c2",
];

const chartOption = computed(() => {
  const regionMap = new Map<string, { periods: string[]; allocated: (number | null)[] }>();

  for (const point of props.data) {
    if (!regionMap.has(point.region)) {
      regionMap.set(point.region, { periods: [], allocated: [] });
    }
    const s = regionMap.get(point.region)!;
    s.periods.push(point.period);
    s.allocated.push(point.volume_allocated_mwh ?? null);
  }

  const allPeriods = [...new Set(props.data.map((d) => d.period))].sort();

  const isPerAuction = activeAggregation.value === "per_auction";

  const series = [...regionMap.entries()].map(([region, { allocated }], i) => ({
    name: region,
    type: isPerAuction ? "scatter" : "bar",
    data: allPeriods.map((period) => {
      const idx = regionMap.get(region)!.periods.indexOf(period);
      return idx >= 0 ? allocated[idx] : null;
    }),
    itemStyle: { color: colours[i % colours.length] },
    symbolSize: isPerAuction ? 8 : undefined,
    stack: isPerAuction ? undefined : "total",
  }));

  return {
    backgroundColor: "transparent",
    tooltip: {
      trigger: "axis",
      axisPointer: { type: "cross" },
      formatter: (params: any[]) => {
        const period = params[0]?.axisValue ?? "";
        const lines = params
          .filter((p) => p.value !== null)
          .map((p) => {
            const val = Number(p.value ?? 0);
            const formatted = val >= 1_000_000
              ? (val / 1_000_000).toFixed(2) + "M"
              : val.toLocaleString("en-GB");
            return `${p.marker} ${p.seriesName}: <b>${formatted} MWh</b>`;
          })
          .join("<br/>");
        return `<div style="font-size:13px"><b>${period}</b><br/>${lines}</div>`;
      },
    },
    legend: {
      type: "scroll",
      bottom: 0,
      textStyle: { fontSize: 11 },
    },
    grid: {
      left: "3%",
      right: "3%",
      bottom: 60,
      top: 16,
      containLabel: true,
    },
    dataZoom: [
      { type: "inside", start: 0, end: 100 },
      { type: "slider", bottom: 30, height: 20 },
    ],
    xAxis: {
      type: "category",
      data: allPeriods,
      axisLabel: { rotate: 30, fontSize: 11 },
    },
    yAxis: {
      type: "value",
      name: "MWh",
      nameLocation: "middle",
      nameGap: 60,
      axisLabel: {
        formatter: (v: number) =>
          v >= 1_000_000 ? (v / 1_000_000).toFixed(1) + "M" : v.toLocaleString("en-GB"),
        fontSize: 11,
      },
    },
    series,
  };
});
</script>

<style scoped>
.chart-container {
  width: 100%;
  height: 400px;
}
</style>
