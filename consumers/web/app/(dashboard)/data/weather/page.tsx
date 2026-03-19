"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { useAuthContext, useLocale } from "@/lib/providers";
import BiasSignalBadge from "@/components/data/BiasSignalBadge";
import StaleWarning from "@/components/data/StaleWarning";

export default function WeatherDataPage() {
  const { api, token } = useAuthContext();
  const { t } = useLocale();
  const [selectedDate, setSelectedDate] = useState<string | null>(null);
  const [selectedCity, setSelectedCity] = useState<string | null>(null);

  const { data: dates } = useQuery({
    queryKey: ["weather-dates"],
    queryFn: () => api.getWeatherDates(),
    enabled: !!token,
  });

  const activeDate = selectedDate || dates?.[0]?.date || null;

  const { data: cities } = useQuery({
    queryKey: ["weather-cities", activeDate],
    queryFn: () => api.getWeatherCities(activeDate!),
    enabled: !!activeDate && !!token,
  });

  const { data: fusion } = useQuery({
    queryKey: ["weather-fusion", activeDate, selectedCity],
    queryFn: () => api.getWeatherFusion(activeDate!, selectedCity!),
    enabled: !!activeDate && !!selectedCity && !!token,
  });

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">{t("nav.weather")} Fusion</h1>
        <p className="mt-1 text-sm text-zinc-400">Forecast probability x market price x bias</p>
      </div>

      {/* Date tabs */}
      {dates && dates.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {dates.map((d) => (
            <button
              key={d.date}
              onClick={() => { setSelectedDate(d.date); setSelectedCity(null); }}
              className={`rounded-full px-3 py-1 text-xs font-medium ${
                activeDate === d.date
                  ? "bg-blue-600 text-white"
                  : "bg-zinc-800 text-zinc-400 hover:bg-zinc-700"
              }`}
            >
              {d.date} ({d.city_count} cities)
            </button>
          ))}
        </div>
      )}

      {/* Cities list */}
      {cities && cities.length > 0 && !selectedCity && (
        <div className="space-y-2">
          {cities.map((city) => (
            <button
              key={city.city}
              onClick={() => setSelectedCity(city.city)}
              className="flex w-full items-center justify-between rounded-lg border border-zinc-800 bg-zinc-900 p-4 text-left hover:border-zinc-600"
            >
              <span className="text-sm font-medium text-white capitalize">{city.city}</span>
              <div className="flex items-center gap-3">
                {city.max_bias_range && (
                  <span className="text-xs text-zinc-500">at {city.max_bias_range}</span>
                )}
                {city.max_bias_direction && city.max_bias_bps != null && (
                  <BiasSignalBadge direction={city.max_bias_direction} bps={city.max_bias_bps} />
                )}
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
            className="text-sm text-blue-400 hover:text-blue-300"
          >
            ← Back to cities
          </button>

          <StaleWarning stale={fusion.stale} />

          <div className="rounded-lg border border-zinc-800 bg-zinc-900 p-4">
            <h3 className="mb-1 text-lg font-bold capitalize text-white">{fusion.city}</h3>
            <p className="mb-4 text-xs text-zinc-500">{fusion.date} · {fusion.temp_unit}</p>

            {/* Temperature bins chart */}
            <div className="space-y-2">
              {fusion.temp_bins.map((bin, i) => {
                const maxProb = Math.max(
                  ...fusion.temp_bins.map((b) => Math.max(b.market_prob, b.forecast_prob)),
                  0.01
                );
                return (
                  <div key={i} className="flex items-center gap-3">
                    <span className="w-24 text-right text-xs text-zinc-400">{bin.range}</span>
                    <div className="flex-1 space-y-0.5">
                      <div className="flex items-center gap-2">
                        <div
                          className="h-3 rounded-sm bg-blue-500/60"
                          style={{ width: `${(bin.market_prob / maxProb) * 100}%` }}
                        />
                        <span className="text-xs text-zinc-500">{(bin.market_prob * 100).toFixed(1)}%</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <div
                          className="h-3 rounded-sm bg-green-500/60"
                          style={{ width: `${(bin.forecast_prob / maxProb) * 100}%` }}
                        />
                        <span className="text-xs text-zinc-500">{(bin.forecast_prob * 100).toFixed(1)}%</span>
                      </div>
                    </div>
                    <BiasSignalBadge direction={bin.bias_direction} bps={bin.bias_bps} />
                  </div>
                );
              })}
            </div>

            <div className="mt-3 flex gap-4 text-xs text-zinc-500">
              <span className="flex items-center gap-1">
                <span className="h-2 w-2 rounded-sm bg-blue-500/60" /> {t("data.marketPrice")}
              </span>
              <span className="flex items-center gap-1">
                <span className="h-2 w-2 rounded-sm bg-green-500/60" /> {t("data.forecast")}
              </span>
            </div>
          </div>
        </div>
      )}

      {(!dates || dates.length === 0) && (
        <div className="py-12 text-center text-zinc-500">{t("common.noData")}</div>
      )}
    </div>
  );
}
