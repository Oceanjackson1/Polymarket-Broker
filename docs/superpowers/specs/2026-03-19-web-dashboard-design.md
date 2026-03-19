# Polymarket Broker Web Dashboard — Design Spec

**Date**: 2026-03-19
**Status**: Approved
**Author**: Ocean Jackson
**Parent Spec**: `2026-03-17-polymarket-broker-design.md`

---

## 1. Overview

A **Next.js Web Dashboard** for the Polymarket Broker platform, enabling external traders to browse markets, place orders (non-custodial wallet signing), manage portfolios, and access enhanced data (NBA Fusion, Weather Fusion, BTC predictions) and AI analysis — all through the same REST + WebSocket API that third-party developers use.

**Revenue driver**: Traders execute orders through the Dashboard → transaction fees (Broker fee layered on top of Polymarket's native fees).

---

## 2. Target Users

**Phase 1 (this spec)**: External traders — browse, trade, monitor positions, consume enhanced data and AI signals.

**Phase 2 (future)**: Third-party developers — API key management, usage stats, billing, documentation.

---

## 3. Tech Stack

| Layer | Technology | Rationale |
|---|---|---|
| Framework | Next.js 15 (App Router) | SSR + CSR, Vercel-native |
| Styling | Tailwind CSS 4 + shadcn/ui | Rapid UI development, consistent design system |
| Wallet | wagmi 2 + viem 2 + RainbowKit 2 | React hooks for Ethereum, Polygon support |
| Data Fetching | @tanstack/react-query 5 | Caching, retry, optimistic updates |
| Charts | recharts 2 | Declarative React charting |
| i18n | next-intl 4 | SSR-compatible, cookie-based language switching |
| Icons | lucide-react | Consistent icon set |
| Deploy | Vercel | Existing infrastructure decision from parent spec |

---

## 4. Authentication

### Two Entry Paths

**Path A — Email Registration**
```
Register (email + password) → JWT access token (15min) + refresh token (30d)
→ Can browse markets, data, analysis
→ Cannot trade (no wallet)
→ Bind wallet via Settings → unlocks trading
```

**Path B — Wallet Connect**
```
Connect wallet (MetaMask / WalletConnect / Coinbase Wallet)
→ Challenge-response (EIP-191 nonce signing)
→ JWT access token + refresh token
→ Full access including trading
```

### Auth State

| State | Capabilities |
|---|---|
| Not logged in | Public market list (SSR), login/register pages |
| Email only (no wallet) | Browse markets, view data/analysis, manage settings |
| Wallet connected | All above + place orders, execute strategies |

### Token Storage
- Access token: memory (React state) + httpOnly cookie (SSR)
- Refresh token: httpOnly cookie
- Wallet state: wagmi persistent connector

---

## 5. Trading Flow (Non-Custodial Only)

```
User fills order form (market_id, side, price, size)
    → POST /api/v1/orders/build
    → Returns { eip712_payload, payload_hash }
    → MetaMask popup: eth_signTypedData_v4
    → User confirms signature
    → POST /api/v1/orders/submit { payload_hash, signature }
    → Returns Order object
    → UI updates: order appears in Orders tab
```

Chain: Polygon (chain ID 137). All order signing happens client-side via wagmi/viem.

---

## 6. Pages & Routes

```
/                                    → Redirect to /markets
/(auth)/login                        → Email login
/(auth)/register                     → Email registration
/(auth)/wallet                       → Wallet Connect login

/(dashboard)/markets                 → Market browsing (SSR, SEO)
/(dashboard)/trade/[id]              → Market detail + orderbook + order form
/(dashboard)/portfolio               → Positions + balance + PnL
/(dashboard)/orders                  → Order history + cancel
/(dashboard)/data/nba                → NBA Fusion (live games + bias)
/(dashboard)/data/weather            → Weather Fusion (date → city → bias)
/(dashboard)/data/btc                → BTC multi-timeframe predictions
/(dashboard)/analysis                → AI scan + single market analysis
/(dashboard)/strategies              → Convergence opportunities + execute
/(dashboard)/settings                → Account + wallet binding + API keys
```

### Rendering Strategy

| Page | Rendering | Reason |
|---|---|---|
| `/markets` | SSR | SEO + fast first paint |
| `/trade/[id]` | CSR | WebSocket real-time data |
| `/portfolio` | CSR | User-private + WebSocket |
| `/orders` | CSR | User-private data |
| `/data/*` | SSR + CSR hydration | Lists SSR, real-time parts CSR |
| `/analysis` | CSR | User-triggered API calls |
| `/strategies` | CSR | Trading operations |
| `/settings` | CSR | User-private data |

---

## 7. Layout

### Root Layout
```
ThemeProvider (dark mode)
  └── I18nProvider (en/zh, cookie-based)
       └── AuthProvider (JWT + wallet state)
            └── QueryClientProvider (react-query)
                 └── WagmiProvider + RainbowKitProvider
```

### Dashboard Layout
```
┌─────────────────────────────────────────────────┐
│ Logo | Markets | Portfolio | Data ▾ | Analysis  │
│      | Strategies | Settings    [Wallet] [Lang] │
├─────────────────────────────────────────────────┤
│                                                 │
│                  {children}                     │
│                                                 │
└─────────────────────────────────────────────────┘
```

Data dropdown: NBA | Weather | BTC

---

## 8. Real-Time Data (WebSocket)

All real-time data delivered via WebSocket, direct connection to backend (not through Vercel).

| Endpoint | Page | Frequency |
|---|---|---|
| `/ws/markets/{token_id}` | `/trade/[id]` | 3s (orderbook + midpoint) |
| `/ws/nba/{game_id}/live` | `/data/nba` | 5s (score + odds + bias) |
| `/ws/btc/live` | `/data/btc` | 5s (all timeframes) |
| `/ws/portfolio/live` | `/portfolio` | 10s (positions update) |

### WebSocket Hook
```typescript
useWebSocket<T>(url, { enabled, onMessage, reconnectInterval })
→ { data, status, send }
```

Auto-reconnect with exponential backoff (3s → 6s → 12s → 30s max).

---

## 9. Internationalization

| Aspect | Approach |
|---|---|
| Library | next-intl |
| Languages | English (default), Chinese (Simplified) |
| Storage | Cookie (`locale=en` / `locale=zh`) |
| Scope | All UI text, labels, error messages, tooltips |
| Not scoped | Market questions (from Polymarket, English only) |

---

## 10. Component Architecture

### Shared Components
```
components/
├── layout/         TopNav, DashboardShell, MobileMenu
├── market/         MarketCard, MarketSearch, OrderBook, OrderForm, PriceChart
├── data/           BiasSignalBadge, NbaFusionCard, WeatherFusionCard, BtcPredictionCard, StaleWarning
├── portfolio/      PositionTable, BalanceCard, PnlChart
├── auth/           LoginForm, RegisterForm, WalletButton, BindWalletModal
└── ui/             shadcn/ui base components
```

### Key Component Behaviors

**OrderBook**: subscribes to `/ws/markets/{token_id}`, dual-column bids/asks, click price → fills OrderForm.

**OrderForm**: BUY/SELL toggle, LIMIT/MARKET type, calls `buildOrder` → wallet sign → `submitOrder`. Shows "Connect Wallet to Trade" when no wallet bound.

**BiasSignalBadge**: reused across NBA/Weather/Analysis. FORECAST_HIGHER → green ▲, MARKET_HIGHER → red ▼, NEUTRAL → gray —.

---

## 11. Non-Functional Requirements

| Requirement | Target |
|---|---|
| Concurrent users | 100–500 (Phase 1) |
| First contentful paint | < 2s (Vercel CDN + SSR) |
| WebSocket connections | 1–2 per user |
| SEO | Market list pages indexed |
| Mobile | Responsive design (no native app) |
| Browser support | Chrome, Safari, Firefox, Edge (latest 2 versions) |
| Accessibility | Basic ARIA labels, keyboard navigation for trading forms |
| Dark mode | Default and only theme (Phase 1) |

---

## 12. Repository Structure

```
consumers/web/
├── app/
│   ├── layout.tsx                 # Root: theme + i18n + auth + query + wagmi
│   ├── page.tsx                   # Redirect to /markets
│   ├── (auth)/
│   │   ├── layout.tsx             # Centered card, no nav
│   │   ├── login/page.tsx
│   │   ├── register/page.tsx
│   │   └── wallet/page.tsx
│   └── (dashboard)/
│       ├── layout.tsx             # TopNav + main content area
│       ├── markets/page.tsx       # SSR market list
│       ├── trade/[id]/page.tsx    # Market detail + trading
│       ├── portfolio/page.tsx
│       ├── orders/page.tsx
│       ├── data/
│       │   ├── nba/page.tsx
│       │   ├── weather/page.tsx
│       │   └── btc/page.tsx
│       ├── analysis/page.tsx
│       ├── strategies/page.tsx
│       └── settings/page.tsx
├── components/
│   ├── layout/
│   ├── market/
│   ├── data/
│   ├── portfolio/
│   ├── auth/
│   └── ui/
├── lib/
│   ├── api-client.ts              # REST API wrapper
│   ├── hooks/
│   │   ├── useWebSocket.ts
│   │   ├── useAuth.ts
│   │   ├── useWallet.ts
│   │   └── useTrading.ts
│   ├── wagmi-config.ts            # Chain config (Polygon)
│   └── utils.ts
├── i18n/
│   ├── en.json
│   └── zh.json
├── public/
│   └── favicon.ico
├── next.config.ts
├── tailwind.config.ts
├── tsconfig.json
├── package.json
└── .env.local.example
```

---

## 13. Environment Variables

```bash
# API
NEXT_PUBLIC_API_BASE=http://localhost:8000/api/v1
NEXT_PUBLIC_WS_BASE=ws://localhost:8000

# Wallet
NEXT_PUBLIC_WALLET_CONNECT_PROJECT_ID=...
NEXT_PUBLIC_CHAIN_ID=137

# i18n
NEXT_PUBLIC_DEFAULT_LOCALE=en
```

---

## 14. Decision Log

| # | Decision | Alternatives | Rationale |
|---|----------|-------------|-----------|
| 1 | Phase 1 traders only | Devs first / both | Traders = revenue |
| 2 | All 11 pages in Phase 1 | Partial delivery | Backend 100% ready |
| 3 | Email + Wallet dual auth | Single auth | Low-barrier + trading |
| 4 | Non-custodial only | Custodial / both | Security-first |
| 5 | Next.js App Router + shadcn | Pages Router / custom | Mainstream, fast dev |
| 6 | Full WebSocket | Polling / hybrid | Trading needs real-time |
| 7 | Dark Dashboard style | Exchange / card style | Data-dense, Bloomberg-lite |
| 8 | Chinese + English | English only | Spec requires Chinese-friendly |
| 9 | Single Next.js app | Micro-frontend / monorepo | YAGNI for Phase 1 |
| 10 | wagmi + RainbowKit | ethers.js / web3.js | Modern React-native wallet UX |
| 11 | react-query | SWR / manual fetch | Mature caching + retry |
| 12 | recharts | D3 / Chart.js | Simple, declarative, React |
