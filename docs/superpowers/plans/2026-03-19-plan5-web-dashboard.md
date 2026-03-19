# Plan 5: Web Dashboard Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Next.js Web Dashboard in `consumers/web/` enabling traders to browse markets, place non-custodial orders, manage portfolios, and access NBA/Weather/BTC fusion data + AI analysis.

**Spec Reference:** `docs/superpowers/specs/2026-03-19-web-dashboard-design.md`

**Tech Stack:** Next.js 15 (App Router), Tailwind CSS 4, shadcn/ui, wagmi 2, viem 2, RainbowKit 2, @tanstack/react-query 5, next-intl 4, recharts 2.

---

## Task Overview

| Task | Deliverable | Pages |
|------|-------------|-------|
| 1 | Project scaffolding + providers + layout | — |
| 2 | Auth pages (Email + Wallet) | login, register, wallet |
| 3 | Markets page (SSR) | markets |
| 4 | Trade page (OrderBook + OrderForm + WS) | trade/[id] |
| 5 | Portfolio + Orders pages | portfolio, orders |
| 6 | Data pages (NBA + Weather + BTC) | data/nba, data/weather, data/btc |
| 7 | Analysis + Strategies pages | analysis, strategies |
| 8 | Settings page + i18n | settings |

---

### Task 1: Project Scaffolding + Providers + Layout

**Deliverable:** Next.js project boots, dark theme renders, TopNav visible, API client configured.

- [ ] **Step 1: Initialize Next.js project**

```bash
cd consumers/ && npx create-next-app@latest web --typescript --tailwind --app --src-dir=false --import-alias="@/*"
```

- [ ] **Step 2: Install dependencies**

```bash
cd consumers/web && npm install @tanstack/react-query wagmi viem @rainbow-me/rainbowkit next-intl recharts lucide-react class-variance-authority clsx tailwind-merge
```

- [ ] **Step 3: Initialize shadcn/ui**

```bash
npx shadcn@latest init
npx shadcn@latest add button card input table tabs badge dialog dropdown-menu toast select separator
```

- [ ] **Step 4: Create lib/api-client.ts**

Typed API client wrapping all 43 REST endpoints. Uses `fetch` with JWT from auth context. Export singleton `api` instance.

- [ ] **Step 5: Create lib/hooks/useWebSocket.ts**

Generic WebSocket hook with auto-reconnect (exponential backoff 3s → 30s max), connection status, typed data.

- [ ] **Step 6: Create wagmi config**

`lib/wagmi-config.ts`: Polygon chain, RainbowKit connectors (MetaMask, WalletConnect, Coinbase Wallet). `NEXT_PUBLIC_WALLET_CONNECT_PROJECT_ID` env var.

- [ ] **Step 7: Create root layout with providers**

`app/layout.tsx`: ThemeProvider (dark) → I18nProvider → AuthProvider → QueryClientProvider → WagmiProvider + RainbowKitProvider. Dark mode via Tailwind `dark` class on `<html>`.

- [ ] **Step 8: Create Dashboard layout with TopNav**

`app/(dashboard)/layout.tsx` + `components/layout/TopNav.tsx`: Logo, nav links (Markets, Portfolio, Data dropdown, Analysis, Strategies, Settings), wallet connect button, language switcher.

- [ ] **Step 9: Create auth layout**

`app/(auth)/layout.tsx`: Centered card, no navigation. Redirect to /markets if already authenticated.

- [ ] **Step 10: Create .env.local.example**

```
NEXT_PUBLIC_API_BASE=http://localhost:8000/api/v1
NEXT_PUBLIC_WS_BASE=ws://localhost:8000
NEXT_PUBLIC_WALLET_CONNECT_PROJECT_ID=your_project_id
NEXT_PUBLIC_CHAIN_ID=137
NEXT_PUBLIC_DEFAULT_LOCALE=en
```

- [ ] **Step 11: Verify**

`npm run dev` → opens browser → sees dark dashboard shell with TopNav → no errors in console.

---

### Task 2: Auth Pages (Email + Wallet)

**Deliverable:** User can register, login, connect wallet, and see auth state in TopNav.

- [ ] **Step 1: Create AuthProvider + useAuth hook**

