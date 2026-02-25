import { ref, type Ref } from "vue";
import {
  getChartPrices,
  getChartVolumes,
  type PriceDataPoint,
  type VolumeDataPoint,
} from "@/services/api";

interface ChartFilters {
  region: string | null;
  startDate: string | null;
  endDate: string | null;
  aggregation: "per_auction" | "monthly" | "yearly";
  technology: string | null;
}

interface ChartDataState {
  chartPrices: Ref<PriceDataPoint[]>;
  chartVolumes: Ref<VolumeDataPoint[]>;
  chartFilters: Ref<ChartFilters>;
  isChartLoading: Ref<boolean>;
  updateRegion: (region: string | null) => void;
  updateDates: (event: { start_date?: string; end_date?: string }) => void;
  updateAggregation: (agg: "per_auction" | "monthly" | "yearly") => void;
  updateTechnology: (tech: string | null) => void;
}

export function useChartData(): ChartDataState {
  const chartPrices = ref<PriceDataPoint[]>([]);
  const chartVolumes = ref<VolumeDataPoint[]>([]);
  const isChartLoading = ref(false);

  const chartFilters = ref<ChartFilters>({
    region: null,
    startDate: null,
    endDate: null,
    aggregation: "monthly",
    technology: null,
  });

  // Debounce timer
  let debounceTimer: ReturnType<typeof setTimeout> | null = null;

  async function fetchCharts() {
    isChartLoading.value = true;
    try {
      const filters = chartFilters.value;
      const params = {
        region: filters.region ?? undefined,
        start_date: filters.startDate ?? undefined,
        end_date: filters.endDate ?? undefined,
        technology: filters.technology ?? undefined,
      };

      const [priceResponse, volumeResponse] = await Promise.allSettled([
        getChartPrices(params),
        getChartVolumes({ ...params, aggregation: filters.aggregation }),
      ]);

      if (priceResponse.status === "fulfilled") {
        chartPrices.value = priceResponse.value.data;
      }
      if (volumeResponse.status === "fulfilled") {
        chartVolumes.value = volumeResponse.value.data;
      }
    } finally {
      isChartLoading.value = false;
    }
  }

  function debouncedFetch() {
    if (debounceTimer) clearTimeout(debounceTimer);
    debounceTimer = setTimeout(fetchCharts, 300);
  }

  function updateRegion(region: string | null) {
    chartFilters.value = { ...chartFilters.value, region };
    debouncedFetch();
  }

  function updateDates(event: { start_date?: string; end_date?: string }) {
    chartFilters.value = {
      ...chartFilters.value,
      startDate: event.start_date ?? null,
      endDate: event.end_date ?? null,
    };
    debouncedFetch();
  }

  function updateAggregation(agg: "per_auction" | "monthly" | "yearly") {
    chartFilters.value = { ...chartFilters.value, aggregation: agg };
    fetchCharts();
  }

  function updateTechnology(tech: string | null) {
    chartFilters.value = { ...chartFilters.value, technology: tech };
    debouncedFetch();
  }

  // Initial load
  fetchCharts();

  return {
    chartPrices,
    chartVolumes,
    chartFilters,
    isChartLoading,
    updateRegion,
    updateDates,
    updateAggregation,
    updateTechnology,
  };
}
