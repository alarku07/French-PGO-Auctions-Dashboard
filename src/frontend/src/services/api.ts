import axios from "axios";

const apiClient = axios.create({
  baseURL: "/api/v1",
  headers: {
    "Content-Type": "application/json",
  },
});

// ─── Response Types ────────────────────────────────────────────────────────

export interface AuctionRecord {
  id: number;
  auction_date: string;
  region: string;
  production_period: string;
  technology: string | null;
  volume_offered_mwh: number | null;
  volume_allocated_mwh: number | null;
  num_bids: number | null;
  num_winning_bids: number | null;
  weighted_avg_price_eur: number | null;
  status: "past" | "upcoming";
}

export interface UpcomingAuction {
  id: number;
  auction_date: string;
  region: string;
  production_period: string;
  order_book_open: string | null;
  order_book_close: string | null;
  order_matching: string | null;
}

export interface Pagination {
  page: number;
  page_size: number;
  total_items: number;
  total_pages: number;
}

export interface AuctionListResponse {
  data: AuctionRecord[];
  pagination: Pagination;
}

export interface UpcomingAuctionListResponse {
  data: UpcomingAuction[];
  count: number;
}

export interface StatsResponse {
  total_auctions_held: number;
  total_volume_awarded_mwh: number | null;
  overall_weighted_avg_price_eur: number | null;
  last_updated: string | null;
}

export interface PriceDataPoint {
  auction_date: string;
  region: string;
  weighted_avg_price_eur: number | null;
  volume_allocated_mwh: number | null;
}

export interface PriceChartFilters {
  start_date: string | null;
  end_date: string | null;
  region: string | null;
  technology: string | null;
}

export interface PriceChartResponse {
  data: PriceDataPoint[];
  filters: PriceChartFilters;
}

export interface VolumeDataPoint {
  period: string;
  region: string;
  volume_offered_mwh: number | null;
  volume_allocated_mwh: number | null;
}

export interface VolumeChartFilters {
  start_date: string | null;
  end_date: string | null;
  region: string | null;
  technology: string | null;
  aggregation: string;
}

export interface VolumeChartResponse {
  data: VolumeDataPoint[];
  filters: VolumeChartFilters;
}

// ─── Query Param Types ─────────────────────────────────────────────────────

export interface AuctionParams {
  start_date?: string;
  end_date?: string;
  region?: string;
  technology?: string;
  page?: number;
  page_size?: number;
  sort_by?: string;
  sort_order?: "asc" | "desc";
}

export interface ChartParams {
  start_date?: string;
  end_date?: string;
  region?: string;
  technology?: string;
}

export interface VolumeChartParams extends ChartParams {
  aggregation?: "per_auction" | "monthly" | "yearly";
}

// ─── API Functions ─────────────────────────────────────────────────────────

export async function getAuctions(params?: AuctionParams): Promise<AuctionListResponse> {
  const response = await apiClient.get<AuctionListResponse>("/auctions", { params });
  return response.data;
}

export async function getUpcomingAuctions(): Promise<UpcomingAuctionListResponse> {
  const response = await apiClient.get<UpcomingAuctionListResponse>("/auctions/upcoming");
  return response.data;
}

export async function getStats(): Promise<StatsResponse> {
  const response = await apiClient.get<StatsResponse>("/stats");
  return response.data;
}

export async function getChartPrices(params?: ChartParams): Promise<PriceChartResponse> {
  const response = await apiClient.get<PriceChartResponse>("/charts/prices", { params });
  return response.data;
}

export async function getChartVolumes(params?: VolumeChartParams): Promise<VolumeChartResponse> {
  const response = await apiClient.get<VolumeChartResponse>("/charts/volumes", { params });
  return response.data;
}

export async function getRegions(): Promise<{ data: string[] }> {
  const response = await apiClient.get<{ data: string[] }>("/regions");
  return response.data;
}

export async function getTechnologies(): Promise<{ data: string[] }> {
  const response = await apiClient.get<{ data: string[] }>("/technologies");
  return response.data;
}

// ─── AuctionEvent Types ─────────────────────────────────────────────────────

export interface AuctionSummary {
  id: number;
  auction_date: string;
  region: string;
  production_period: string;
  technology: string | null;
  status: "past" | "upcoming";
}

export interface AuctionEventRecord {
  id: number;
  event_date: string;
  status: "upcoming" | "completed";
  is_cancelled: boolean;
  auctioning_month: string | null;
  production_month: string | null;
  order_book_open: string | null;
  cash_trading_limits_modification: string | null;
  order_book_close: string | null;
  order_matching: string | null;
  auctions: AuctionSummary[];
}

export interface AuctionEventListResponse {
  data: AuctionEventRecord[];
  count: number;
}

export interface AuctionEventYearsResponse {
  data: number[];
}

export interface AuctionEventParams {
  include_cancelled?: boolean;
  start_date?: string;
  end_date?: string;
}

// ─── AuctionEvent API Function ──────────────────────────────────────────────

export async function getAuctionEvents(
  params?: AuctionEventParams,
): Promise<AuctionEventListResponse> {
  const response = await apiClient.get<AuctionEventListResponse>(
    "/auction-events",
    { params },
  );
  return response.data;
}

export async function getAuctionEventYears(): Promise<AuctionEventYearsResponse> {
  const response = await apiClient.get<AuctionEventYearsResponse>("/auction-events/years");
  return response.data;
}
