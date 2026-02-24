<template>
  <div class="price-chart">
    <div v-if="!isLoading && data.length === 0" style="text-align: center; padding: 48px; color: var(--color-text-muted);">
      No price data available for the selected filters.
    </div>
    <v-chart
      v-else
      class="chart-container"
      :option="chartOption"
      :loading="isLoading"
      :autoresize="true"
      aria-label="Clearing price over time chart"
    />
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";
import VChart from "vue-echarts";
import { use } from "echarts/core";
import { LineChart } from "echarts/charts";
import {
  GridComponent,
  TooltipComponent,
  DataZoomComponent,
  LegendComponent,
} from "echarts/components";
import { CanvasRenderer } from "echarts/renderers";
import type { PriceDataPoint } from "@/services/api";

use([LineChart, GridComponent, TooltipComponent, DataZoomComponent, LegendComponent, CanvasRenderer]);

interface Props {
  data: PriceDataPoint[];
  isLoading: boolean;
  filters: {
    region: string | null;
    technology: string | null;
  };
}

const props = defineProps<Props>();

const chartOption = computed(() => {
  // Group by region for multi-series chart
  const regionMap = new Map<string, { dates: string[]; prices: (number | null)[] }>();

  for (const point of props.data) {
    if (!regionMap.has(point.region)) {
      regionMap.set(point.region, { dates: [], prices: [] });
    }
    const series = regionMap.get(point.region)!;
    series.dates.push(point.auction_date);
    series.prices.push(point.weighted_avg_price_eur ?? null);
  }

  // Collect all unique dates for shared x-axis
  const allDates = [...new Set(props.data.map((d) => d.auction_date))].sort();

  const colours = [
    "#2196f3", "#e53935", "#ff9800", "#9c27b0",
    "#00bcd4", "#f06292", "#8bc34a", "#ff5722",
    "#607d8b", "#ffd600", "#00897b", "#7e57c2",
  ];

  const series = [...regionMap.entries()].map(([region, { prices }], i) => ({
    name: region,
    type: "line",
    data: allDates.map((date) => {
      const idx = regionMap.get(region)!.dates.indexOf(date);
      return idx >= 0 ? prices[idx] : null;
    }),
    smooth: true,
    symbol: "circle",
    symbolSize: 5,
    lineStyle: { width: 2, color: colours[i % colours.length] },
    itemStyle: { color: colours[i % colours.length] },
    connectNulls: false,
  }));

  return {
    backgroundColor: "transparent",
    tooltip: {
      trigger: "axis",
      axisPointer: { type: "cross" },
      formatter: (params: any[]) => {
        const date = params[0]?.axisValue ?? "";
        const lines = params
          .filter((p) => Number.isFinite(p.value))
          .map((p) => `${p.marker} ${p.seriesName}: <b>${(p.value as number).toFixed(4)} EUR/MWh</b>`)
          .join("<br/>");
        return `<div style="font-size:13px"><b>${date}</b><br/>${lines}</div>`;
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
      data: allDates,
      axisLabel: { rotate: 30, fontSize: 11 },
      boundaryGap: false,
    },
    yAxis: {
      type: "value",
      name: "EUR/MWh",
      nameLocation: "middle",
      nameGap: 50,
      axisLabel: {
        formatter: (v: number) => v.toFixed(2),
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
