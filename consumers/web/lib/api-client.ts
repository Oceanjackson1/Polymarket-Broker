const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000/api/v1";

type RequestOptions = {
  method?: string;
  body?: unknown;
  headers?: Record<string, string>;
  params?: Record<string, string | number | boolean | undefined>;
};

class BrokerAPI {
  private getToken: () => string | null;

  constructor(getToken: () => string | null = () => null) {
    this.getToken = getToken;
  }

  private async request<T>(path: string, opts: RequestOptions = {}): Promise<T> {
    const { method = "GET", body, headers = {}, params } = opts;

    let url = `${API_BASE}${path}`;
    if (params) {
      const qs = new URLSearchParams();
      Object.entries(params).forEach(([k, v]) => {
        if (v !== undefined) qs.set(k, String(v));
      });
      const qsStr = qs.toString();
      if (qsStr) url += `?${qsStr}`;
    }

    const token = this.getToken();
    const reqHeaders: Record<string, string> = {
      "Content-Type": "application/json",
      ...headers,
    };
    if (token) {
      reqHeaders["X-API-Key"] = token;
    }

    const resp = await fetch(url, {
      method,
      headers: reqHeaders,
      body: body ? JSON.stringify(body) : undefined,
    });

    if (!resp.ok) {
      const error = await resp.json().catch(() => ({ error: { message: resp.statusText } }));
      throw new APIError(resp.status, error?.error?.message || resp.statusText, error?.error?.code);
    }

    return resp.json();
  }

  // Auth
  register(email: string, password: string) {
    return this.request<{ id: string; email: string }>("/auth/register", {
      method: "POST", body: { email, password },
    });
  }

  login(email: string, password: string) {
    return this.request<{ access_token: string; refresh_token: string }>("/auth/login", {
      method: "POST", body: { email, password },
    });
  }

  walletChallenge(address: string) {
    return this.request<{ nonce: string; expires_at: string }>("/auth/wallet/challenge", {
      method: "POST", body: { address },
    });
  }

  walletVerify(address: string, signature: string) {
    return this.request<{ access_token: string; refresh_token: string }>("/auth/wallet/verify", {
      method: "POST", body: { address, signature },
    });
  }

  refreshToken(refreshToken: string) {
    return this.request<{ access_token: string }>("/auth/wallet/refresh", {
      method: "POST", body: { refresh_token: refreshToken },
    });
  }

  // API Keys
  listApiKeys() {
    return this.request<{ keys: Array<{ id: string; name: string; scopes: string[]; created_at: string }> }>("/auth/keys");
  }

  createApiKey(name: string, scopes: string[]) {
    return this.request<{ key: string; key_id: string }>("/auth/keys", {
      method: "POST", body: { name, scopes },
    });
  }

  revokeApiKey(keyId: string) {
    return this.request<void>(`/auth/keys/${keyId}`, { method: "DELETE" });
  }

  // Markets
  getMarkets(params?: { limit?: number; cursor?: string; category?: string }) {
    return this.request<PaginatedResponse<Market>>("/markets", { params });
  }

  getMarket(marketId: string) {
    return this.request<Market>(`/markets/${marketId}`);
  }

  searchMarkets(q: string) {
    return this.request<PaginatedResponse<Market>>("/markets/search", { params: { q } });
  }

  getOrderbook(marketId: string) {
    return this.request<Orderbook>(`/markets/${marketId}/orderbook`);
  }

  getTrades(marketId: string) {
    return this.request<Trade[]>(`/markets/${marketId}/trades`);
  }

  getMidpoint(marketId: string) {
    return this.request<{ mid: number }>(`/markets/${marketId}/midpoint`);
  }

  // Orders (non-custodial)
  buildOrder(params: { market_id: string; side: string; price: number; size: number }) {
    return this.request<{ eip712_payload: unknown; payload_hash: string }>("/orders/build", {
      method: "POST", body: params,
    });
  }

  submitOrder(payloadHash: string, signature: string) {
    return this.request<Order>("/orders/submit", {
      method: "POST", body: { payload_hash: payloadHash, signature },
    });
  }

  getOrders(params?: { status?: string; cursor?: string; limit?: number }) {
    return this.request<PaginatedResponse<Order>>("/orders", { params });
  }

  cancelOrder(orderId: string) {
    return this.request<void>(`/orders/${orderId}`, { method: "DELETE" });
  }

  // Portfolio
  getPositions() {
    return this.request<Position[]>("/portfolio/positions");
  }

  getBalance() {
    return this.request<Balance>("/portfolio/balance");
  }

  getPnl() {
    return this.request<PnL>("/portfolio/pnl");
  }

  // Data - NBA
  getNbaGames(params?: { game_date?: string; status?: string }) {
    return this.request<PaginatedResponse<NbaGame>>("/data/nba/games", { params });
  }

  getNbaFusion(gameId: string) {
    return this.request<NbaFusion>(`/data/nba/games/${gameId}/fusion`);
  }

  // Data - Weather
  getWeatherDates() {
    return this.request<WeatherDate[]>("/data/weather/dates");
  }

  getWeatherCities(date: string) {
    return this.request<WeatherCity[]>(`/data/weather/dates/${date}/cities`);
  }

