"use client";

import Link from "next/link";
import { motion } from "motion/react";
import { BlurText } from "@/components/effects/blur-text";
import { Particles } from "@/components/effects/particles";

/* ─── Product Mockups ─── */

function ArbitragePreview() {
  return (
    <div className="overflow-hidden rounded-2xl border border-white/[0.08] bg-[#0a0a0a]">
      <div className="flex items-center gap-2 border-b border-white/[0.06] px-5 py-3">
        <div className="flex gap-1.5">
          <div className="h-3 w-3 rounded-full bg-[#ff5f57]" />
          <div className="h-3 w-3 rounded-full bg-[#febc2e]" />
          <div className="h-3 w-3 rounded-full bg-[#28c840]" />
        </div>
        <span className="ml-3 text-xs text-white/30">Polydesk — Arbitrage Scanner</span>
      </div>
      <div className="p-5">
        {/* Header */}
        <div className="mb-4 flex items-center justify-between">
          <p className="text-xs font-medium uppercase tracking-widest text-white/30">Cross-Platform Spreads</p>
          <span className="rounded-full bg-emerald-500/10 px-2.5 py-0.5 text-[10px] font-medium text-emerald-400">3 Opportunities</span>
        </div>
        {/* Spread rows */}
        <div className="space-y-2">
          {[
            { event: "NBA Finals MVP", poly: "0.42", kalshi: "0.38", spread: "+400", dir: "BUY_POLY" },
            { event: "BTC > $75k June", poly: "0.31", kalshi: "0.35", spread: "+400", dir: "BUY_KALSHI" },
            { event: "Fed Rate Cut Jul", poly: "0.68", kalshi: "0.62", spread: "+600", dir: "BUY_POLY" },
          ].map((r) => (
            <div key={r.event} className="flex items-center justify-between rounded-xl bg-white/[0.03] px-4 py-3">
              <div className="flex-1">
                <p className="text-sm text-white">{r.event}</p>
                <p className="mt-0.5 text-[11px] text-white/25">Poly {r.poly} vs Kalshi {r.kalshi}</p>
              </div>
              <div className="text-right">
                <p className="font-mono text-sm font-medium text-emerald-400">{r.spread} bps</p>
                <p className="text-[10px] text-white/25">{r.dir}</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

function NbaPreview() {
  return (
    <div className="overflow-hidden rounded-2xl border border-white/[0.08] bg-[#0a0a0a] p-5">
      <p className="mb-4 text-xs font-medium uppercase tracking-widest text-white/30">Live Game</p>
      <div className="mb-4 flex items-center justify-between">
        <div className="text-center">
          <p className="text-xs text-white/40">GSW</p>
          <p className="font-mono text-3xl font-bold text-white">94</p>
        </div>
        <div className="text-center">
          <p className="font-mono text-xs text-emerald-400">LIVE</p>
          <p className="font-mono text-lg text-white/50">Q3 · 4:22</p>
        </div>
        <div className="text-center">
          <p className="text-xs text-white/40">LAL</p>
          <p className="font-mono text-3xl font-bold text-white">87</p>
        </div>
      </div>
      <div className="rounded-xl bg-white/[0.04] p-3">
        <div className="flex items-center justify-between">
          <span className="text-[10px] uppercase tracking-wider text-white/30">Bias Signal</span>
          <span className="font-mono text-xs text-emerald-400">HOME_UNDERPRICED</span>
        </div>
        <div className="mt-2 flex items-center justify-between">
          <span className="text-[10px] text-white/30">Magnitude</span>
          <span className="font-mono text-sm font-medium text-white">+420 bps</span>
        </div>
      </div>
    </div>
  );
}

function OddsPreview() {
  return (
    <div className="overflow-hidden rounded-2xl border border-white/[0.08] bg-[#0a0a0a] p-5">
      <div className="mb-4 flex items-center justify-between">
        <p className="text-xs font-medium uppercase tracking-widest text-white/30">Bookmaker vs Polymarket</p>
        <span className="rounded-full bg-white/[0.06] px-2 py-0.5 text-[10px] text-white/40">EPL</span>
      </div>
      <div className="space-y-2">
        {[
          { match: "Arsenal vs Chelsea", book: "72%", poly: "65%", bias: "+700" },
          { match: "Liverpool vs City", book: "45%", poly: "48%", bias: "-300" },
          { match: "Spurs vs United", book: "58%", poly: "53%", bias: "+500" },
        ].map((r) => (
          <div key={r.match} className="flex items-center gap-3 rounded-lg bg-white/[0.03] px-3 py-2">
            <span className="flex-1 text-xs text-white/50">{r.match}</span>
            <span className="font-mono text-[11px] text-white/30">{r.book}</span>
            <span className="text-[10px] text-white/20">vs</span>
            <span className="font-mono text-[11px] text-white/30">{r.poly}</span>
            <span className={`font-mono text-xs font-medium ${r.bias.startsWith("+") ? "text-emerald-400" : "text-red-400"}`}>
              {r.bias}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}

function BtcPreview() {
  return (
    <div className="overflow-hidden rounded-2xl border border-white/[0.08] bg-[#0a0a0a] p-5">
      <div className="mb-4 flex items-center justify-between">
        <p className="text-xs font-medium uppercase tracking-widest text-white/30">BTC Fusion</p>
        <p className="font-mono text-sm font-medium text-white">$68,420</p>
      </div>
      <div className="space-y-2">
        {[
          { tf: "5m", p: 0.61, up: true },
          { tf: "15m", p: 0.48, up: false },
          { tf: "1h", p: 0.55, up: true },
          { tf: "4h", p: 0.62, up: true },
        ].map((r) => (
          <div key={r.tf} className="flex items-center gap-3 rounded-lg bg-white/[0.03] px-3 py-2">
            <span className="w-8 font-mono text-xs text-white/40">{r.tf}</span>
            <div className="h-1 flex-1 overflow-hidden rounded-full bg-white/[0.06]">
              <div
                className={`h-full rounded-full ${r.up ? "bg-emerald-500/50" : "bg-red-500/40"}`}
                style={{ width: `${r.p * 100}%` }}
              />
            </div>
            <span className={`font-mono text-xs ${r.up ? "text-emerald-400" : "text-red-400"}`}>
              {r.p.toFixed(2)}
            </span>
          </div>
        ))}
      </div>
      <div className="mt-3 rounded-lg bg-white/[0.03] px-3 py-2">
        <p className="text-[10px] text-white/25">CoinGlass: Funding +0.012% · OI $18.2B · F&G 72</p>
      </div>
    </div>
  );
}

/* ═══ HERO ═══ */
export function HeroSection() {
  return (
    <section className="relative bg-black overflow-hidden">
      {/* Particles background */}
      <div className="absolute inset-0 h-[800px]">
        <Particles count={35} speed={0.2} opacity={0.12} size={1.2} />
      </div>
      {/* Soft glow */}
      <div className="pointer-events-none absolute inset-x-0 top-0 -z-10 h-[600px]">
        <div className="absolute left-1/2 top-0 h-[400px] w-[800px] -translate-x-1/2 rounded-full bg-white/[0.02] blur-[120px]" />
      </div>

      <div className="relative mx-auto max-w-6xl px-6 pb-4 pt-24 md:pt-36">
        {/* ── Title ── */}
        <div className="mx-auto max-w-4xl text-center">
          <motion.p
            className="mb-8 text-[11px] font-medium uppercase tracking-[0.25em] text-white/20"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.8 }}
          >
            The Data Layer for Prediction Markets
          </motion.p>

          <h1 className="text-[clamp(2.5rem,7vw,4.5rem)] font-semibold leading-[1.08] tracking-tight">
            <BlurText text="Find Edge" className="text-white" delay={0.2} />{" "}
            <BlurText text="Others Miss" className="text-white/20" delay={0.5} />
          </h1>
        </div>

        {/* ── Description ── */}
        <motion.p
          className="mx-auto mt-7 max-w-lg text-center text-[17px] leading-[1.7] text-white/45"
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.7 }}
        >
          Cross-platform arbitrage, 40+ bookmaker odds, live sports fusion,
          weather ensemble forecasts, and AI pricing-bias analysis.
          <br />
          <span className="text-white/60">One API. 80+ endpoints.</span>
        </motion.p>

        {/* ── Actions ── */}
        <motion.div
          className="mt-12 flex items-center justify-center gap-3"
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.4 }}
        >
          <Link
            href="/login"
            className="rounded-full bg-white px-8 py-3.5 text-[15px] font-medium text-black transition-all hover:bg-white/90 active:scale-[0.98]"
          >
            Get Started Free
          </Link>
          <Link
            href="/docs"
            className="rounded-full border border-white/[0.12] px-8 py-3.5 text-[15px] font-medium text-white/80 transition-all hover:border-white/25 hover:bg-white/[0.04]"
          >
            API Docs
          </Link>
        </motion.div>

        {/* ── Bento Grid ── */}
        <motion.div
          className="mt-20 grid gap-4 md:grid-cols-12"
          initial={{ opacity: 0, y: 40 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 1, delay: 0.5 }}
        >
          {/* Arbitrage Scanner — 8 cols */}
          <div className="md:col-span-8">
            <ArbitragePreview />
          </div>

          {/* NBA — 4 cols */}
          <div className="md:col-span-4">
            <NbaPreview />
          </div>

          {/* Odds — 5 cols */}
          <div className="md:col-span-5">
            <OddsPreview />
          </div>

          {/* BTC — 7 cols */}
          <div className="md:col-span-7">
            <BtcPreview />
          </div>
        </motion.div>
      </div>
    </section>
  );
}

/* ═══ FEATURES GRID ═══ */
interface ExclusiveFeature {
  title: string;
  description: string;
  badge: string;
  href: string;
  isAI: boolean;
}

export function ExclusiveFeaturesGrid({ features }: { features: ExclusiveFeature[] }) {
  return (
    <motion.div
      className="grid gap-4 md:grid-cols-2 lg:grid-cols-3"
      initial="hidden"
      whileInView="show"
      viewport={{ once: true, margin: "-60px" }}
      transition={{ staggerChildren: 0.08 }}
    >
      {features.map((feature) => (
        <motion.div
          key={feature.title}
          variants={{ hidden: { opacity: 0, y: 20 }, show: { opacity: 1, y: 0 } }}
        >
          <Link
            href={feature.href}
            className="group block rounded-2xl border border-white/[0.06] bg-white/[0.02] p-8 transition-all duration-300 hover:border-white/[0.12] hover:bg-white/[0.04]"
          >
            <div className="mb-4 flex items-center gap-3">
              <span className={`rounded-full px-3 py-1 text-xs font-medium ${
                feature.isAI
                  ? "bg-blue-500/10 text-blue-400"
                  : "bg-white/[0.06] text-white/60"
              }`}>
                {feature.badge}
              </span>
            </div>
            <h3 className="mb-2 text-xl font-semibold text-white">
              {feature.title}
            </h3>
            <p className="text-sm leading-relaxed text-white/50">
              {feature.description}
            </p>
            <p className="mt-6 text-sm text-white/25 transition-colors group-hover:text-white/50">
              Learn More {"\u2192"}
            </p>
          </Link>
        </motion.div>
      ))}
    </motion.div>
  );
}
