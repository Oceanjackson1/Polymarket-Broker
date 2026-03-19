// ─── Polydesk — Typed API Client ────────────────────────────────────────────

const API_BASE = "/api/v1";

// ─── Error ────────────────────────────────────────────────────────────────────

export class ApiError extends Error {
  constructor(
    public readonly status: number,
    public readonly statusText: string,
    message: string
  ) {
    super(message);
    this.name = "ApiError";
  }
}

// ─── Core fetch wrapper ───────────────────────────────────────────────────────

async function apiFetch<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  // Read API key from cookie (set by auth flow)
  let apiKey: string | null = null;
  if (typeof document !== "undefined") {
    const match = document.cookie.match(/(?:^|;\s*)pm_api_key=([^;]+)/);
    apiKey = match ? decodeURIComponent(match[1]) : null;
  }

  const headers: HeadersInit = {
    "Content-Type": "application/json",
    ...(apiKey ? { "X-API-Key": apiKey } : {}),
    ...options.headers,
  };

  const res = await fetch(`${API_BASE}${path}`, { ...options, headers });

  if (!res.ok) {
    let message = res.statusText;
    try {
      const body = (await res.json()) as { detail?: string; message?: string };
      message = body.detail ?? body.message ?? message;
    } catch {
      // non-JSON error body — keep statusText
    }
    throw new ApiError(res.status, res.statusText, message);
  }

  // 204 No Content
  if (res.status === 204) return undefined as T;

  return res.json() as Promise<T>;
}

// ─── Auth Types ───────────────────────────────────────────────────────────────