`lib/hooks/useAuth.ts`: login, register, logout, refreshToken. Store JWT in memory + httpOnly cookie. Expose `user`, `isAuthenticated`.

- [ ] **Step 2: Create useWallet hook**

`lib/hooks/useWallet.ts`: wraps wagmi `useAccount`, `useConnect`, `useSignMessage`. Adds `bindWallet` (calls `/auth/wallet/challenge` → sign → `/auth/wallet/verify`).

- [ ] **Step 3: Build LoginForm + RegisterForm components**

`components/auth/LoginForm.tsx`, `RegisterForm.tsx`: shadcn form with email + password. Error handling, loading states.

- [ ] **Step 4: Build WalletButton + BindWalletModal**

`components/auth/WalletButton.tsx`: RainbowKit ConnectButton wrapper for TopNav. `BindWalletModal.tsx`: dialog for Email users to bind wallet.

- [ ] **Step 5: Build auth pages**

`app/(auth)/login/page.tsx`, `register/page.tsx`, `wallet/page.tsx`. Wallet page triggers RainbowKit connect → challenge-response → redirect to /markets.

- [ ] **Step 6: Protect dashboard routes**

Middleware or layout-level check: redirect to /login if no valid JWT.

- [ ] **Step 7: Verify**

Register → login → see user in TopNav → connect wallet → see wallet address → logout → redirected to login.

---

### Task 3: Markets Page (SSR)

**Deliverable:** SEO-friendly market listing with search and category filters.

- [ ] **Step 1: Build MarketCard component**

`components/market/MarketCard.tsx`: question, YES/NO price, 24h volume, 24h price change. Click → navigate to `/trade/[id]`.

- [ ] **Step 2: Build MarketSearch component**

`components/market/MarketSearch.tsx`: search input + category tabs (All, Sports, Crypto, Politics, Weather, etc.).

- [ ] **Step 3: Build markets page (SSR)**

`app/(dashboard)/markets/page.tsx`: Server component. Fetches `GET /markets` server-side. Renders MarketCard grid. Cursor-based pagination with "Load More".

- [ ] **Step 4: Add client-side search**

Search input triggers `GET /markets/search?q=` via react-query. Category filter passes `category` param.

- [ ] **Step 5: Verify**

Page loads with market cards → search works → category filter works → click card navigates to trade page → view page source shows SSR content.

---

### Task 4: Trade Page (OrderBook + OrderForm + WebSocket)

**Deliverable:** Real-time orderbook, order placement via wallet signing.

- [ ] **Step 1: Build OrderBook component**

`components/market/OrderBook.tsx`: subscribes to `/ws/markets/{token_id}` via `useWebSocket`. Dual-column bids (green) / asks (red). Midpoint in center. Click price row → fills OrderForm price.

- [ ] **Step 2: Build OrderForm component**

`components/market/OrderForm.tsx`: BUY/SELL toggle, price input, size input, LIMIT/MARKET select. Shows estimated fee + total. "Connect Wallet to Trade" if no wallet. Submit calls `useTrading().buildAndSubmitOrder()`.

- [ ] **Step 3: Create useTrading hook**

`lib/hooks/useTrading.ts`: `buildAndSubmitOrder(params)` → `POST /orders/build` → `signTypedData` (wagmi) → `POST /orders/submit`. Returns order + loading + error states.

- [ ] **Step 4: Build trade page**

`app/(dashboard)/trade/[id]/page.tsx`: left column (market info + OrderBook + recent trades), right column (OrderForm + AI analysis snippet). Fetches market detail on mount.

- [ ] **Step 5: Add recent trades section**

Fetch `GET /markets/{id}/trades` on mount, display as scrollable list.

- [ ] **Step 6: Verify**

Open trade page → orderbook updates in real-time → fill order form → click Place Order → MetaMask popup → sign → order confirmed → appears in orders list.

---

### Task 5: Portfolio + Orders Pages

**Deliverable:** User can view positions, balance, PnL, and manage orders.

- [ ] **Step 1: Build PositionTable + BalanceCard + PnlChart**

`components/portfolio/`: Table with market, side, size, entry price, current price, unrealized PnL. Balance card: USDC balance, locked, available. PnL chart: recharts line chart.

- [ ] **Step 2: Build portfolio page**

