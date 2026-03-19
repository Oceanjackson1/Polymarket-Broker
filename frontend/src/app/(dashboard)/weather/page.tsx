"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { weatherApi } from "@/lib/api";

function BiasTag({ direction, bps }: { direction: string | null; bps: number | null }) {
  if (!direction || !bps) return null;
  const isUp = direction === "FORECAST_HIGHER";
  const isDown = direction === "MARKET_HIGHER";
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

export default function WeatherPage() {
  const [selectedDate, setSelectedDate] = useState<string | null>(null);
  const [selectedCity, setSelectedCity] = useState<string | null>(null);

  const { data: dates, isLoading: datesLoading } = useQuery({
    queryKey: ["weather-dates"],
    queryFn: () => weatherApi.dates(),
  });

  const activeDate = selectedDate || dates?.[0]?.date || null;

  const { data: cities } = useQuery({
    queryKey: ["weather-cities", activeDate],
    queryFn: () => weatherApi.cities(activeDate!),
    enabled: !!activeDate,
  });

  const { data: fusion } = useQuery({
    queryKey: ["weather-fusion", activeDate, selectedCity],
    queryFn: () => weatherApi.fusion(activeDate!, selectedCity!),
    enabled: !!activeDate && !!selectedCity,
  });

  return (
    <div className="p-6">
      <div className="mb-8">
        <h1 className="text-xl font-semibold text-text-primary">Weather Fusion</h1>
        <p className="mt-1 text-sm text-text-secondary">
          Ensemble forecast probability × Polymarket temperature market price × bias signal
        </p>
      </div>

      {/* Date selector */}
      {datesLoading ? (
        <div className="mb-6 flex gap-2">
          {[0, 1, 2].map((i) => (
            <div key={i} className="h-8 w-36 animate-pulse rounded bg-bg-elevated" />
          ))}
        </div>
      ) : dates && dates.length > 0 ? (
        <div className="mb-6 flex flex-wrap gap-2">
          {dates.map((d) => (
            <button
              key={d.date}
              onClick={() => {
                setSelectedDate(d.date);
                setSelectedCity(null);
              }}
              className={`rounded-full px-4 py-1.5 text-xs font-medium transition-colors ${
                activeDate === d.date
                  ? "bg-accent-gold text-bg-base"
                  : "border border-border-default bg-bg-card text-text-secondary hover:border-accent-gold hover:text-text-primary"
              }`}
            >
              {d.date} · {d.city_count} cities
            </button>
          ))}
        </div>
      ) : (
        <div className="rounded-lg border border-border-subtle bg-bg-card p-8 text-center text-sm text-text-muted">
          No weather markets available. Collector may still be initializing.
        </div>
      )}

      {/* City list */}
      {cities && cities.length > 0 && !selectedCity && (
        <div className="space-y-2">
          {cities.map((city) => (
            <button
              key={city.city}
              onClick={() => setSelectedCity(city.city)}
              className="flex w-full items-center justify-between rounded-lg border border-border-subtle bg-bg-card px-5 py-4 text-left transition-colors hover:border-accent-gold"
            >
              <span className="text-sm font-medium capitalize text-text-primary">{city.city}</span>
              <div className="flex items-center gap-3">
                {city.max_bias_range && (
                  <span className="font-mono text-xs text-text-muted">at {city.max_bias_range}</span>
                )}
                <BiasTag direction={city.max_bias_direction} bps={city.max_bias_bps} />
              </div>
            </button>
          ))}
        </div>
      )}

      {/* Fusion detail */}
      {fusion && selectedCity && (
        <div className="space-y-4">
          <button
            onClick={() => setSelectedCity(null)}
            className="text-xs text-accent-gold hover:underline"
          >
            ← Back to cities
          </button>

          {fusion.stale && (
            <div className="rounded-md bg-warning/10 px-4 py-2 text-xs text-warning">
              ⚠ Data may be stale
            </div>
          )}

          <div className="rounded-lg border border-border-subtle bg-bg-card p-5">
            <h2 className="text-base font-semibold capitalize text-text-primary">{fusion.city}</h2>
            <p className="mt-0.5 text-xs text-text-muted">
              {fusion.date} · {fusion.temp_unit === "fahrenheit" ? "°F" : "°C"}
            </p>

            {/* Temperature bin bars */}
            <div className="mt-5 space-y-2.5">
              {fusion.temp_bins.map((bin, i) => {
                const maxProb = Math.max(
                  ...fusion.temp_bins.map((b) => Math.max(b.market_prob, b.forecast_prob)),
                  0.01
                );
                return (
                  <div key={i} className="flex items-center gap-3">
                    <span className="w-28 text-right font-mono text-xs text-text-muted">{bin.range}</span>
                    <div className="flex-1 space-y-1">
                      <div className="flex items-center gap-2">
                        <div
                          className="h-2.5 rounded-sm bg-info-blue/50"
                          style={{ width: `${(bin.market_prob / maxProb) * 100}%`, minWidth: "2px" }}
                        />
                        <span className="font-mono text-[10px] text-text-muted">
                          {(bin.market_prob * 100).toFixed(1)}%
                        </span>
                      </div>
                      <div className="flex items-center gap-2">
                        <div
                          className="h-2.5 rounded-sm bg-profit/50"
                          style={{ width: `${(bin.forecast_prob / maxProb) * 100}%`, minWidth: "2px" }}
                        />
                        <span className="font-mono text-[10px] text-text-muted">
                          {(bin.forecast_prob * 100).toFixed(1)}%
                        </span>
                      </div>
                    </div>
                    <BiasTag direction={bin.bias_direction} bps={bin.bias_bps} />
                  </div>
                );
              })}
            </div>

            {/* Legend */}
            <div className="mt-4 flex gap-5 text-[10px] text-text-muted">
              <span className="flex items-center gap-1.5">
                <span className="inline-block h-2 w-2 rounded-sm bg-info-blue/50" /> Market Price
              </span>
              <span className="flex items-center gap-1.5">
                <span className="inline-block h-2 w-2 rounded-sm bg-profit/50" /> Forecast
              </span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
