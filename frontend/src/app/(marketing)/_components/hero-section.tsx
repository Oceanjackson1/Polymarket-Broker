"use client";

import Link from "next/link";
import { motion } from "motion/react";

/* ─── Product Mockups (Apple-style: minimal, clean) ─── */

function DashboardPreview() {
  return (
    <div className="overflow-hidden rounded-2xl border border-white/[0.08] bg-[#0a0a0a]">
      <div className="flex items-center gap-2 border-b border-white/[0.06] px-5 py-3">
        <div className="flex gap-1.5">
          <div className="h-3 w-3 rounded-full bg-[#ff5f57]" />
          <div className="h-3 w-3 rounded-full bg-[#febc2e]" />
          <div className="h-3 w-3 rounded-full bg-[#28c840]" />
        </div>
        <span className="ml-3 text-xs text-white/30">Polymarket Broker</span>
      </div>
      <div className="p-5">
        {/* Stats */}
        <div className="mb-4 grid grid-cols-4 gap-3">
          {[
            { l: "Portfolio", v: "$45,230.00" },
            { l: "Today", v: "+$1,240.50", c: "text-emerald-400" },
            { l: "Positions", v: "12" },
            { l: "Win Rate", v: "68.4%" },
          ].map((s) => (
            <div key={s.l} className="rounded-xl bg-white/[0.04] p-3">
              <p className="text-[10px] text-white/30">{s.l}</p>
              <p className={`mt-0.5 font-mono text-sm font-medium ${s.c || "text-white"}`}>{s.v}</p>
            </div>
          ))}
        </div>
        {/* Chart */}
        <div className="flex h-32 items-end gap-[2px] rounded-xl bg-white/[0.02] p-4">
          {[28,32,30,38,35,42,40,48,45,52,50,58,55,62,60,65,62,68,72,70,75,73,78,80,82,78,85,88,85,90].map((h, i) => (
            <div
              key={i}
              className="flex-1 rounded-t bg-gradient-to-t from-white/20 to-white/5"
              style={{ height: `${h}%` }}
            />
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

function BtcPreview() {
  return (
    <div className="overflow-hidden rounded-2xl border border-white/[0.08] bg-[#0a0a0a] p-5">
      <div className="mb-4 flex items-center justify-between">
        <p className="text-xs font-medium uppercase tracking-widest text-white/30">BTC Predictions</p>
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
    </div>
  );
}

function CodePreview() {
  return (
    <div className="overflow-hidden rounded-2xl border border-white/[0.08] bg-[#0a0a0a]">
      <div className="flex items-center gap-2 border-b border-white/[0.06] px-5 py-3">
        <div className="flex gap-1.5">
          <div className="h-3 w-3 rounded-full bg-[#ff5f57]" />
          <div className="h-3 w-3 rounded-full bg-[#febc2e]" />
          <div className="h-3 w-3 rounded-full bg-[#28c840]" />
        </div>
        <span className="ml-3 text-xs text-white/30">main.py</span>
      </div>
      <pre className="p-5 text-[13px] leading-relaxed">
        <code>
          <span className="text-blue-400">import</span> <span className="text-white">requests</span>{"\n\n"}
          <span className="text-white/30"># Get live NBA fusion data</span>{"\n"}
          <span className="text-white">data</span> = requests.<span className="text-blue-400">get</span>({"\n"}
          {"  "}<span className="text-emerald-400">&quot;/api/v1/data/nba/games/gsw-lal/fusion&quot;</span>{"\n"}
          ).json(){"\n\n"}
          <span className="text-white/30"># Auto-trade on pricing bias</span>{"\n"}
          <span className="text-blue-400">if</span> data[<span className="text-emerald-400">&quot;magnitude_bps&quot;</span>] &gt; <span className="text-purple-400">300</span>:{"\n"}
          {"  "}place_order(side=<span className="text-emerald-400">&quot;BUY&quot;</span>)
        </code>
      </pre>
    </div>
  );
}

/* ═══ HERO ═══ */
export function HeroSection() {
  return (
    <section className="relative bg-black">
      {/* Subtle top glow */}
      <div className="pointer-events-none absolute inset-x-0 top-0 -z-10 h-[600px]">
        <div className="absolute left-1/2 top-0 h-[400px] w-[800px] -translate-x-1/2 rounded-full bg-white/[0.02] blur-[120px]" />
      </div>

      <div className="mx-auto max-w-6xl px-6 pb-4 pt-24 md:pt-36">
        {/* ── Title Group ── */}
        <div className="mx-auto max-w-4xl text-center">
          <motion.p
            className="mb-8 text-[11px] font-medium uppercase tracking-[0.25em] text-white/20"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.8 }}
          >
            Institutional Prediction Market Terminal
          </motion.p>

          <motion.h1
            className="text-[clamp(3rem,7vw,4.5rem)] font-semibold leading-[1.08] tracking-tight text-white"
            initial={{ opacity: 0, y: 24 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.1 }}
          >
            Prediction markets{" "}
            <span className="text-white/20">reimagined</span>
          </motion.h1>
        </div>

        {/* ── Description Group (tighter coupling to title) ── */}
        <motion.p
          className="mx-auto mt-7 max-w-md text-center text-[17px] leading-[1.7] text-white/45"
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.25 }}
        >
          Exclusive data Polymarket does not offer.
          <br />
          NBA live fusion, BTC multi-timeframe predictions,
          <br />
          AI pricing-bias analysis, one unified API
        </motion.p>

        {/* ── Action Group ── */}
        <motion.div
          className="mt-12 flex items-center justify-center gap-3"
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.4 }}
        >
          <Link
            href="/dashboard"
            className="rounded-full bg-white px-8 py-3.5 text-[15px] font-medium text-black transition-all hover:bg-white/90 active:scale-[0.98]"
          >
            Get started free
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
          {/* Dashboard — 8 cols */}
          <div className="md:col-span-8">
            <DashboardPreview />
          </div>

          {/* NBA — 4 cols */}
          <div className="md:col-span-4">
            <NbaPreview />
          </div>

          {/* Code — 5 cols */}
          <div className="md:col-span-5">
            <CodePreview />
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
      className="grid gap-4 md:grid-cols-2"
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
              <span className="rounded-full bg-white/[0.06] px-3 py-1 text-xs font-medium text-white/60">
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
              Learn more
            </p>
          </Link>
        </motion.div>
      ))}
    </motion.div>
  );
}
