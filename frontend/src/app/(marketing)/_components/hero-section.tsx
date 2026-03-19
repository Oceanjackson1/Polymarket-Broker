"use client";

import Link from "next/link";
import { motion } from "motion/react";

/* ─── Grid Background Pattern ─── */
function GridPattern() {
  return (
    <div className="pointer-events-none absolute inset-0 -z-10 overflow-hidden">
      {/* Dot grid */}
      <svg className="absolute inset-0 h-full w-full" xmlns="http://www.w3.org/2000/svg">
        <defs>
          <pattern id="grid-dots" x="0" y="0" width="32" height="32" patternUnits="userSpaceOnUse">
            <circle cx="1" cy="1" r="0.8" fill="rgba(148,163,184,0.12)" />
          </pattern>
        </defs>
        <rect width="100%" height="100%" fill="url(#grid-dots)" />
      </svg>
      {/* Gradient overlay to fade edges */}
      <div className="absolute inset-0 bg-gradient-to-b from-bg-base via-transparent to-bg-base" />
      <div className="absolute inset-0 bg-gradient-to-r from-bg-base via-transparent to-bg-base" />
      {/* Ambient glow orbs */}
      <div className="absolute left-1/4 top-1/4 h-[500px] w-[500px] rounded-full bg-accent-gold/[0.04] blur-[120px]" />
      <div className="absolute right-1/4 top-1/3 h-[400px] w-[400px] rounded-full bg-info-blue/[0.05] blur-[100px]" />
      <div className="absolute bottom-0 left-1/2 h-[300px] w-[600px] -translate-x-1/2 rounded-full bg-info-cyan/[0.03] blur-[80px]" />
    </div>
  );
}

/* ─── Terminal Mockup Frame ─── */
function MockupFrame({ children, title }: { children: React.ReactNode; title: string }) {
  return (
    <div className="overflow-hidden rounded-xl border border-white/[0.06] bg-bg-card/80 shadow-2xl shadow-black/40 backdrop-blur-sm">
      {/* Window chrome */}
      <div className="flex items-center gap-2 border-b border-white/[0.06] px-4 py-2.5">
        <div className="flex gap-1.5">
          <div className="h-2.5 w-2.5 rounded-full bg-loss/60" />
          <div className="h-2.5 w-2.5 rounded-full bg-accent-gold/60" />
          <div className="h-2.5 w-2.5 rounded-full bg-profit/60" />
        </div>
        <span className="ml-2 text-[10px] text-text-muted">{title}</span>
      </div>
      <div className="p-4">{children}</div>
    </div>
  );
}

/* ─── Dashboard Preview Mockup ─── */
function DashboardMockup() {
  return (
    <MockupFrame title="Polymarket Broker — Dashboard">
      <div className="space-y-3">
        {/* Stats row */}
        <div className="grid grid-cols-4 gap-2">
          {[
            { label: "Total", value: "$45,230", color: "text-text-primary" },
            { label: "P&L", value: "+$1,240", color: "text-profit" },
            { label: "Positions", value: "12", color: "text-text-primary" },
            { label: "API Calls", value: "347/500", color: "text-text-primary" },
          ].map((s) => (
            <div key={s.label} className="rounded-md border border-white/[0.04] bg-bg-base/60 p-2">
              <p className="text-[8px] text-text-muted">{s.label}</p>
              <p className={`font-mono text-xs font-semibold ${s.color}`}>{s.value}</p>
            </div>
          ))}
        </div>
        {/* Chart placeholder */}
        <div className="flex h-24 items-end gap-px rounded-md border border-white/[0.04] bg-bg-base/60 p-3">
          {[30, 45, 35, 55, 50, 65, 60, 72, 68, 78, 75, 82, 80, 88, 85, 90, 87, 92, 95, 93].map((h, i) => (
            <div key={i} className="flex-1 rounded-t-sm bg-accent-gold/40" style={{ height: `${h}%` }} />
          ))}
        </div>
      </div>
    </MockupFrame>
  );
}

/* ─── NBA Fusion Mockup ─── */
function NbaFusionMockup() {
  return (
    <MockupFrame title="NBA Live Fusion — GSW vs LAL">
      <div className="space-y-3">
        {/* Score */}
        <div className="flex items-center justify-center gap-6 rounded-md border border-white/[0.04] bg-bg-base/60 p-3">
          <div className="text-center">
            <p className="text-[8px] text-text-muted">GSW</p>
            <p className="font-mono text-xl font-bold text-text-primary">94</p>
          </div>
          <div className="text-center">
            <p className="text-[8px] text-info-cyan">Q3</p>
            <p className="font-mono text-sm font-semibold text-info-cyan">4:22</p>
          </div>
          <div className="text-center">
            <p className="text-[8px] text-text-muted">LAL</p>
            <p className="font-mono text-xl font-bold text-text-primary">87</p>
          </div>
        </div>
        {/* Bias signal */}
        <div className="rounded-md border border-accent-gold/20 bg-accent-gold/[0.06] p-2">
          <div className="flex items-center justify-between">
            <span className="text-[8px] font-semibold uppercase text-accent-gold">Bias Signal</span>
            <span className="font-mono text-[10px] text-profit">HOME_UNDERPRICED +420bps</span>
          </div>
        </div>
      </div>
    </MockupFrame>
  );
}

