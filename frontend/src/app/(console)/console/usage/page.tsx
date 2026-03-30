"use client";

import { useQuery } from "@tanstack/react-query";
import { authApi, developerApi } from "@/lib/api";
import { Shimmer } from "@/components/ui/shimmer";

const TIER_LIMITS: Record<string, number> = {
  free: 500,
  pro: 0,
  enterprise: 0,
};

export default function UsagePage() {
  const user = useQuery({
    queryKey: ["auth", "me"],
    queryFn: () => authApi.me(),
    staleTime: 60_000,
  });

  const usage = useQuery({
    queryKey: ["developer", "usage"],
    queryFn: () => developerApi.usage(),
    staleTime: 30_000,
  });

  const tier = user.data?.tier ?? "free";
  const dailyLimit = TIER_LIMITS[tier] ?? 500;
  const callsToday = usage.data?.calls_today ?? 0;
  const remaining = usage.data?.calls_remaining;
  const isUnlimited = dailyLimit === 0;

  return (
    <div>
      <div className="mb-10">
        <h1 className="text-2xl font-semibold tracking-tight text-white">API Usage</h1>
        <p className="mt-2 text-[15px] text-white/50">Monitor your API usage and quota.</p>
      </div>

      {/* Stats */}
      <div className="mb-10 grid grid-cols-3 gap-5">
        <div className="rounded-2xl border border-white/20 bg-white/[0.03] p-6">
          <p className="text-[14px] text-white/40">Calls Today</p>
          {usage.isLoading ? (
            <Shimmer className="mt-3 h-8 w-20" />
          ) : (
            <p className="mt-2 font-mono text-3xl font-semibold text-white">
              {callsToday.toLocaleString()}
            </p>
          )}
        </div>
        <div className="rounded-2xl border border-white/20 bg-white/[0.03] p-6">
          <p className="text-[14px] text-white/40">Remaining</p>
          {usage.isLoading ? (
            <Shimmer className="mt-3 h-8 w-20" />
          ) : (
            <p className="mt-2 font-mono text-3xl font-semibold text-white">
              {isUnlimited ? "Unlimited" : remaining?.toLocaleString() ?? "\u2014"}
            </p>
          )}
        </div>
        <div className="rounded-2xl border border-white/20 bg-white/[0.03] p-6">
          <p className="text-[14px] text-white/40">Plan</p>
          {user.isLoading ? (
            <Shimmer className="mt-3 h-8 w-20" />
          ) : (
            <p className="mt-2 text-3xl font-semibold text-white capitalize">{tier}</p>
          )}
        </div>
      </div>

      {/* Rate Limits */}
      <div className="rounded-2xl border border-white/20 bg-white/[0.03]">
        <div className="border-b border-white/10 px-6 py-4">
          <h2 className="text-[15px] font-medium text-white">Rate Limits by Plan</h2>
        </div>
        <table className="w-full text-[14px]">
          <thead>
            <tr className="border-b border-white/10 text-left text-[13px] text-white/30">
              <th className="px-6 py-3.5 font-medium">Plan</th>
              <th className="px-6 py-3.5 font-medium">Daily API Calls</th>
              <th className="px-6 py-3.5 font-medium">AI Analysis</th>
              <th className="px-6 py-3.5 font-medium">Broker Fee</th>
            </tr>
          </thead>
          <tbody className="text-white/50">
            {[
              { plan: "Free", calls: "500 / day", ai: "10 / day", fee: "10 bps", current: tier === "free" },
              { plan: "Pro", calls: "Unlimited", ai: "Unlimited", fee: "5 bps", current: tier === "pro" },
              { plan: "Enterprise", calls: "Unlimited", ai: "Unlimited", fee: "0 bps", current: tier === "enterprise" },
            ].map((row) => (
              <tr
                key={row.plan}
                className={`border-b border-white/10 last:border-0 ${row.current ? "bg-white/[0.03]" : ""}`}
              >
                <td className="px-6 py-3.5 font-medium text-white">
                  {row.plan}
                  {row.current && (
                    <span className="ml-2 rounded-full bg-white/10 px-2 py-0.5 text-[11px] text-white/60">
                      CURRENT
                    </span>
                  )}
                </td>
                <td className="px-6 py-3.5 font-mono">{row.calls}</td>
                <td className="px-6 py-3.5 font-mono">{row.ai}</td>
                <td className="px-6 py-3.5 font-mono">{row.fee}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Upgrade CTA */}
      {tier === "free" && (
        <div className="mt-8 rounded-2xl border border-white/20 bg-white/[0.03] p-6">
          <h3 className="text-[15px] font-medium text-white">Upgrade to Pro</h3>
          <p className="mt-1.5 text-[15px] text-white/40">
            Get unlimited API calls, unlimited AI analysis, strategies, webhooks, and lower fees.
          </p>
          <a
            href="/pricing"
            className="mt-4 inline-block rounded-full bg-white px-6 py-2.5 text-[14px] font-medium text-black transition-all hover:bg-white/90 active:scale-[0.98]"
          >
            View Pricing
          </a>
        </div>
      )}
    </div>
  );
}
