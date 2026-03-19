"use client";

import Link from "next/link";
import { motion } from "motion/react";
import { BackgroundOrbs } from "@/components/effects/background-orbs";

const featureVariants = {
  hidden: { opacity: 0, y: 24 },
  show: { opacity: 1, y: 0 },
};

interface ExclusiveFeature {
  title: string;
  description: string;
  badge: string;
  href: string;
  isAI: boolean;
}

export function HeroSection() {
  return (
    <section className="relative bg-bg-base">
      <BackgroundOrbs />
      <div className="mx-auto max-w-7xl px-6 py-24 text-center md:py-32">
        <div className="mb-6 inline-flex items-center gap-2 rounded-full border border-accent-gold-bg bg-accent-gold-bg/20 px-4 py-1.5 text-sm text-accent-gold">
          <span>机构级预测市场终端</span>
        </div>
        <motion.h1
          className="mx-auto max-w-4xl text-4xl font-bold tracking-tight text-text-primary md:text-6xl"
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.7 }}
        >
          用华尔街的工具
          <br />
          <span className="text-accent-gold">交易预测市场</span>
        </motion.h1>
        <motion.p
          className="mx-auto mt-6 max-w-2xl text-lg text-text-secondary"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.7, delay: 0.2 }}
        >
          Polymarket 本身不提供的独家数据 —— NBA 实时融合、145
          项体育订单簿、BTC 多时间框架预测、AI
          定价偏差分析。所有数据通过统一 REST API 交付。
        </motion.p>
        <motion.div
          className="mt-10 flex items-center justify-center gap-4"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.7, delay: 0.4 }}
        >
          <Link
            href="/dashboard"
            className="btn-premium rounded-lg bg-accent-gold px-8 py-3 text-base font-semibold text-bg-base transition-colors hover:bg-accent-gold-hover"
          >
            免费开始
          </Link>
          <Link
            href="/docs"
            className="rounded-lg border border-border-default px-8 py-3 text-base font-semibold text-text-primary transition-colors hover:bg-bg-elevated"
          >
            查看 API 文档
          </Link>
        </motion.div>
        <p className="mt-4 text-sm text-text-muted">
          Free 套餐: 500 次 API 调用/天 · 无需信用卡
        </p>
      </div>
    </section>
  );
}

export function ExclusiveFeaturesGrid({ features }: { features: ExclusiveFeature[] }) {
  return (
    <motion.div
      className="grid gap-6 md:grid-cols-2"
      initial="hidden"
      whileInView="show"
      viewport={{ once: true, margin: "-80px" }}
      transition={{ staggerChildren: 0.1 }}
    >
      {features.map((feature) => (
        <motion.div key={feature.title} variants={featureVariants}>
          <Link
            href={feature.href}
            className={`group block rounded-xl border bg-bg-base p-8 transition-colors hover:border-accent-gold/30 ${
              feature.isAI
                ? "gradient-border-gold border-accent-gold/30"
                : "border-border-subtle"
            }`}
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
        </motion.div>
      ))}
    </motion.div>
  );
}
