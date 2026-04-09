# croo_agent — Croo Marketplace Provider for Polymarket Broker

This module registers the Polymarket Broker `tg_agent` capability layer as paid
services on the [Croo](https://croo.network) decentralized agent marketplace, using
the [`python-sdk-dev`](https://github.com/RayCroo/python-sdk-dev) SDK.

It is a separate process from `tg_agent` (which keeps running for Telegram users).
Both processes can run side-by-side and share the same database / Redis pool.

---

## Services exposed (39 fine-grained services)

The Polymarket Broker provider exposes its capabilities as **39 separate Croo
marketplace services**, each priced at **0.0001 USDC** (100 base units) for
dev. Each service is self-contained — the buyer doesn't need to know about
internal `capability` / `feed` / `action` concepts; they just pick a service
and (optionally) supply the required field for that specific service.

The full catalogue lives in [`croo_agent/services.py`](services.py) under
`SPECS`. A quick overview:

| Group | Slugs | Examples |
|---|---|---|
| **Market** (2) | `market_search`, `market_detail` | Search Polymarket; fetch full market by id |
| **Strategy** (2) | `strategy_list`, `strategy_scan_convergence` | List strategies; convergence-arbitrage scanner |
| **Analysis** (2) | `analysis_ask`, `analysis_scan` | DeepSeek Q&A; AI mispricing scanner |
| **NBA** (3) | `nba_list`, `nba_detail`, `nba_fusion` | Today's games; per-game detail; Polymarket fusion |
| **BTC** (3) | `btc_list`, `btc_detail`, `btc_fusion` | Latest snapshots; history; derivatives fusion |
| **Crypto Derivatives** (5) | `crypto_overview`, `crypto_funding`, `crypto_oi`, `crypto_liquidations`, `crypto_sentiment` | Per-symbol breakdowns + fear & greed |
| **Weather** (3) | `weather_dates`, `weather_cities`, `weather_fusion` | Available dates; cities by date; bias fusion |
| **Sports** (2) | `sports_categories`, `sports_events` | Active categories; events list |
| **Sports Odds** (4) | `sports_odds_sports`, `sports_odds_bookmaker`, `sports_odds_scores`, `sports_odds_opportunities` | Bookmaker odds vs Polymarket |
| **Dome Markets** (2) | `dome_markets_list`, `dome_markets_candles` | Market snapshots + candles |
| **Dome Arbitrage** (2) | `dome_arb_spreads`, `dome_arb_opportunities` | Polymarket–Kalshi spreads |
| **Dome Wallets** (2) | `dome_wallet_positions`, `dome_wallet_pnl` | Position snapshots + PnL history |
| **Dome Crypto** (1) | `dome_crypto_price` | Live BTC/ETH prices via Dome |
| **Dome Events** (2) | `dome_events_list`, `dome_events_activity` | Latest events + activity stream |
| **Kalshi** (4) | `kalshi_markets`, `kalshi_price`, `kalshi_trades`, `kalshi_orderbook` | Markets search + per-ticker data |

User-scoped capabilities (`place_order`, `cancel_order`, `portfolio`) and
write actions (`strategy.execute`, `strategy.positions`) are **not** exposed
because they bind to or mutate a real Polymarket Broker user account.

### How buyer requirements work

Each service has a fixed **`preset_params`** dict (e.g. `{"feed": "nba",
"action": "detail"}`) that the dispatcher injects automatically — buyers never
see it and **cannot override it**. Buyers only supply the small set of fields
the service truly needs, defined per spec as `extra_required` /
`extra_optional`.

For example:

| Service slug | Buyer sends | Provider runs |
|---|---|---|
| `nba_list` | `{}` (nothing) | `data_feed.invoke(feed=nba, action=list)` |
| `nba_detail` | `{"game_id": "0021400001"}` | `data_feed.invoke(feed=nba, action=detail, game_id=...)` |
| `analysis_ask` | `{"question": "..."}` | `analysis.invoke(action=ask, question=...)` |
| `kalshi_price` | `{"ticker": "PRES2024"}` | `data_feed.invoke(feed=kalshi, action=price, ticker=...)` |

If a buyer attempts to override a preset routing field (e.g. send
`{"feed": "btc"}` to `nba_list`), the dispatcher rejects the negotiation
immediately with `buyer cannot override preset routing fields`.

---

## Prerequisites

1. **Feilian VPN** — `dev-api.croo.network` is on the internal network.
2. **Python venv** with the project dependencies installed:
   ```bash
   .venv/bin/python -m pip install -r requirements.txt
   ```
3. **`.env`** with the dev-only Croo settings (in addition to the existing
   Polymarket Broker config):
   ```ini
   CROO_API_BASE=https://dev-api.croo.network
   CROO_WS_URL=wss://dev-api.croo.network/ws
   CROO_RPC_URL=<dev-chain JSON-RPC URL — ask the Croo team>
   CROO_PAYMENT_TOKEN=<dev USDC token address — ask the Croo team>
   # Set after Phase A of setup_cli below:
   # CROO_WALLET_PRIVATE_KEY=0x...
   ```

---

## One-time setup

### Phase A — generate the controller wallet

```bash
.venv/bin/python -m croo_agent.setup_cli
```

The script will:
1. Detect that no `CROO_WALLET_PRIVATE_KEY` is set
2. Generate a fresh EOA (`eth_account.Account.create()`)
3. Print the address + private key (**this is the only time you will see the key**)
4. Print the exact `.env` line to add
5. Exit non-zero

Copy the private key into `.env`. Then **fund the printed address** on the Croo
dev chain with native gas (for the AA wallet deployment + accept_negotiation
transactions). USDC is only required if this same wallet is also acting as a
*consumer* — providers receive USDC, they don't pay it.

### Phase B — register the agent + services

Re-run the same command:

```bash
.venv/bin/python -m croo_agent.setup_cli
```

This time it:
1. Constructs `UserClient(Config(dev URLs), PrivateKeySigner(<key>))`
2. Calls `setup_agent()` for the **first** service — this also deploys the agent's
   AA wallet and returns the SDK-Key
3. Calls `create_service()` for each remaining service
4. Writes `croo_agent/.credentials.json` (chmod 600, gitignored) with:
   ```json
   {
     "version": 1,
     "agent_id": "agent_xxx",
     "sdk_key": "croo_sk_xxx",
     "wallet_address": "0x...",
     "services": {
       "<service_id_1>": "market_query",
       "<service_id_2>": "data_feed",
       "<service_id_3>": "strategy",
       "<service_id_4>": "analysis"
     },
     "environment": "dev",
     "generated_at": "2026-04-07T..."
   }
   ```

If `.credentials.json` already exists, you'll be prompted to confirm the
overwrite. Use `--force` to skip the prompt.

---

## Runtime

```bash
.venv/bin/python -m croo_agent
```

On startup the runtime will:
1. **Feilian connectivity check** against `CROO_API_BASE` (5s timeout)
2. Load credentials from `croo_agent/.credentials.json` (or env vars)
3. Initialise shared infra: PostgreSQL, Redis, Gamma client, Dome client
4. Build a `tg_agent` orchestrator (the Croo path bypasses the LLM intent parser)
5. Construct `AgentClient(Config(dev URLs), sdk_key)`
6. Connect the WebSocket and register listeners on
   `NEGOTIATION_CREATED`, `ORDER_PAID`, plus log-only listeners on
   `ORDER_COMPLETED` / `ORDER_REJECTED` / `ORDER_EXPIRED`

You should see something like:

```
Provider live: agent_id=agent_xxx, wallet=0x..., services=[analysis, data_feed, market_query, strategy]
```

Send `Ctrl-C` (or `SIGTERM`) for graceful shutdown — in-flight handlers get up to
30 seconds to finish before resources are torn down.

### Useful flags

- `--check` — only run the Feilian connectivity check, then exit. Useful for CI.
- `--dry-run` — connect, listen, and run handlers normally, but **never** call
  `deliver_order`. The envelope that *would* have been delivered is logged
  instead. Useful for rehearsals against real dev orders.

---

## How an order flows through the dispatcher

```
Buyer agent                              Provider (this process)
─────────────                            ────────────────────────
negotiate_order ────► NEGOTIATION_CREATED
                      ├─ validate requirement against ServiceSpec schema
                      │  • on validation failure → reject_negotiation(reason)
                      ├─ accept_negotiation()  → returns Order
                      └─ cache (order_id, requirement) for ORDER_PAID
pay_order ──────────► ORDER_PAID
                      ├─ pop cached requirement
                      ├─ orchestrator.invoke(capability, params, system_user_id, ctx)
                      │  └─ tg_agent handler runs against shared DB / Redis / Gamma / Dome
                      ├─ wrap result in standardised envelope (build_envelope)
                      └─ deliver_order(order_id, DeliverOrderRequest(TEXT, json))
get_delivery   ◄──── ORDER_COMPLETED
```

### Failure semantics

| When | Action |
|------|--------|
| Validation fails *before* accept (bad service_id, schema, disallowed action) | `reject_negotiation(reason)` — buyer pays nothing |
| Handler raises *after* payment | `deliver_order` with `status="error"` envelope |
| Handler times out | `deliver_order` with `error.code="HANDLER_TIMEOUT"` |
| Handler returns `success=False` | `deliver_order` with `status="error"` and the partial result echoed |

### Envelope shape

Every deliverable is the same JSON shape (see `croo_agent/deliverables.py`):

```json
{
  "envelope_version": "1",
  "service": "analysis",
  "order_id": "ord_xxx",
  "status": "ok",
  "generated_at": "2026-04-07T12:34:56+00:00",
  "request": { "action": "ask", "question": "..." },
  "result": { "answer": "..." }
}
```

Hard size cap: 64 KiB. Larger payloads are truncated with `truncated: true`.

---

## Synthetic user_id

The Croo path runs every handler with `user_id=settings.croo_system_user_id`
(default `"croo:provider"`). The four exposed handlers were audited and either
ignore `user_id` (`market_query`, `data_feed`, `strategy.{list,scan}`) or use it
purely for the Redis daily-quota counter (`analysis`).

If the analysis daily quota becomes a bottleneck, either:
- Insert a `User` row with `tier="pro"` for the synthetic id (bypasses the free
  10/day limit), or
- Add a dedicated `croo_analysis_daily_quota` setting and switch the handler to
  use a separate Redis key (requires a small change in `api/analysis/service.py`).

---

## Troubleshooting

**`Feilian check FAILED for https://dev-api.croo.network`**
→ Connect Feilian VPN. Re-run with `--check` to confirm.

**`Cannot start Croo provider: Credentials file not found`**
→ Run `python -m croo_agent.setup_cli`.

**`No credentials at … and CROO_SDK_KEY/CROO_AGENT_ID not set in env`**
→ Either restore `croo_agent/.credentials.json` from backup, or set
`CROO_SDK_KEY` + `CROO_AGENT_ID` in `.env` and *manually* recover the
`service_id → capability` map (the dispatcher won't start with an empty `services`
map — easier to just re-run `setup_cli` and re-register on a new agent).

**`unknown service_id <id> for negotiation <id>; rejecting`**
→ The buyer paid for a `service_id` that isn't in `.credentials.json`. Likely
caused by re-running setup against the same agent without cleaning up the JSON
file. Run `setup_cli --force` to refresh.

**`HANDLER_TIMEOUT`**
→ Increase the relevant timeout in `.env`:
```
CROO_HANDLER_TIMEOUT_DEFAULT_S=60
CROO_HANDLER_TIMEOUT_ANALYSIS_S=120
CROO_HANDLER_TIMEOUT_STRATEGY_S=120
```

**`ANALYSIS_QUOTA_EXCEEDED`**
→ The synthetic user_id has hit the free daily quota. See the "Synthetic user_id"
section above for the two workarounds.

---

## Rebuilding the service catalogue

If you change `services.py:SPECS` (add a slug, change a description, retire a
service…) and want to refresh the dev catalogue **without** redeploying the
agent on-chain, run:

```bash
.venv/bin/python -m croo_agent.setup_cli --rebuild [--force]
```

This keeps the same `agent_id`, `SDK-Key`, and AA wallet. It:

1. Calls `list_services(agent_id)` to enumerate the existing catalogue
2. `update_service(sid, status=INACTIVE)` for every active service
3. `create_service(agent_id, spec)` for each entry in `SPECS` (then explicitly
   activates it)
4. Writes the new `service_id → slug` map back to `.credentials.json`

After rebuild, **restart the provider** so it picks up the new map:

```bash
# Stop the running provider (Ctrl-C or SIGTERM), then:
.venv/bin/python -m croo_agent
```

Use `--force` to skip the overwrite confirmation prompt.

---

## End-to-end smoke test (`buyer_smoke.py`)

`croo_agent/buyer_smoke.py` is a self-contained buyer-side validator that exercises
the full negotiation chain against the local provider. It uses the **same controller
wallet** as the provider (Croo dev rejects self-trade between identical agents, but
allows different agents under the same controller) and creates a lightweight buyer
agent — `create_agent` + `deploy_agent` + `list_sdk_keys`, no `create_service`.

```bash
# Terminal 1 — provider
.venv/bin/python -m croo_agent

# Terminal 2 — list all available service slugs (no network needed)
.venv/bin/python -m croo_agent.buyer_smoke --list-services

# Terminal 2 — buy an nba_list service (no buyer fields needed)
.venv/bin/python -m croo_agent.buyer_smoke --service nba_list

# Buy nba_detail with a specific game_id
.venv/bin/python -m croo_agent.buyer_smoke --service nba_detail \
  --requirements '{"game_id":"0021400001"}'

# Buy analysis_ask with a custom question
.venv/bin/python -m croo_agent.buyer_smoke --service analysis_ask \
  --requirements '{"question":"BTC sentiment today?"}'
```

Flags:

- `--service <slug>` — slug of the service to buy (required, see `--list-services`)
- `--list-services` — print every slug + whether it's in the catalogue and the provider creds, then exit
- `--requirements '<json>'` — override the buyer requirements payload (defaults to the spec's `example_requirement()`)
- `--reset` — delete cached buyer credentials and create a fresh buyer agent
- `--pay` — attempt `pay_order` after acceptance (will fail without dev USDC; that's expected — this just exercises the off-chain signaling)
- `--wait-seconds N` — how long to poll for state transitions (default 60)

The cached buyer credentials live in `croo_agent/.buyer_credentials.json` (gitignored).

### Expected non-payment flow

Without USDC on the buyer wallet, the chain plays out like this:

```
buyer.negotiate_order ───────► negotiation: pending
                                    │ (provider WebSocket recv NEGOTIATION_CREATED)
                                    │ (dispatcher validates requirement, accepts)
                          ──────► negotiation: accepted   ← within ~2-4s
                          ──────► order: creating
                                    │ (on-chain confirmation, ~30s)
                          ──────► order: created          ← terminal in non-payment mode
```

To get past `created`, the buyer wallet needs USDC on the dev chain to call
`pay_order` — that's the only segment of the flow that depends on real on-chain
funds. Provider integration itself is fully validated by reaching `created`.

---

## Coexistence with `tg_agent`

`croo_agent` and `tg_agent` are two independent `python -m …` processes that share
the same PostgreSQL connection pool, Redis pool, and HTTP clients (each builds its
own instances). Run them in parallel — there is no port conflict because
`croo_agent` does not expose an HTTP listener.

```bash
# Terminal 1
.venv/bin/python -m tg_agent
# Terminal 2 (Feilian VPN must be on)
.venv/bin/python -m croo_agent
```
