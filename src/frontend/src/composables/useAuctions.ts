import { ref, type Ref } from "vue";
import {
  getAuctions,
  getUpcomingAuctions,
  getStats,
  getRegions,
  getAuctionEvents,
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
  stats: Ref<StatsResponse | null>;
  regions: Ref<string[]>;
  isLoading: Ref<boolean>;
  error: Ref<string | null>;
  fetchAll: () => Promise<void>;
  updateAuctionFilter: (filter: { start_date?: string; end_date?: string }) => void;
  updateAuctionPage: (page: number) => void;
}

export function useAuctions(): AuctionsState {
  const auctions = ref<AuctionRecord[]>([]);
  const auctionPagination = ref<Pagination | null>(null);
  const upcoming = ref<UpcomingAuction[]>([]);
  const auctionEvents = ref<AuctionEventRecord[]>([]);
  const stats = ref<StatsResponse | null>(null);
  const regions = ref<string[]>([]);
  const isLoading = ref(false);
  const error = ref<string | null>(null);

  // Current auction table filter state
  const currentFilter = ref<AuctionParams>({});

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
      ]);
    } finally {
      isLoading.value = false;
    }
  }

  function updateAuctionFilter(filter: { start_date?: string; end_date?: string }) {
    currentFilter.value = { ...currentFilter.value, ...filter, page: 1 };
    fetchAuctions(currentFilter.value);
  }

  function updateAuctionPage(page: number) {
    currentFilter.value = { ...currentFilter.value, page };
    fetchAuctions(currentFilter.value);
  }

  return {
    auctions,
    auctionPagination,
    upcoming,
    auctionEvents,
    stats,
    regions,
    isLoading,
    error,
    fetchAll,
    updateAuctionFilter,
    updateAuctionPage,
  };
}
