"use client";

import { useEffect, useRef } from "react";
import { createChart, LineSeries, type IChartApi, type UTCTimestamp } from "lightweight-charts";

interface PriceChartProps {
  marketTitle: string;
  midPrice: number;
}

// 30 days of mock probability data (0–1 range)
const MOCK_DATA = (() => {
  const base = Date.UTC(2026, 1, 17) / 1000; // Feb 17 2026 in seconds
  const day = 86400;
  const prices = [
    0.48, 0.5, 0.47, 0.52, 0.55, 0.53, 0.58, 0.56, 0.6, 0.59, 0.62, 0.61,
    0.65, 0.63, 0.67, 0.66, 0.64, 0.68, 0.7, 0.69, 0.72, 0.71, 0.69, 0.73,
    0.74, 0.72, 0.75, 0.74, 0.76, 0.75,
  ];
  return prices.map((value, i) => ({ time: (base + i * day) as UTCTimestamp, value }));
})();

export default function PriceChart({ marketTitle, midPrice }: PriceChartProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);

  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;

    const chart = createChart(el, {
      layout: {
        background: { color: "#111827" },
        textColor: "#94A3B8",
        fontFamily: "var(--font-jetbrains-mono, monospace)",
        fontSize: 11,
      },
      grid: {
        vertLines: { color: "#1E293B" },
        horzLines: { color: "#1E293B" },
      },
      crosshair: {
        vertLine: { color: "#334155", width: 1, style: 2 },
        horzLine: { color: "#334155", width: 1, style: 2 },
      },
      rightPriceScale: {
        borderColor: "#1E293B",
        textColor: "#64748B",
      },
      timeScale: {
        borderColor: "#1E293B",
        timeVisible: true,
        secondsVisible: false,
      },
      width: el.clientWidth,
      height: el.clientHeight,
    });

    chartRef.current = chart;

    const series = chart.addSeries(LineSeries, {
      color: "#F59E0B",
      lineWidth: 2,
      priceLineVisible: true,
      priceLineColor: "#F59E0B",
      priceLineWidth: 1,
      lastValueVisible: true,
      crosshairMarkerVisible: true,
      crosshairMarkerRadius: 4,
      crosshairMarkerBackgroundColor: "#F59E0B",
    });

    series.setData(MOCK_DATA);
    chart.timeScale().fitContent();

    // Resize observer
    const ro = new ResizeObserver(() => {
      if (el) chart.resize(el.clientWidth, el.clientHeight);
    });
    ro.observe(el);

    return () => {
      ro.disconnect();
      chart.remove();
      chartRef.current = null;
    };
  }, []);

  return (
    <div className="flex h-full flex-col">
      {/* Panel header */}
      <div className="flex items-center justify-between border-b border-border-subtle px-4 py-2">
        <div className="flex items-center gap-3">
          <span className="text-xs font-semibold uppercase tracking-wider text-text-muted">
            Price Chart
          </span>
          <span className="max-w-[260px] truncate text-sm text-text-primary">
            {marketTitle}
          </span>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs text-text-muted">Mid</span>
          <span className="font-mono text-lg font-semibold text-accent-gold">
            {midPrice.toFixed(3)}
          </span>
        </div>
      </div>
      {/* Chart canvas */}
      <div ref={containerRef} className="min-h-0 flex-1" />
    </div>
  );
}
