import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = {
  title: "Polymarket Broker — Institutional Prediction Market Terminal",
  description:
    "Trade prediction markets with institutional-grade tools. Real-time NBA fusion data, 145-sport orderbooks, BTC multi-timeframe predictions, and AI pricing-bias analysis. Free to start, Pro at $99/mo.",
  openGraph: {
    title: "Polymarket Broker — Institutional Prediction Market Terminal",
    description:
      "The only broker providing NBA×Polymarket real-time fusion data, AI pricing-bias analysis, and convergence arbitrage execution.",
  },
};

const jsonLd = {
  "@context": "https://schema.org",
  "@type": "WebApplication",
  name: "Polymarket Broker",
  applicationCategory: "FinanceApplication",
  operatingSystem: "Web",
  description:
    "Institutional-grade prediction market trading platform with exclusive data feeds and AI analysis.",
  offers: [
    {
      "@type": "Offer",
      name: "Free",
      price: "0",
      priceCurrency: "USD",
      description: "500 API calls/day, 10 AI analyses/day",
    },
    {
      "@type": "Offer",
      name: "Pro",
      price: "99",
      priceCurrency: "USD",
      billingIncrement: "P1M",
      description:
        "Unlimited API calls, unlimited AI analysis, strategies, webhooks",
    },
  ],
};

const exclusiveFeatures = [
  {
    title: "NBA 实时融合数据",
    description:
      "ESPN 比分 × Polymarket 赔率 × AI 偏差信号。发现市场定价错误，毫秒级更新。",
    badge: "独家",
    href: "/docs/guides/nba-fusion-trading",
  },
  {
    title: "145 项体育历史订单簿",
    description:
      "覆盖 NBA、NFL、UFC、CS2 等 145 个运动/电竞品类的完整历史订单簿数据。",
    badge: "独家",
    href: "/docs/guides/sports-orderbooks",
  },
  {
    title: "BTC 多时间框架预测",
    description:
      "5 分钟到 4 小时，四个时间框架的 BTC 预测市场概率 + 链上交易数据。",
    badge: "独家",
    href: "/docs/guides/btc-multiframe",
  },
  {
    title: "AI 定价偏差分析",
    description:
      "DeepSeek 驱动的市场扫描，自动发现全市场 top 定价偏差机会。一键交易。",
    badge: "AI",
    href: "/docs/api-reference/analysis",
  },
];

