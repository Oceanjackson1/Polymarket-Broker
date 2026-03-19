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

const stats = [
  { value: "145+", label: "体育/电竞品类" },
  { value: "30ms", label: "API 平均响应" },
  { value: "4", label: "BTC 时间框架" },
  { value: "24/7", label: "实时数据采集" },
];

const howItWorks = [
  {
    step: "01",
    title: "注册获取 API Key",
    description: "30 秒完成注册，立即获得 API Key。支持 API Key 和以太坊钱包两种认证方式。",
  },
  {
    step: "02",
    title: "获取独家数据",
    description: "通过 REST API 或 WebSocket 获取 NBA 融合数据、BTC 预测、体育订单簿等独家数据。",
  },
  {
    step: "03",
    title: "AI 发现机会",
    description: "AI 引擎自动扫描全市场定价偏差，推送交易信号。偏差超过阈值时实时提醒。",
  },
  {
    step: "04",
    title: "一键执行交易",
    description: "托管模式一键下单，或非托管模式本地签名提交。收敛套利策略自动执行。",
  },
];

export default function LandingPage() {
  return (
    <>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
      />

      {/* ═══ Hero + Bento Grid ═══ */}
      <HeroSection />

      {/* ═══ Stats Bar ═══ */}
      <section className="border-y border-white/[0.06] bg-bg-card/50 backdrop-blur-sm">
        <div className="mx-auto grid max-w-7xl grid-cols-2 divide-x divide-white/[0.06] px-6 md:grid-cols-4">
          {stats.map((stat) => (
            <div key={stat.label} className="py-8 text-center">
              <p className="font-mono text-3xl font-bold text-accent-gold">{stat.value}</p>
              <p className="mt-1 text-sm text-text-muted">{stat.label}</p>
            </div>
          ))}
        </div>
      </section>

      {/* ═══ Exclusive Features ═══ */}
      <section className="relative bg-bg-base">
        {/* Subtle grid background */}
        <div className="pointer-events-none absolute inset-0 -z-10">
          <svg className="h-full w-full opacity-[0.03]" xmlns="http://www.w3.org/2000/svg">
            <defs>
              <pattern id="grid-lines" x="0" y="0" width="64" height="64" patternUnits="userSpaceOnUse">
                <path d="M 64 0 L 0 0 0 64" fill="none" stroke="white" strokeWidth="0.5" />
              </pattern>
            </defs>
            <rect width="100%" height="100%" fill="url(#grid-lines)" />
          </svg>
        </div>

        <div className="mx-auto max-w-7xl px-6 py-24">
          <div className="mb-16 text-center">
            <p className="mb-3 text-sm font-semibold uppercase tracking-widest text-accent-gold">
              Exclusive Data
            </p>
            <h2 className="text-3xl font-bold text-text-primary md:text-4xl">
              竞品无法提供的数据
            </h2>
            <p className="mx-auto mt-4 max-w-xl text-text-secondary">
              这些是 Polymarket 原生 API 不提供的独家增强数据层
            </p>
          </div>
          <ExclusiveFeaturesGrid features={exclusiveFeatures} />
        </div>
      </section>

      {/* ═══ How It Works ═══ */}
      <section className="border-t border-white/[0.06] bg-bg-card/30">
        <div className="mx-auto max-w-7xl px-6 py-24">
          <div className="mb-16 text-center">
            <p className="mb-3 text-sm font-semibold uppercase tracking-widest text-accent-gold">
              How It Works
            </p>
            <h2 className="text-3xl font-bold text-text-primary md:text-4xl">
              四步开始交易
            </h2>
          </div>
          <div className="grid gap-8 md:grid-cols-4">
            {howItWorks.map((item, i) => (
              <div
                key={item.step}
                className={`animate-fade-in stagger-${i + 1} relative rounded-xl border border-white/[0.06] bg-bg-card/60 p-6 backdrop-blur-sm`}
              >
                <span className="mb-4 block font-mono text-3xl font-bold text-accent-gold/30">
                  {item.step}
                </span>
                <h3 className="mb-2 text-base font-semibold text-text-primary">
                  {item.title}
                </h3>
                <p className="text-sm leading-relaxed text-text-secondary">
                  {item.description}
                </p>
                {/* Connector line */}
                {i < howItWorks.length - 1 && (
                  <div className="absolute -right-4 top-1/2 hidden h-px w-8 bg-gradient-to-r from-accent-gold/30 to-transparent md:block" />
                )}
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ═══ API First (Code Preview) ═══ */}
      <section className="border-t border-white/[0.06] bg-bg-base">
        <div className="mx-auto max-w-7xl px-6 py-24">
          <div className="grid items-center gap-16 md:grid-cols-2">
            <div>
              <p className="mb-3 text-sm font-semibold uppercase tracking-widest text-accent-gold">
                Developer Experience
              </p>
              <h2 className="text-3xl font-bold text-text-primary md:text-4xl">
                API 优先设计
              </h2>
              <p className="mt-4 text-text-secondary">
                自有 Web 终端和第三方开发者调用完全相同的 API。我们自己吃自己的 API。
              </p>
              <ul className="mt-8 space-y-4">
                {[
                  "RESTful API + WebSocket 实时流",
                  "API Key + 以太坊钱包双认证路径",
                  "托管模式和非托管模式订单",
                  "完整的 OpenAPI 规范文档",
                ].map((item) => (
                  <li key={item} className="flex items-center gap-3 text-sm text-text-secondary">
                    <span className="flex h-5 w-5 items-center justify-center rounded-full bg-accent-gold/10 text-[10px] text-accent-gold">✓</span>
                    {item}
                  </li>
                ))}
              </ul>
              <div className="mt-8 flex gap-4">
                <Link
                  href="/docs/getting-started/quickstart"
                  className="btn-premium rounded-xl bg-accent-gold px-6 py-3 text-sm font-semibold text-bg-base"
                >
                  5 分钟快速接入
                </Link>
                <Link
                  href="/docs"
                  className="rounded-xl border border-white/10 px-6 py-3 text-sm font-semibold text-text-primary transition-colors hover:bg-white/[0.04]"
                >
                  API 文档
                </Link>
              </div>
            </div>
            <div className="animate-fade-in overflow-hidden rounded-xl border border-white/[0.06] bg-bg-card/80 shadow-2xl shadow-black/40">
              {/* Window chrome */}
              <div className="flex items-center gap-2 border-b border-white/[0.06] px-4 py-2.5">
                <div className="flex gap-1.5">
                  <div className="h-2.5 w-2.5 rounded-full bg-loss/60" />
                  <div className="h-2.5 w-2.5 rounded-full bg-accent-gold/60" />
                  <div className="h-2.5 w-2.5 rounded-full bg-profit/60" />
                </div>
                <span className="ml-2 text-[10px] text-text-muted">terminal — python3</span>
              </div>
              <pre className="overflow-x-auto p-6 text-sm leading-relaxed">
                <code className="font-mono">
                  <span className="text-info-blue">import</span> <span className="text-text-primary">requests</span>{"\n\n"}
                  <span className="text-text-muted"># 一行代码获取 NBA 融合数据</span>{"\n"}
                  <span className="text-text-primary">r</span> = <span className="text-text-primary">requests</span>.<span className="text-info-cyan">get</span>({"\n"}
                  {"  "}<span className="text-accent-gold">&quot;/api/v1/data/nba/games/gsw-lal/fusion&quot;</span>,{"\n"}
                  {"  "}headers={"{"}
                  <span className="text-accent-gold">&quot;X-API-Key&quot;</span>: <span className="text-accent-gold">&quot;pm_live_sk_...&quot;</span>
                  {"}"}{"\n"}
                  ){"\n\n"}
                  <span className="text-text-muted"># 偏差信号 → 自动交易</span>{"\n"}
                  <span className="text-info-blue">if</span> r.json()[<span className="text-accent-gold">&quot;bias_signal&quot;</span>][<span className="text-accent-gold">&quot;magnitude_bps&quot;</span>] &gt; <span className="text-profit">300</span>:{"\n"}
                  {"  "}<span className="text-text-primary">place_order</span>(side=<span className="text-accent-gold">&quot;BUY&quot;</span>, size=<span className="text-profit">100</span>)
                </code>
              </pre>
            </div>
          </div>
        </div>
      </section>

      {/* ═══ CTA ═══ */}
      <section className="relative overflow-hidden border-t border-white/[0.06] bg-bg-card/30">
        {/* Background glow */}
        <div className="pointer-events-none absolute inset-0 -z-10">
          <div className="absolute left-1/2 top-0 h-[300px] w-[600px] -translate-x-1/2 rounded-full bg-accent-gold/[0.06] blur-[100px]" />
        </div>

        <div className="mx-auto max-w-7xl px-6 py-24 text-center">
          <h2 className="text-3xl font-bold text-text-primary md:text-4xl">
            开始使用 Polymarket Broker
          </h2>
          <p className="mx-auto mt-4 max-w-lg text-text-secondary">
            Free 套餐永久免费 · Pro $99/月解锁全部独家数据和策略 · 30 秒完成注册
          </p>
          <div className="mt-10 flex items-center justify-center gap-4">
            <Link
              href="/dashboard"
              className="btn-premium rounded-xl bg-accent-gold px-10 py-4 text-base font-semibold text-bg-base"
            >
              免费注册
            </Link>
            <Link
              href="/pricing"
              className="rounded-xl border border-white/10 px-10 py-4 text-base font-semibold text-text-primary transition-colors hover:bg-white/[0.04]"
            >
              查看定价方案
            </Link>
          </div>
        </div>
      </section>
    </>
  );
}