`app/(dashboard)/portfolio/page.tsx`: subscribe to `/ws/portfolio/live` for real-time updates. Display PositionTable + BalanceCard + PnlChart.

- [ ] **Step 3: Build orders page**

`app/(dashboard)/orders/page.tsx`: fetch `GET /orders` with status filter tabs (All, Open, Filled, Cancelled). Cancel button calls `DELETE /orders/{id}`. Cursor pagination.

- [ ] **Step 4: Verify**

Portfolio shows positions + balance + PnL chart → Orders page lists orders → cancel works → status filter works.

---

### Task 6: Data Pages (NBA + Weather + BTC)

**Deliverable:** Three data pages showing fusion/prediction data with bias signals.

- [ ] **Step 1: Build BiasSignalBadge + StaleWarning components**

Shared across all data pages. Badge: direction arrow + bps value + color. StaleWarning: yellow banner when data_updated_at exceeds threshold.

- [ ] **Step 2: Build NBA Fusion page**

`app/(dashboard)/data/nba/page.tsx`: fetch `GET /data/nba/games`. List of NbaFusionCard components. Live games subscribe to `/ws/nba/{game_id}/live`. Show score bar, polymarket prob, statistical prob, bias signal.

- [ ] **Step 3: Build Weather Fusion page**

`app/(dashboard)/data/weather/page.tsx`: date tab selector (fetch `GET /data/weather/dates`). Click date → fetch cities. Click city → show fusion detail with temperature bin chart (recharts bar chart: market_prob vs forecast_prob per bin).

- [ ] **Step 4: Build BTC Predictions page**

`app/(dashboard)/data/btc/page.tsx`: four-panel layout for 5m/15m/1h/4h. Subscribe to `/ws/btc/live`. Show price, prediction probability, volume per timeframe.

- [ ] **Step 5: Verify**

NBA page shows live games with bias → Weather page shows dates/cities/bins → BTC page shows 4 timeframes updating in real-time.

---

### Task 7: Analysis + Strategies Pages

**Deliverable:** AI analysis results and convergence strategy execution.

- [ ] **Step 1: Build analysis page**

`app/(dashboard)/analysis/page.tsx`: two sections. Top: "Scan Markets" button → `POST /analysis/scan` → list of opportunities with bias signals. Bottom: market ID input → `GET /analysis/market/{id}` → AI probability estimate vs market price.

- [ ] **Step 2: Add "Ask" feature**

Input box for natural language query → `POST /analysis/ask` → display response. Show remaining daily quota for free-tier users.

- [ ] **Step 3: Build strategies page**

`app/(dashboard)/strategies/page.tsx`: fetch `GET /strategies/convergence/opportunities`. Table: market, current price, estimated fair value, profit potential. "Execute" button → `POST /strategies/convergence/execute`. Active positions section: `GET /strategies/convergence/positions`.

- [ ] **Step 4: Verify**

Scan returns opportunities → single market analysis works → ask question works → convergence execute triggers wallet sign → position appears.

---

### Task 8: Settings Page + i18n Completion

**Deliverable:** Account management, wallet binding, API key management, full Chinese translation.

- [ ] **Step 1: Build settings page**

`app/(dashboard)/settings/page.tsx`: three tabs. Account (email, tier, created_at). Wallet (bind/unbind, current address). API Keys (list, create, revoke — calls `/auth/keys` endpoints).

- [ ] **Step 2: Complete i18n translations**

Fill `i18n/zh.json` with all UI strings. Ensure every component uses `useTranslations()`. Test language switcher toggles all visible text.

- [ ] **Step 3: Responsive design pass**

Test all pages at mobile (375px), tablet (768px), desktop (1440px). Fix layout breaks. MobileMenu hamburger for narrow screens.

- [ ] **Step 4: Final integration verification**

Full user journey: register → login → browse markets → open trade → connect wallet → place order → check portfolio → view NBA/Weather data → run AI scan → execute strategy → manage API keys → switch language to Chinese → verify all text switched.

---

## Summary

| Metric | Value |
|--------|-------|
| Total pages | 14 (3 auth + 11 dashboard) |
| Components | ~30 custom + shadcn/ui base |
| API endpoints consumed | 43 REST + 4 WebSocket |
| Languages | English + Chinese |
| Estimated files | ~60-80 |
