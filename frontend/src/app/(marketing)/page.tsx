import type { Metadata } from "next";
import Link from "next/link";
import { HeroSection, ExclusiveFeaturesGrid } from "./_components/hero-section";

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
    isAI: false,
  },
  {
    title: "145 项体育历史订单簿",
    description:
      "覆盖 NBA、NFL、UFC、CS2 等 145 个运动/电竞品类的完整历史订单簿数据。",
    badge: "独家",
    href: "/docs/guides/sports-orderbooks",
    isAI: false,
  },
  {
    title: "BTC 多时间框架预测",
    description:
      "5 分钟到 4 小时，四个时间框架的 BTC 预测市场概率 + 链上交易数据。",
    badge: "独家",
    href: "/docs/guides/btc-multiframe",
    isAI: false,
  },
  {
    title: "AI 定价偏差分析",
    description:
      "DeepSeek 驱动的市场扫描，自动发现全市场 top 定价偏差机会。一键交易。",
    badge: "AI",
    href: "/docs/api-reference/analysis",
    isAI: true,
  },
];

export default function LandingPage() {
  return (
    <>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
      />

      {/* Hero — client component for animations + BackgroundOrbs */}
      <HeroSection />

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
          <ExclusiveFeaturesGrid features={exclusiveFeatures} />
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
            <div className="animate-fade-in rounded-xl border border-border-subtle bg-bg-card p-6">
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
              className="btn-premium rounded-lg bg-accent-gold px-8 py-3 text-base font-semibold text-bg-base transition-colors hover:bg-accent-gold-hover"
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
