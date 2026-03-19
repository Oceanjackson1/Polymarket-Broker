"use client";

import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { analysisApi } from "@/lib/api";

function BiasTag({ direction, bps }: { direction: string; bps: number }) {
  const isUp = direction === "FORECAST_HIGHER" || direction === "AI_HIGHER";
  const isDown = direction === "MARKET_HIGHER" || direction === "AI_LOWER";
  return (
    <span
      className={`rounded px-2 py-0.5 font-mono text-[10px] font-medium ${
        isUp ? "bg-profit-bg text-profit" : isDown ? "bg-loss-bg text-loss" : "bg-bg-elevated text-text-muted"
      }`}
    >
      {isUp ? "▲" : isDown ? "▼" : "—"} {(bps / 100).toFixed(1)}%
    </span>
  );
}

export default function AnalysisPage() {
  const [marketId, setMarketId] = useState("");
  const [question, setQuestion] = useState("");

  const scanMutation = useMutation({ mutationFn: () => analysisApi.scan() });
  const analyzeMutation = useMutation({ mutationFn: (id: string) => analysisApi.market(id) });
  const askMutation = useMutation({ mutationFn: (q: string) => analysisApi.ask(q) });

  return (
    <div className="space-y-8 p-6">
      <div>
        <h1 className="text-xl font-semibold text-text-primary">AI Analysis</h1>
        <p className="mt-1 text-sm text-text-secondary">
          DeepSeek-powered pricing bias detection and market insights
        </p>
      </div>

      {/* Scan Markets */}
      <section className="rounded-lg border border-border-subtle bg-bg-card p-5">
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-sm font-semibold text-text-primary">Scan Markets</h2>
          <button
            onClick={() => scanMutation.mutate()}
            disabled={scanMutation.isPending}
            className="rounded bg-accent-gold px-4 py-1.5 text-xs font-semibold text-bg-base transition-colors hover:bg-accent-gold-hover disabled:opacity-50"
          >
            {scanMutation.isPending ? "Scanning…" : "Run Scan"}
          </button>
        </div>

        {scanMutation.error && (
          <div className="mb-3 rounded bg-loss-bg px-3 py-2 text-xs text-loss">
            {(scanMutation.error as Error).message}
          </div>
        )}

        {scanMutation.data?.opportunities && scanMutation.data.opportunities.length > 0 ? (
          <div className="space-y-2">
            {scanMutation.data.opportunities.map((opp, i) => (
              <div key={i} className="flex items-center justify-between rounded bg-bg-base px-4 py-3">
                <span className="max-w-[70%] truncate text-sm text-text-primary">{opp.question}</span>
                <BiasTag direction={opp.bias_direction} bps={opp.bias_bps} />
              </div>
            ))}
          </div>
        ) : scanMutation.isSuccess ? (
          <p className="text-xs text-text-muted">No significant opportunities found.</p>
        ) : null}
      </section>

      {/* Analyze Single Market */}
      <section className="rounded-lg border border-border-subtle bg-bg-card p-5">
        <h2 className="mb-4 text-sm font-semibold text-text-primary">Analyze Market</h2>
        <div className="flex gap-2">
          <input
            value={marketId}
            onChange={(e) => setMarketId(e.target.value)}
            placeholder="Enter market ID or condition ID…"
            className="flex-1 rounded border border-border-default bg-bg-base px-3 py-2 font-mono text-xs text-text-primary placeholder-text-muted outline-none focus:border-accent-gold"
          />
          <button
            onClick={() => analyzeMutation.mutate(marketId)}
            disabled={!marketId || analyzeMutation.isPending}
            className="rounded bg-accent-gold px-4 py-2 text-xs font-semibold text-bg-base transition-colors hover:bg-accent-gold-hover disabled:opacity-50"
          >
            Analyze
          </button>
        </div>

        {analyzeMutation.error && (
          <div className="mt-3 rounded bg-loss-bg px-3 py-2 text-xs text-loss">
            {(analyzeMutation.error as Error).message}
          </div>
        )}

        {analyzeMutation.data && (
          <div className="mt-4 space-y-3 rounded bg-bg-base p-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <span className="text-[10px] uppercase tracking-wider text-text-muted">AI Probability</span>
                <div className="mt-0.5 font-mono text-lg font-semibold text-text-primary">
                  {(analyzeMutation.data.ai_probability * 100).toFixed(1)}%
                </div>
              </div>
              <div>
                <span className="text-[10px] uppercase tracking-wider text-text-muted">Market Price</span>
                <div className="mt-0.5 font-mono text-lg font-semibold text-text-primary">
                  {(analyzeMutation.data.market_price * 100).toFixed(1)}%
                </div>
              </div>
            </div>
            <BiasTag direction={analyzeMutation.data.bias_direction} bps={analyzeMutation.data.bias_bps} />
            <div>
              <span className="text-[10px] uppercase tracking-wider text-text-muted">Reasoning</span>
              <p className="mt-1 text-sm leading-relaxed text-text-secondary">{analyzeMutation.data.reasoning}</p>
            </div>
          </div>
        )}
      </section>

      {/* Ask Question */}
      <section className="rounded-lg border border-border-subtle bg-bg-card p-5">
        <h2 className="mb-4 text-sm font-semibold text-text-primary">Ask a Question</h2>
        <div className="flex gap-2">
          <input
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder="Ask anything about markets…"
            className="flex-1 rounded border border-border-default bg-bg-base px-3 py-2 text-sm text-text-primary placeholder-text-muted outline-none focus:border-accent-gold"
            onKeyDown={(e) => e.key === "Enter" && question && askMutation.mutate(question)}
          />
          <button
            onClick={() => askMutation.mutate(question)}
            disabled={!question || askMutation.isPending}
            className="rounded bg-accent-gold px-4 py-2 text-xs font-semibold text-bg-base transition-colors hover:bg-accent-gold-hover disabled:opacity-50"
          >
            Ask
          </button>
        </div>

        {askMutation.data && (
          <div className="mt-4 rounded bg-bg-base p-4">
            <p className="whitespace-pre-wrap text-sm leading-relaxed text-text-secondary">
              {askMutation.data.answer}
            </p>
          </div>
        )}
      </section>
    </div>
  );
}