  getWeatherFusion(date: string, city: string) {
    return this.request<WeatherFusion>(`/data/weather/dates/${date}/cities/${city}/fusion`);
  }

  // Data - BTC
  getBtcPredictions() {
    return this.request<BtcPrediction[]>("/data/btc/predictions");
  }

  // Analysis
  analyzeMarket(marketId: string) {
    return this.request<MarketAnalysis>(`/analysis/market/${marketId}`);
  }

  scanMarkets() {
    return this.request<ScanResult>("/analysis/scan", { method: "POST" });
  }

  analyzeNba(gameId: string) {
    return this.request<NbaAnalysis>(`/analysis/nba/${gameId}`);
  }

  askQuestion(question: string) {
    return this.request<AskResponse>("/analysis/ask", {
      method: "POST", body: { question },
    });
  }

  // Strategies
  getStrategies() {
    return this.request<StrategyInfo[]>("/strategies");
  }

  getConvergenceOpportunities() {
    return this.request<ConvergenceOpportunity[]>("/strategies/convergence/opportunities");
  }

  executeConvergence(marketId: string, size: number) {
    return this.request<Order>("/strategies/convergence/execute", {
      method: "POST", body: { market_id: marketId, size },
    });
  }

  getConvergencePositions() {
    return this.request<ConvergencePosition[]>("/strategies/convergence/positions");
  }

  // Developer
  getUsage() {
    return this.request<UsageInfo>("/developer/usage");
  }
}

export class APIError extends Error {
  status: number;
  code?: string;

  constructor(status: number, message: string, code?: string) {
    super(message);
    this.status = status;
    this.code = code;
  }
}

// Types
export type PaginatedResponse<T> = {
  data: T[];
  pagination: { cursor: string | null; has_more: boolean; limit: number };
};

export type Market = {
  id: string;
  // Gamma API uses "question", Dome API uses "title"
  question?: string;
  title?: string;
  market_slug?: string;
  category?: string;
  tags?: string[];
  volume?: number;
  volume24hr?: number;
  volume_total?: number;
  volume_1_week?: number;
  lastTradePrice?: number;
  oneDayPriceChange?: number;
  outcomes?: string[];
  outcomePrices?: string[];
  active?: boolean;
  endDate?: string;
  end_time?: number;
  description?: string;
  image?: string;
};

export type Orderbook = { bids: OrderbookLevel[]; asks: OrderbookLevel[] };
export type OrderbookLevel = { price: string; size: string };
export type Trade = { price: string; size: string; side: string; timestamp: string };

export type Order = {
  order_id: string;
  market_id: string;
  side: string;
  type: string;
  price: number;
  size: number;
  size_filled: number;
  status: string;
  created_at: string;
};

export type Position = { market_id: string; market_question?: string; side: string; size: number; entry_price: number; current_price?: number; unrealized_pnl?: number };
export type Balance = { balance: number; locked: number; available: number };
export type PnL = { realized: number; unrealized: number; fees_paid_broker: number; fees_paid_polymarket: number };

export type NbaGame = { game_id: string; home_team: string; away_team: string; score_home: number; score_away: number; quarter?: number; time_remaining?: string; game_status: string; home_win_prob?: number; away_win_prob?: number; bias_direction?: string; bias_magnitude_bps?: number; data_updated_at?: string };
export type NbaFusion = { game_id: string; score: { home: number; away: number; quarter?: number; time_remaining?: string }; polymarket: { home_win_prob?: number; away_win_prob?: number; last_trade_price?: number }; bias_signal: { direction: string; magnitude_bps: number }; stale?: boolean; data_updated_at?: string };

export type WeatherDate = { date: string; city_count: number; event_count: number };
export type WeatherCity = { city: string; event_date: string; max_bias_range?: string; max_bias_direction?: string; max_bias_bps?: number; data_updated_at: string };
export type TempBin = { range: string; market_id?: string; market_prob: number; forecast_prob: number; bias_direction: string; bias_bps: number };
export type WeatherFusion = { city: string; date: string; event_slug: string; temp_unit: string; temp_bins: TempBin[]; max_bias: { range: string; direction: string; magnitude_bps: number }; stale: boolean; data_updated_at: string };

export type BtcPrediction = { timeframe: string; price_usd: string; prediction_prob?: string; volume?: string; recorded_at?: string };

export type MarketAnalysis = { market_id: string; ai_probability: number; market_price: number; bias_direction: string; bias_bps: number; reasoning: string };
export type ScanResult = { opportunities: Array<{ market_id: string; question: string; bias_direction: string; bias_bps: number }> };
export type NbaAnalysis = { game_id: string; suggestion: string; confidence: number };
export type AskResponse = { answer: string; sources?: string[] };

export type StrategyInfo = { slug: string; description: string };
export type ConvergenceOpportunity = { market_id: string; question: string; current_price: number; fair_value: number; profit_bps: number };
export type ConvergencePosition = { market_id: string; question: string; entry_price: number; current_price: number; size: number; pnl: number };
export type UsageInfo = { calls_today: number; calls_remaining: number; tier: string; reset_at: string };

export function createAPI(getToken: () => string | null = () => null) {
  return new BrokerAPI(getToken);
}

export default BrokerAPI;
