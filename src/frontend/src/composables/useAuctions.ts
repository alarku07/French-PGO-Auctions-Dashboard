import { ref, type Ref } from "vue";
import {
  getAuctions,
  getUpcomingAuctions,
  getStats,
  getRegions,
  getAuctionEvents,
  getAuctionEventYears,
  type AuctionRecord,
  type UpcomingAuction,
  type AuctionEventRecord,
  type StatsResponse,
  type Pagination,
  type AuctionParams,
} from "@/services/api";

interface AuctionsState {
  auctions: Ref<AuctionRecord[]>;
  auctionPagination: Ref<Pagination | null>;
  upcoming: Ref<UpcomingAuction[]>;
  auctionEvents: Ref<AuctionEventRecord[]>;
  auctionEventYears: Ref<number[]>;
  stats: Ref<StatsResponse | null>;
  regions: Ref<string[]>;
  isLoading: Ref<boolean>;
  error: Ref<string | null>;
  fetchAll: () => Promise<void>;
  updateAuctionFilter: (filter: { start_date?: string; end_date?: string; region?: string }) => void;
  updateAuctionPage: (page: number) => void;
  updateAuctionEventsYear: (year: number) => void;
}

export function useAuctions(): AuctionsState {
  const auctions = ref<AuctionRecord[]>([]);
  const auctionPagination = ref<Pagination | null>(null);
  const upcoming = ref<UpcomingAuction[]>([]);
  const auctionEvents = ref<AuctionEventRecord[]>([]);
  const auctionEventYears = ref<number[]>([]);
  const stats = ref<StatsResponse | null>(null);
  const regions = ref<string[]>([]);
  const isLoading = ref(false);
  const error = ref<string | null>(null);

  // Current auction table filter state
  const currentFilter = ref<AuctionParams>({ page_size: 24 });

  async function fetchAuctions(params?: AuctionParams) {
    try {
      const response = await getAuctions(params);
      auctions.value = response.data;
      auctionPagination.value = response.pagination;
    } catch (err) {
      error.value = "Failed to load auction results.";
      console.error(err);
    }
  }

  async function fetchAll() {
    isLoading.value = true;
    error.value = null;
    const year = new Date().getFullYear();
    try {
      await Promise.allSettled([
        fetchAuctions(currentFilter.value),
        getUpcomingAuctions().then((r) => { upcoming.value = r.data; }),
        getStats().then((r) => { stats.value = r; }),
        getRegions().then((r) => { regions.value = r.data; }),
        getAuctionEvents({
          start_date: `${year}-01-01`,
          end_date: `${year}-12-31`,
        }).then((r) => { auctionEvents.value = r.data; }),
        getAuctionEventYears().then((r) => { auctionEventYears.value = r.data; }),
      ]);
    } finally {
      isLoading.value = false;
    }
  }

  function updateAuctionFilter(filter: { start_date?: string; end_date?: string; region?: string }) {
    currentFilter.value = { ...currentFilter.value, ...filter, page: 1 };
    fetchAuctions(currentFilter.value);
  }

  function updateAuctionPage(page: number) {
    currentFilter.value = { ...currentFilter.value, page };
    fetchAuctions(currentFilter.value);
  }

  async function updateAuctionEventsYear(year: number) {
    try {
      const response = await getAuctionEvents({
        start_date: `${year}-01-01`,
        end_date: `${year}-12-31`,
      });
      auctionEvents.value = response.data;
    } catch (err) {
      console.error(err);
    }
  }

  return {
    auctions,
    auctionPagination,
    upcoming,
    auctionEvents,
    auctionEventYears,
    stats,
    regions,
    isLoading,
    error,
    fetchAll,
    updateAuctionFilter,
    updateAuctionPage,
    updateAuctionEventsYear,
  };
}