export interface UserResponse {
  id: string;
  email: string;
  tier: string;
  created_at: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface ApiKeyListItem {
  id: string;
  name: string;
  key_hint: string;
  scopes: string[];
  is_active: boolean;
  created_at: string;
  last_used_at: string | null;
}

export interface ApiKeyCreatedResponse {
  id: string;
  name: string;
  key: string;
  key_hint: string;
  scopes: string[];
  created_at: string;
}

// ─── Orders Types ─────────────────────────────────────────────────────────────

export interface OrderResponse {
  order_id: string;
  market_id: string;
  token_id: string;
  side: "BUY" | "SELL";
  type: "LIMIT" | "MARKET" | "GTD";
  price: number;
  size: number;
  size_filled: number;
  size_remaining: number;
  status: string;
  broker_fee_bps: number;
  polymarket_order_id: string | null;
  mode: string;
  created_at: string;
  updated_at: string;
  expires_at: string | null;
}

export interface PaginatedOrders {
  data: OrderResponse[];
  pagination: Record<string, unknown>;
}

export interface BuildOrderResponse {
  eip712_payload: Record<string, unknown>;
  payload_hash: string;
}

// ─── Portfolio Types ──────────────────────────────────────────────────────────

export interface PositionsResponse {
  positions: {
    market_id: string;
    token_id: string;
    side: string;
    size_held: number;
    avg_price: number;
    notional: number;
    order_count: number;
  }[];
}

export interface BalanceResponse {
  balance: number;
  locked: number;
  available: number;
}

export interface PnlResponse {
  realized: number;
  unrealized: number;
  fees_paid_broker: number;
  fees_paid_polymarket: number;
}

// ─── NBA Data Types ───────────────────────────────────────────────────────────

export interface NbaGameResponse {
  game_id: string;
  home_team: string;
  away_team: string;
  game_date: string;
  game_status: string;
  score_home: number | null;
  score_away: number | null;
  quarter: number | null;
  time_remaining: string | null;
  market_id: string | null;
  data_updated_at: string;
}

export interface NbaFusionResponse {
  game_id: string;
  score: {
    home: number | null;
    away: number | null;
    quarter: number | null;
    time_remaining: string | null;
  };
  polymarket: {
    home_win_prob: number | null;
    away_win_prob: number | null;
    last_trade_price: number | null;
  };
  bias_signal: {
    direction: string | null;
    magnitude_bps: number | null;
  };
  stale: boolean;
  data_updated_at: string;
}

export interface PaginatedNbaGames {
  data: NbaGameResponse[];
  pagination: {
    cursor: string | null;
    has_more: boolean;
    limit: number;
  };
}

export interface NbaGameDetailResponse {
  stale: boolean;
  data_updated_at: string;
  data: NbaGameResponse;
}

// ─── BTC Data Types ───────────────────────────────────────────────────────────

export interface BtcSnapshotResponse {
  id: number;
  timeframe: string;
  price_usd: string;
  market_id: string | null;
  prediction_prob: string | null;
  volume: string | null;
  recorded_at: string;
}

export interface BtcTimeframeResponse {
  stale: boolean;
  data_updated_at: string | null;
  data: BtcSnapshotResponse[];
}

export interface BtcHistoryResponse {
  data: BtcSnapshotResponse[];
  pagination: {
    limit: number;
    count: number;
  };
}

// ─── Sports Data Types ────────────────────────────────────────────────────────

export interface SportsCategoryResponse {
  slug: string;
  active_events: number;
}

export interface SportsEventResponse {
  market_id: string;
  sport_slug: string;
  question: string;
  outcomes: unknown[];
  status: string;
  resolution: unknown | null;
  volume: number | null;
  end_date: string | null;
  data_updated_at: string;
}

export interface PaginatedSportsEvents {
  stale: boolean;
  data_updated_at: string | null;
  data: SportsEventResponse[];
  pagination: {
    cursor: string | null;
    has_more: boolean;
    limit: number;
  };
}

// ─── Weather Data Types ──────────────────────────────────────────────────────

export interface WeatherDateResponse {
  date: string;
  city_count: number;
  event_count: number;
}

export interface WeatherCityResponse {
  city: string;
  event_date: string;
  max_bias_range: string | null;
  max_bias_direction: string | null;
  max_bias_bps: number | null;
  data_updated_at: string;
}

export interface WeatherTempBin {
  range: string;
  market_id: string | null;
  market_prob: number;
  forecast_prob: number;
  bias_direction: string;
  bias_bps: number;
}

export interface WeatherFusionResponse {
  city: string;
  date: string;
  event_slug: string;
  temp_unit: string;
  temp_bins: WeatherTempBin[];
  max_bias: {
    range: string;
    direction: string;
    magnitude_bps: number;
  };
  stale: boolean;
  data_updated_at: string;
}

// ─── Analysis Types ──────────────────────────────────────────────────────────

export interface MarketAnalysisResponse {
  market_id: string;
  ai_probability: number;
  market_price: number;
  bias_direction: string;
  bias_bps: number;
  reasoning: string;
}

export interface ScanOpportunity {
  market_id: string;
  question: string;
  bias_direction: string;
  bias_bps: number;
}

export interface ScanResponse {
  opportunities: ScanOpportunity[];
}

export interface AskResponse {
  answer: string;
  sources?: string[];
}

// ─── Strategies Types ────────────────────────────────────────────────────────

export interface ConvergenceOpportunity {
  market_id: string;
  question: string;
  current_price: number;
  fair_value: number;
  profit_bps: number;
}

export interface ConvergencePosition {
  market_id: string;
  question: string;
  entry_price: number;
  current_price: number;
  size: number;
  pnl: number;
}

// ─── Markets Types (raw from Polymarket Gamma/CLOB — loosely typed) ───────────

export interface MarketResponse {
  [key: string]: unknown;
  id?: string;
  question?: string;
}

export interface MarketsListResponse {
  data: MarketResponse[];
  pagination: {
    limit: number;
    offset: number;
    has_more: boolean;
  };
}

export interface ListMarketsParams {
  limit?: number;
  offset?: number;
  [key: string]: unknown;
}

// ─── Auth request shapes ──────────────────────────────────────────────────────

export interface RegisterRequest {
  email: string;
  password: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface CreateApiKeyRequest {
  name: string;
  scopes?: string[];
}

// ─── Auth API ─────────────────────────────────────────────────────────────────

export const authApi = {
  register: (req: RegisterRequest): Promise<TokenResponse> =>
    apiFetch<TokenResponse>("/auth/register", {
      method: "POST",
      body: JSON.stringify(req),
    }),

  login: (req: LoginRequest): Promise<TokenResponse> =>
    apiFetch<TokenResponse>("/auth/login", {
      method: "POST",
      body: JSON.stringify(req),
    }),

  me: (): Promise<UserResponse> => apiFetch<UserResponse>("/auth/me"),

  apiKeys: (): Promise<ApiKeyListItem[]> =>
    apiFetch<ApiKeyListItem[]>("/auth/api-keys"),

  createApiKey: (req: CreateApiKeyRequest): Promise<ApiKeyCreatedResponse> =>
    apiFetch<ApiKeyCreatedResponse>("/auth/api-keys", {
      method: "POST",
      body: JSON.stringify(req),
    }),

  deleteApiKey: (id: string): Promise<void> =>
    apiFetch<void>(`/auth/api-keys/${id}`, { method: "DELETE" }),
};

// ─── Orders API ───────────────────────────────────────────────────────────────

export interface BuildOrderRequest {
  market_id: string;
  token_id: string;
  side: "BUY" | "SELL";
  type: "LIMIT" | "MARKET" | "GTD";
  price?: number;
  size: number;
  expires_at?: string;
}

export interface SubmitOrderRequest {
  payload_hash: string;
  signature: string;
}

export const ordersApi = {
  list: (): Promise<PaginatedOrders> =>
    apiFetch<PaginatedOrders>("/orders/"),

  build: (req: BuildOrderRequest): Promise<BuildOrderResponse> =>
    apiFetch<BuildOrderResponse>("/orders/build", {
      method: "POST",
      body: JSON.stringify(req),
    }),

  submit: (req: SubmitOrderRequest): Promise<OrderResponse> =>
    apiFetch<OrderResponse>("/orders/submit", {
      method: "POST",
      body: JSON.stringify(req),
    }),

  cancel: (orderId: string): Promise<void> =>
    apiFetch<void>(`/orders/${orderId}`, { method: "DELETE" }),
};

// ─── Portfolio API ────────────────────────────────────────────────────────────

export const portfolioApi = {
  positions: (): Promise<PositionsResponse> =>
    apiFetch<PositionsResponse>("/portfolio/positions"),

  balance: (): Promise<BalanceResponse> =>
    apiFetch<BalanceResponse>("/portfolio/balance"),

  pnl: (): Promise<PnlResponse> => apiFetch<PnlResponse>("/portfolio/pnl"),
};

// ─── NBA API ──────────────────────────────────────────────────────────────────

export const nbaApi = {
  games: (): Promise<PaginatedNbaGames> =>
    apiFetch<PaginatedNbaGames>("/data/nba/games"),

  game: (id: string): Promise<NbaGameDetailResponse> =>
    apiFetch<NbaGameDetailResponse>(`/data/nba/games/${id}`),

  fusion: (id: string): Promise<NbaFusionResponse> =>
    apiFetch<NbaFusionResponse>(`/data/nba/games/${id}/fusion`),
};

// ─── Sports API ───────────────────────────────────────────────────────────────

export const sportsApi = {
  categories: (): Promise<SportsCategoryResponse[]> =>
    apiFetch<SportsCategoryResponse[]>("/data/sports/categories"),

  events: (sport: string): Promise<PaginatedSportsEvents> =>
    apiFetch<PaginatedSportsEvents>(
      `/data/sports/${encodeURIComponent(sport)}/events`
    ),
};

// ─── BTC API ─────────────────────────────────────────────────────────────────

export const btcApi = {
  predictions: (): Promise<BtcSnapshotResponse[]> =>
    apiFetch<BtcSnapshotResponse[]>("/data/btc/predictions"),

  timeframe: (tf: string): Promise<BtcTimeframeResponse> =>
    apiFetch<BtcTimeframeResponse>(
      `/data/btc/predictions/${encodeURIComponent(tf)}`
    ),

  history: (tf: string): Promise<BtcHistoryResponse> =>
    apiFetch<BtcHistoryResponse>(
      `/data/btc/history/${encodeURIComponent(tf)}`
    ),
};

// ─── Markets API ──────────────────────────────────────────────────────────────

export const marketsApi = {
  list: (params?: ListMarketsParams): Promise<MarketsListResponse> => {
    const qs = params
      ? "?" +
        new URLSearchParams(
          Object.fromEntries(
            Object.entries(params)
              .filter(([, v]) => v !== undefined)
              .map(([k, v]) => [k, String(v)])
          )
        ).toString()
      : "";
    return apiFetch<MarketsListResponse>(`/markets/${qs}`);
  },

  get: (id: string): Promise<MarketResponse> =>
    apiFetch<MarketResponse>(`/markets/${id}`),

  orderbook: (id: string): Promise<Record<string, unknown>> =>
    apiFetch<Record<string, unknown>>(`/markets/${id}/orderbook`),

  trades: (id: string): Promise<Record<string, unknown>> =>
    apiFetch<Record<string, unknown>>(`/markets/${id}/trades`),

  midpoint: (id: string): Promise<Record<string, unknown>> =>
    apiFetch<Record<string, unknown>>(`/markets/${id}/midpoint`),

  search: (q: string): Promise<MarketsListResponse> =>
    apiFetch<MarketsListResponse>(`/markets/search?q=${encodeURIComponent(q)}`),
};

// ─── Weather API ─────────────────────────────────────────────────────────────

export const weatherApi = {
  dates: (): Promise<WeatherDateResponse[]> =>
    apiFetch<WeatherDateResponse[]>("/data/weather/dates"),

  cities: (date: string): Promise<WeatherCityResponse[]> =>
    apiFetch<WeatherCityResponse[]>(`/data/weather/dates/${date}/cities`),

  fusion: (date: string, city: string): Promise<WeatherFusionResponse> =>
    apiFetch<WeatherFusionResponse>(`/data/weather/dates/${date}/cities/${encodeURIComponent(city)}/fusion`),
};

// ─── Analysis API ────────────────────────────────────────────────────────────

export const analysisApi = {
  market: (marketId: string): Promise<MarketAnalysisResponse> =>
    apiFetch<MarketAnalysisResponse>(`/analysis/market/${encodeURIComponent(marketId)}`),

  scan: (): Promise<ScanResponse> =>
    apiFetch<ScanResponse>("/analysis/scan", { method: "POST" }),

  nba: (gameId: string): Promise<Record<string, unknown>> =>
    apiFetch<Record<string, unknown>>(`/analysis/nba/${encodeURIComponent(gameId)}`),

  ask: (question: string): Promise<AskResponse> =>
    apiFetch<AskResponse>("/analysis/ask", {
      method: "POST",
      body: JSON.stringify({ question }),
    }),
};

// ─── Strategies API ──────────────────────────────────────────────────────────

export const strategiesApi = {
  opportunities: (): Promise<ConvergenceOpportunity[]> =>
    apiFetch<ConvergenceOpportunity[]>("/strategies/convergence/opportunities"),

  execute: (marketId: string, size: number): Promise<OrderResponse> =>
    apiFetch<OrderResponse>("/strategies/convergence/execute", {
      method: "POST",
      body: JSON.stringify({ market_id: marketId, size }),
    }),

  positions: (): Promise<ConvergencePosition[]> =>
    apiFetch<ConvergencePosition[]>("/strategies/convergence/positions"),
};