/* ─── BTC Prediction Mockup ─── */
function BtcMockup() {
  return (
    <MockupFrame title="BTC Multi-Timeframe Predictions">
      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <span className="text-[10px] text-text-muted">Bitcoin</span>
          <span className="font-mono text-sm font-bold text-text-primary">$68,420</span>
        </div>
        {[
          { tf: "5m", prob: 0.61, dir: "up" },
          { tf: "15m", prob: 0.48, dir: "down" },
          { tf: "1h", prob: 0.55, dir: "up" },
          { tf: "4h", prob: 0.62, dir: "up" },
        ].map((row) => (
          <div key={row.tf} className="flex items-center justify-between rounded border border-white/[0.04] bg-bg-base/60 p-1.5">
            <span className="font-mono text-[10px] text-text-muted">{row.tf}</span>
            <div className="h-1 flex-1 mx-2 rounded-full bg-bg-elevated overflow-hidden">
              <div className={`h-full rounded-full ${row.dir === "up" ? "bg-profit/60" : "bg-loss/60"}`} style={{ width: `${row.prob * 100}%` }} />
            </div>
            <span className={`font-mono text-[10px] ${row.dir === "up" ? "text-profit" : "text-loss"}`}>
              {row.dir === "up" ? "▲" : "▼"} {row.prob.toFixed(2)}
            </span>
          </div>
        ))}
      </div>
    </MockupFrame>
  );
}

/* ─── Orderbook Mockup ─── */
function OrderbookMockup() {
  return (
    <MockupFrame title="Order Book — Market View">
      <div className="grid grid-cols-2 gap-2">
        <div className="space-y-0.5">
          <p className="text-[8px] font-semibold text-profit">BID</p>
          {[
            { p: "0.34", s: "500", w: 40 },
            { p: "0.33", s: "800", w: 65 },
            { p: "0.32", s: "1200", w: 95 },
            { p: "0.31", s: "900", w: 72 },
          ].map((row) => (
            <div key={row.p} className="relative flex items-center justify-between rounded-sm px-1.5 py-0.5">
              <div className="depth-bar depth-bar-bid rounded-sm" style={{ width: `${row.w}%` }} />
              <span className="relative z-10 font-mono text-[9px] text-profit">{row.p}</span>
              <span className="relative z-10 font-mono text-[9px] text-text-muted">{row.s}</span>
            </div>
          ))}
        </div>
        <div className="space-y-0.5">
          <p className="text-[8px] font-semibold text-loss">ASK</p>
          {[
            { p: "0.36", s: "300", w: 25 },
            { p: "0.37", s: "200", w: 17 },
            { p: "0.38", s: "600", w: 50 },
            { p: "0.39", s: "450", w: 37 },
          ].map((row) => (
            <div key={row.p} className="relative flex items-center justify-between rounded-sm px-1.5 py-0.5">
              <div className="depth-bar depth-bar-ask rounded-sm" style={{ width: `${row.w}%` }} />
              <span className="relative z-10 font-mono text-[9px] text-loss">{row.p}</span>
              <span className="relative z-10 font-mono text-[9px] text-text-muted">{row.s}</span>
            </div>
          ))}
        </div>
      </div>
    </MockupFrame>
  );
}

/* ─── API Code Mockup ─── */
function ApiCodeMockup() {
  return (
    <MockupFrame title="terminal — API Quick Start">
      <pre className="text-[10px] leading-relaxed">
        <code>
          <span className="text-text-muted"># NBA 融合数据 — 一个 API 获取比分+赔率+偏差</span>{"\n"}
          <span className="text-info-cyan">curl</span>{" -H "}<span className="text-accent-gold">&quot;X-API-Key: pm_live_sk_xxx&quot;</span>{" \\\n"}
          {"  "}<span className="text-text-primary">/api/v1/data/nba/games/gsw-lal/fusion</span>{"\n\n"}
          <span className="text-text-muted"># Response (30ms)</span>{"\n"}
          <span className="text-text-secondary">{`{`}</span>{"\n"}
          {"  "}<span className="text-info-blue">&quot;score&quot;</span>: {"{ "}<span className="text-accent-gold">&quot;home&quot;</span>: <span className="text-profit">94</span>, <span className="text-accent-gold">&quot;away&quot;</span>: <span className="text-profit">87</span>{" },"}{"\n"}
          {"  "}<span className="text-info-blue">&quot;bias_signal&quot;</span>: {"{ "}<span className="text-accent-gold">&quot;direction&quot;</span>: <span className="text-profit">&quot;HOME_UNDERPRICED&quot;</span>{" },"}{"\n"}
          {"  "}<span className="text-info-blue">&quot;magnitude_bps&quot;</span>: <span className="text-accent-gold">420</span>{"\n"}
          <span className="text-text-secondary">{`}`}</span>
        </code>
      </pre>
    </MockupFrame>
  );
}

