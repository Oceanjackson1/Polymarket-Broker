export const dynamic = "force-static";

export async function GET() {
  const content = `# Polymarket Broker

> Institutional-grade prediction market trading platform. Provides real-time
> NBA score × Polymarket odds fusion data, 145-sport historical orderbooks,
> BTC multi-timeframe on-chain prediction data, and AI pricing-bias analysis
> — data unavailable via Polymarket directly.

## Core Resources

- [Markets Overview](/markets): Browse all prediction markets with real-time odds across politics, sports, crypto, and more
- [API Documentation](/docs): Complete REST API reference for developers building on Polymarket Broker
- [API Quick Start](/docs/getting-started/quickstart): 5-minute integration guide
- [Authentication Guide](/docs/getting-started/authentication): API Key and Wallet auth setup
- [Pricing](/pricing): Subscription tiers — Free, Pro ($99/mo), Enterprise

## Exclusive Data (Not Available on Polymarket)

- [NBA Fusion Data Guide](/docs/guides/nba-fusion-trading): Real-time ESPN scores × Polymarket odds with bias signals
- [BTC Multi-Timeframe Predictions](/docs/guides/btc-multiframe): 5m/15m/1h/4h Bitcoin prediction markets
- [Sports Historical Orderbooks](/docs/guides/sports-orderbooks): 145 sport/esport categories with full historical order books
- [AI Analysis Endpoints](/docs/api-reference/analysis): Machine learning pricing-bias detection

## API Reference

- [Auth Endpoints](/docs/api-reference/auth): Registration, login, API keys, wallet auth
- [Markets Endpoints](/docs/api-reference/markets): List, search, orderbook, trades, midpoint
- [Orders Endpoints](/docs/api-reference/orders): Place, cancel, build (non-custodial), submit
- [Portfolio Endpoints](/docs/api-reference/portfolio): Positions, balance, PnL
- [Data — Sports](/docs/api-reference/data-sports): 145-sport event data and orderbooks
- [Data — NBA](/docs/api-reference/data-nba): Live games, fusion view, bias signals
- [Data — BTC](/docs/api-reference/data-btc): Multi-timeframe predictions, on-chain trades
- [Strategies](/docs/api-reference/strategies): Convergence arbitrage execution

## Optional

- [Blog](/blog): Market analysis, data reports, trading strategies
- [About](/about): Company information
- [Changelog](/docs/changelog): API updates and release notes
`;

  return new Response(content, {
    headers: {
      "Content-Type": "text/plain; charset=utf-8",
      "Cache-Control": "public, max-age=86400",
    },
  });
}