export default function LandingPage() {
  return (
    <>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
      />

      {/* Hero */}
      <section className="bg-bg-base">
        <div className="mx-auto max-w-7xl px-6 py-24 text-center md:py-32">
          <div className="mb-6 inline-flex items-center gap-2 rounded-full border border-accent-gold-bg bg-accent-gold-bg/20 px-4 py-1.5 text-sm text-accent-gold">
            <span>机构级预测市场终端</span>
          </div>
          <h1 className="mx-auto max-w-4xl text-4xl font-bold tracking-tight text-text-primary md:text-6xl">
            用华尔街的工具
            <br />
            <span className="text-accent-gold">交易预测市场</span>
          </h1>
          <p className="mx-auto mt-6 max-w-2xl text-lg text-text-secondary">
            Polymarket 本身不提供的独家数据 —— NBA 实时融合、145
            项体育订单簿、BTC 多时间框架预测、AI
            定价偏差分析。所有数据通过统一 REST API 交付。
          </p>
          <div className="mt-10 flex items-center justify-center gap-4">
            <Link
              href="/dashboard"
              className="rounded-lg bg-accent-gold px-8 py-3 text-base font-semibold text-bg-base transition-colors hover:bg-accent-gold-hover"
            >
              免费开始
            </Link>
            <Link
              href="/docs"
              className="rounded-lg border border-border-default px-8 py-3 text-base font-semibold text-text-primary transition-colors hover:bg-bg-elevated"
            >
              查看 API 文档
            </Link>
          </div>
          <p className="mt-4 text-sm text-text-muted">
            Free 套餐: 500 次 API 调用/天 · 无需信用卡
          </p>
        </div>
      </section>

      {/* Exclusive Features */}
      <section className="border-t border-border-subtle bg-bg-card">
        <div className="mx-auto max-w-7xl px-6 py-24">
          <div className="mb-16 text-center">
            <h2 className="text-3xl font-bold text-text-primary">
              竞品无法提供的数据
            </h2>
            <p className="mt-4 text-text-secondary">
              这些数据是你付费升级 Pro 的核心理由
            </p>
          </div>
          <div className="grid gap-6 md:grid-cols-2">
            {exclusiveFeatures.map((feature) => (
              <Link
                key={feature.title}
                href={feature.href}
                className="group rounded-xl border border-border-subtle bg-bg-base p-8 transition-colors hover:border-accent-gold/30"
              >
                <div className="mb-4 flex items-center gap-3">
                  <span className="rounded bg-accent-gold-bg px-2 py-0.5 text-xs font-semibold text-accent-gold">
                    {feature.badge}
                  </span>
                  <h3 className="text-lg font-semibold text-text-primary group-hover:text-accent-gold">
                    {feature.title}
                  </h3>
                </div>
                <p className="text-sm leading-relaxed text-text-secondary">
                  {feature.description}
                </p>
              </Link>
            ))}
          </div>
        </div>
      </section>

      {/* API-first */}
      <section className="border-t border-border-subtle bg-bg-base">
        <div className="mx-auto max-w-7xl px-6 py-24">
          <div className="grid items-center gap-16 md:grid-cols-2">
            <div>
              <h2 className="text-3xl font-bold text-text-primary">
                API 优先设计
              </h2>
              <p className="mt-4 text-text-secondary">
                自有 Web 终端和第三方开发者调用完全相同的 API。我们自己吃自己的
                API。
              </p>
              <ul className="mt-8 space-y-4">
                {[
                  "RESTful API + WebSocket 实时流",
                  "API Key + 以太坊钱包双认证路径",
                  "托管模式和非托管模式订单",
                  "完整的 OpenAPI 规范文档",
                ].map((item) => (
                  <li
                    key={item}
                    className="flex items-center gap-3 text-sm text-text-secondary"
                  >
                    <span className="text-accent-gold">✓</span>
                    {item}
                  </li>
                ))}
              </ul>
              <div className="mt-8">
                <Link
                  href="/docs/getting-started/quickstart"
                  className="text-sm font-medium text-accent-gold hover:text-accent-gold-hover"
                >
                  5 分钟快速接入 →
                </Link>
              </div>
            </div>
            <div className="rounded-xl border border-border-subtle bg-bg-card p-6">
              <pre className="overflow-x-auto text-sm leading-relaxed">
                <code className="font-mono text-text-secondary">
                  <span className="text-text-muted"># 获取 NBA 融合数据</span>
                  {"\n"}
                  <span className="text-info-cyan">curl</span>
                  {" -H "}
                  <span className="text-accent-gold">
                    &quot;X-API-Key: pm_live_sk_xxx&quot;
                  </span>
                  {" \\\n  "}
                  <span className="text-text-primary">
                    /api/v1/data/nba/games/gsw-lal/fusion
                  </span>
                  {"\n\n"}
                  <span className="text-text-muted"># Response</span>
                  {"\n"}
                  <span className="text-text-secondary">{`{
  "score": { "home": 94, "away": 87 },
  "polymarket": { "home_win_prob": 0.31 },
  "bias_signal": {
    "direction": "HOME_UNDERPRICED",
    "magnitude_bps": 420
  }
}`}</span>
                </code>
              </pre>
            </div>
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="border-t border-border-subtle bg-bg-card">
        <div className="mx-auto max-w-7xl px-6 py-24 text-center">
          <h2 className="text-3xl font-bold text-text-primary">
            开始使用 Polymarket Broker
          </h2>
          <p className="mt-4 text-text-secondary">
            Free 套餐永久免费 · Pro $99/月解锁全部独家数据和策略
          </p>
          <div className="mt-8 flex items-center justify-center gap-4">
            <Link
              href="/dashboard"
              className="rounded-lg bg-accent-gold px-8 py-3 text-base font-semibold text-bg-base transition-colors hover:bg-accent-gold-hover"
            >
              免费注册
            </Link>
            <Link
              href="/pricing"
              className="text-sm font-medium text-text-secondary hover:text-text-primary"
            >
              查看定价方案 →
            </Link>
          </div>
        </div>
      </section>
    </>
  );
}