/* ═══ HERO SECTION ═══ */
export function HeroSection() {
  return (
    <section className="relative overflow-hidden bg-bg-base">
      <GridPattern />

      <div className="relative mx-auto max-w-7xl px-6 pb-8 pt-20 md:pt-28">
        {/* Badge + Title */}
        <div className="text-center">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
            className="mb-6 inline-flex items-center gap-2 rounded-full border border-accent-gold/20 bg-accent-gold/[0.06] px-4 py-1.5 text-sm text-accent-gold backdrop-blur-sm"
          >
            <span className="live-dot h-1.5 w-1.5 rounded-full bg-accent-gold" />
            机构级预测市场终端
          </motion.div>

          <motion.h1
            className="mx-auto max-w-4xl text-4xl font-bold tracking-tight text-text-primary md:text-6xl lg:text-7xl"
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.7, delay: 0.1 }}
          >
            用华尔街的工具
            <br />
            <span className="bg-gradient-to-r from-accent-gold via-amber-400 to-accent-gold bg-clip-text text-transparent">
              交易预测市场
            </span>
          </motion.h1>

          <motion.p
            className="mx-auto mt-6 max-w-2xl text-lg leading-relaxed text-text-secondary"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.7, delay: 0.25 }}
          >
            独家数据，竞品无法提供 —— NBA 实时融合、145 项体育订单簿、
            BTC 多时间框架预测、AI 定价偏差分析
          </motion.p>

          <motion.div
            className="mt-10 flex items-center justify-center gap-4"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.7, delay: 0.4 }}
          >
            <Link
              href="/dashboard"
              className="btn-premium rounded-xl bg-accent-gold px-8 py-3.5 text-base font-semibold text-bg-base"
            >
              免费开始
            </Link>
            <Link
              href="/docs"
              className="rounded-xl border border-white/10 bg-white/[0.03] px-8 py-3.5 text-base font-semibold text-text-primary backdrop-blur-sm transition-colors hover:bg-white/[0.06]"
            >
              查看 API 文档
            </Link>
          </motion.div>
          <motion.p
            className="mt-4 text-sm text-text-muted"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.6 }}
          >
            Free 套餐永久免费 · 500 次 API 调用/天 · 无需信用卡
          </motion.p>
        </div>

        {/* ─── Bento Grid: Product Preview ─── */}
        <motion.div
          className="mt-16 grid gap-4 md:grid-cols-3 md:grid-rows-2"
          initial={{ opacity: 0, y: 40 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.5 }}
        >
          {/* Main dashboard — spans 2 cols */}
          <div className="md:col-span-2">
            <DashboardMockup />
          </div>

          {/* NBA Fusion */}
          <div className="md:row-span-2">
            <div className="flex h-full flex-col gap-4">
              <NbaFusionMockup />
              <BtcMockup />
            </div>
          </div>

          {/* Orderbook + API Code */}
          <div>
            <OrderbookMockup />
          </div>
          <div>
            <ApiCodeMockup />
          </div>
        </motion.div>
      </div>
    </section>
  );
}

/* ═══ EXCLUSIVE FEATURES GRID ═══ */
interface ExclusiveFeature {
  title: string;
  description: string;
  badge: string;
  href: string;
  isAI: boolean;
}

const featureVariants = {
  hidden: { opacity: 0, y: 24 },
  show: { opacity: 1, y: 0 },
};

export function ExclusiveFeaturesGrid({ features }: { features: ExclusiveFeature[] }) {
  return (
    <motion.div
      className="grid gap-4 md:grid-cols-2"
      initial="hidden"
      whileInView="show"
      viewport={{ once: true, margin: "-80px" }}
      transition={{ staggerChildren: 0.1 }}
    >
      {features.map((feature) => (
        <motion.div key={feature.title} variants={featureVariants}>
          <Link
            href={feature.href}
            className={`hover-glow group block rounded-xl border p-8 transition-all duration-300 ${
              feature.isAI
                ? "gradient-border-gold border-accent-gold/30 bg-bg-card"
                : "border-white/[0.06] bg-bg-card/60 hover:border-accent-gold/20 hover:bg-bg-card"
            }`}
          >
            <div className="mb-4 flex items-center gap-3">
              <span className={`rounded-md px-2.5 py-1 text-xs font-semibold ${
                feature.isAI
                  ? "bg-accent-gold/10 text-accent-gold"
                  : "bg-info-cyan/10 text-info-cyan"
              }`}>
                {feature.badge}
              </span>
              <h3 className="text-lg font-semibold text-text-primary group-hover:text-accent-gold transition-colors">
                {feature.title}
              </h3>
            </div>
            <p className="text-sm leading-relaxed text-text-secondary">
              {feature.description}
            </p>
            <div className="mt-4 text-sm text-text-muted group-hover:text-accent-gold transition-colors">
              了解更多 →
            </div>
          </Link>
        </motion.div>
      ))}
    </motion.div>
  );
}
