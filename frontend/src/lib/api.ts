// ─── Polymarket Broker — Typed API Client ────────────────────────────────────

const API_BASE =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

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

// ─── Types ────────────────────────────────────────────────────────────────────

export interface Market {
  id: string;
  question: string;
  category: string;
  status: "open" | "closed" | "resolved";
  yes_price: number;
  no_price: number;
  volume: number;
  liquidity: number;
  end_date: string;
}

export interface OrderbookLevel {
  price: number;
  size: number;
}

export interface Orderbook {
  market_id: string;
  yes: { bids: OrderbookLevel[]; asks: OrderbookLevel[] };
  no: { bids: OrderbookLevel[]; asks: OrderbookLevel[] };
  timestamp: string;
}

export interface Trade {
  id: string;
  market_id: string;
  side: "YES" | "NO";
  price: number;
  size: number;
  timestamp: string;
}

export interface Midpoint {
  market_id: string;
  yes_midpoint: number;
  no_midpoint: number;
}

export interface Position {
  market_id: string;
  market_question: string;
  side: "YES" | "NO";
  size: number;
  avg_price: number;
  current_price: number;
  unrealized_pnl: number;
  realized_pnl: number;
}

export interface Balance {
  usdc: number;
  reserved: number;
  available: number;
}

export interface PnL {
  total_realized: number;
  total_unrealized: number;
  today_pnl: number;
  all_time_pnl: number;
}

export interface Order {
  id: string;
  market_id: string;
  side: "YES" | "NO";
  type: "limit" | "market";
  price: number;
  size: number;
  status: "open" | "filled" | "cancelled" | "partial";
  created_at: string;
}

export interface BuildOrderRequest {
  market_id: string;
  side: "YES" | "NO";
  type: "limit" | "market";
  price?: number;
  size: number;
}

export interface BuiltOrder {
  order_id: string;
  signature_data: Record<string, unknown>;
  estimated_fill: number;
  fee: number;
}

export interface SubmitOrderRequest {
  order_id: string;
  signature: string;
}

export interface SportCategory {
  id: string;
  name: string;
  slug: string;
  event_count: number;
}

export interface SportEvent {
  id: string;
  sport: string;
  home_team: string;
  away_team: string;
  start_time: string;
  status: string;
  market_id?: string;
}

export interface NbaGame {
  id: string;
  home_team: string;
  away_team: string;
  home_score: number;
  away_score: number;
  quarter: number;
  time_remaining: string;
  status: "scheduled" | "live" | "final";
  game_date: string;
}

export interface NbaGameFusion {
  game: NbaGame;
  market: Market | null;
  bias_signal: string | null;
  bias_bps: number | null;
  yes_price: number | null;
  model_probability: number | null;
}

export interface BtcPrediction {
  timeframe: string;
  direction: "UP" | "DOWN";
  probability: number;
  model_version: string;
  generated_at: string;
}

export interface BtcOnchain {
  price: number;
  volume_24h: number;
  market_cap: number;
  dominance: number;
  fear_greed_index: number;
  timestamp: string;
}

export interface BtcHistoryPoint {
  timestamp: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export interface ListMarketsParams {
  category?: string;
  status?: "open" | "closed" | "resolved";
  limit?: number;
  offset?: number;
}

// ─── Markets API ──────────────────────────────────────────────────────────────

export const marketsApi = {
  list: (params?: ListMarketsParams): Promise<Market[]> => {
    const qs = params
      ? "?" + new URLSearchParams(params as Record<string, string>).toString()
      : "";
    return apiFetch<Market[]>(`/markets/${qs}`);
  },

  get: (id: string): Promise<Market> => apiFetch<Market>(`/markets/${id}`),

  orderbook: (id: string): Promise<Orderbook> =>
    apiFetch<Orderbook>(`/markets/${id}/orderbook`),

  trades: (id: string): Promise<Trade[]> =>
    apiFetch<Trade[]>(`/markets/${id}/trades`),

  midpoint: (id: string): Promise<Midpoint> =>
    apiFetch<Midpoint>(`/markets/${id}/midpoint`),

  search: (q: string): Promise<Market[]> =>
    apiFetch<Market[]>(`/markets/?q=${encodeURIComponent(q)}`),
};

// ─── Orders API ───────────────────────────────────────────────────────────────

export const ordersApi = {
  list: (): Promise<Order[]> => apiFetch<Order[]>("/orders/"),

  build: (req: BuildOrderRequest): Promise<BuiltOrder> =>
    apiFetch<BuiltOrder>("/orders/build", {
      method: "POST",
      body: JSON.stringify(req),
    }),

  submit: (req: SubmitOrderRequest): Promise<Order> =>
    apiFetch<Order>("/orders/submit", {
      method: "POST",
      body: JSON.stringify(req),
    }),
};

// ─── Portfolio API ────────────────────────────────────────────────────────────

export const portfolioApi = {
  positions: (): Promise<Position[]> =>
    apiFetch<Position[]>("/portfolio/positions"),

  balance: (): Promise<Balance> => apiFetch<Balance>("/portfolio/balance"),

  pnl: (): Promise<PnL> => apiFetch<PnL>("/portfolio/pnl"),
};

// ─── NBA API ──────────────────────────────────────────────────────────────────

export const nbaApi = {
  games: (): Promise<NbaGame[]> => apiFetch<NbaGame[]>("/data/nba/games"),

  game: (id: string): Promise<NbaGame> =>
    apiFetch<NbaGame>(`/data/nba/games/${id}`),

  fusion: (id: string): Promise<NbaGameFusion> =>
    apiFetch<NbaGameFusion>(`/data/nba/games/${id}/fusion`),
};

// ─── Sports API ───────────────────────────────────────────────────────────────

export const sportsApi = {
  categories: (): Promise<SportCategory[]> =>
    apiFetch<SportCategory[]>("/data/sports/categories"),

  events: (sport: string): Promise<SportEvent[]> =>
    apiFetch<SportEvent[]>(`/data/sports/${encodeURIComponent(sport)}/events`),
};

// ─── BTC API ─────────────────────────────────────────────────────────────────

export const btcApi = {
  predictions: (): Promise<BtcPrediction[]> =>
    apiFetch<BtcPrediction[]>("/data/btc/predictions"),

  prediction: (timeframe: string): Promise<BtcPrediction> =>
    apiFetch<BtcPrediction>(
      `/data/btc/predictions/${encodeURIComponent(timeframe)}`
    ),

  onchain: (): Promise<BtcOnchain> =>
    apiFetch<BtcOnchain>("/data/btc/onchain"),

  history: (): Promise<BtcHistoryPoint[]> =>
    apiFetch<BtcHistoryPoint[]>("/data/btc/history"),
};

// ─── Auth API ─────────────────────────────────────────────────────────────────

export interface RegisterRequest {
  email: string;
  password: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
}

export interface ApiKeyResponse {
  key: string;
  created_at: string;
}

export const authApi = {
  register: (req: RegisterRequest): Promise<AuthResponse> =>
    apiFetch<AuthResponse>("/auth/register", {
      method: "POST",
      body: JSON.stringify(req),
    }),

  login: (req: LoginRequest): Promise<AuthResponse> =>
    apiFetch<AuthResponse>("/auth/login", {
      method: "POST",
      body: JSON.stringify(req),
    }),

  apiKeys: (): Promise<ApiKeyResponse[]> =>
    apiFetch<ApiKeyResponse[]>("/auth/api-keys"),
};
