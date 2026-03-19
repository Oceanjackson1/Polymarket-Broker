"use client";

import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { useAuthContext, useLocale } from "@/lib/providers";
import BiasSignalBadge from "@/components/data/BiasSignalBadge";

export default function AnalysisPage() {
  const { api, token } = useAuthContext();
  const { t } = useLocale();
  const [marketId, setMarketId] = useState("");
  const [question, setQuestion] = useState("");

  // Scan
  const scanMutation = useMutation({
    mutationFn: () => api.scanMarkets(),
  });

  // Single market analysis
  const analyzeMutation = useMutation({
    mutationFn: (id: string) => api.analyzeMarket(id),
  });

  // Ask
  const askMutation = useMutation({
    mutationFn: (q: string) => api.askQuestion(q),
  });

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold">{t("nav.analysis")}</h1>
        <p className="mt-1 text-sm text-zinc-400">AI-powered market analysis</p>
      </div>

      {/* Scan Markets */}
      <section className="rounded-lg border border-zinc-800 bg-zinc-900 p-4">
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-lg font-semibold">{t("analysis.scanMarkets")}</h2>
          <button
            onClick={() => scanMutation.mutate()}
            disabled={scanMutation.isPending}
            className="rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
          >
            {scanMutation.isPending ? t("common.loading") : t("analysis.scanMarkets")}
          </button>
        </div>

        {scanMutation.data?.opportunities && (
          <div className="space-y-2">
            {scanMutation.data.opportunities.map((opp, i) => (
              <div key={i} className="flex items-center justify-between rounded-md bg-zinc-800 p-3">
                <span className="max-w-[70%] truncate text-sm text-white">{opp.question}</span>
                <BiasSignalBadge direction={opp.bias_direction} bps={opp.bias_bps} />
              </div>
            ))}
          </div>
        )}
      </section>

      {/* Analyze Single Market */}
      <section className="rounded-lg border border-zinc-800 bg-zinc-900 p-4">
        <h2 className="mb-4 text-lg font-semibold">{t("analysis.analyzeMarket")}</h2>
        <div className="flex gap-2">
          <input
            value={marketId}
            onChange={(e) => setMarketId(e.target.value)}
            placeholder={t("analysis.enterMarketId")}
            className="flex-1 rounded-md border border-zinc-700 bg-zinc-800 px-3 py-2 text-sm text-white placeholder-zinc-500 focus:border-blue-500 focus:outline-none"
          />
          <button
            onClick={() => analyzeMutation.mutate(marketId)}
            disabled={!marketId || analyzeMutation.isPending}
            className="rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
          >
            Analyze
          </button>
        </div>

        {analyzeMutation.data && (
          <div className="mt-4 space-y-3 rounded-md bg-zinc-800 p-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <span className="text-xs text-zinc-500">{t("analysis.aiProbability")}</span>
                <div className="text-lg font-bold text-white">
                  {(analyzeMutation.data.ai_probability * 100).toFixed(1)}%
                </div>
              </div>
              <div>
                <span className="text-xs text-zinc-500">{t("analysis.marketProbability")}</span>
                <div className="text-lg font-bold text-white">
                  {(analyzeMutation.data.market_price * 100).toFixed(1)}%
                </div>
              </div>
            </div>
            <BiasSignalBadge
              direction={analyzeMutation.data.bias_direction}
              bps={analyzeMutation.data.bias_bps}
            />
            <div>
              <span className="text-xs text-zinc-500">{t("analysis.reasoning")}</span>
              <p className="mt-1 text-sm text-zinc-300">{analyzeMutation.data.reasoning}</p>
            </div>
          </div>
        )}
      </section>

      {/* Ask Question */}
      <section className="rounded-lg border border-zinc-800 bg-zinc-900 p-4">
        <h2 className="mb-4 text-lg font-semibold">{t("analysis.askQuestion")}</h2>
        <div className="flex gap-2">
          <input
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder={t("analysis.enterQuestion")}
            className="flex-1 rounded-md border border-zinc-700 bg-zinc-800 px-3 py-2 text-sm text-white placeholder-zinc-500 focus:border-blue-500 focus:outline-none"
            onKeyDown={(e) => e.key === "Enter" && question && askMutation.mutate(question)}
          />
          <button
            onClick={() => askMutation.mutate(question)}
            disabled={!question || askMutation.isPending}
            className="rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
          >
            Ask
          </button>
        </div>

        {askMutation.data && (
          <div className="mt-4 rounded-md bg-zinc-800 p-4">
            <p className="text-sm text-zinc-300 whitespace-pre-wrap">{askMutation.data.answer}</p>
          </div>
        )}
      </section>
    </div>
  );
}
