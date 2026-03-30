"use client";

import { useRouter } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { authApi } from "@/lib/api";
import { Shimmer } from "@/components/ui/shimmer";

export default function SettingsPage() {
  const router = useRouter();

  const user = useQuery({
    queryKey: ["auth", "me"],
    queryFn: () => authApi.me(),
    staleTime: 60_000,
  });

  const profile = user.data;

  function handleLogout() {
    document.cookie =
      "pm_api_key=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT";
    router.push("/login");
  }

  return (
    <div>
      <div className="mb-10">
        <h1 className="text-2xl font-semibold tracking-tight text-white">Settings</h1>
        <p className="mt-2 text-[15px] text-white/50">Manage your account.</p>
      </div>

      <div className="space-y-10">
        {/* Account Info */}
        <section>
          <h2 className="mb-4 text-[13px] font-medium uppercase tracking-widest text-white/30">
            Account
          </h2>
          <div className="rounded-2xl border border-white/20 bg-white/[0.03] divide-y divide-white/10">
            {user.isLoading ? (
              <div className="px-6 py-5">
                <Shimmer className="h-5 w-48" />
              </div>
            ) : user.error ? (
              <div className="px-6 py-5 text-[15px] text-red-400">Failed to load profile</div>
            ) : (
              <>
                {[
                  { label: "Email", value: profile?.email ?? "\u2014" },
                  { label: "User ID", value: profile?.id ?? "\u2014" },
                  { label: "Tier", value: (profile?.tier ?? "free").toUpperCase() },
                  {
                    label: "Joined",
                    value: profile?.created_at
                      ? new Date(profile.created_at).toLocaleDateString()
                      : "\u2014",
                  },
                ].map((row) => (
                  <div key={row.label} className="flex items-center justify-between px-6 py-4">
                    <span className="text-[15px] text-white/40">{row.label}</span>
                    <span className="font-mono text-[15px] text-white">{row.value}</span>
                  </div>
                ))}
              </>
            )}
          </div>
        </section>

        {/* Session */}
        <section>
          <h2 className="mb-4 text-[13px] font-medium uppercase tracking-widest text-white/30">
            Session
          </h2>
          <div className="rounded-2xl border border-white/20 bg-white/[0.03] px-6 py-5">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-[15px] font-medium text-white">Log out</p>
                <p className="mt-1 text-[14px] text-white/40">
                  Clear your session and return to the login page.
                </p>
              </div>
              <button
                onClick={handleLogout}
                className="rounded-full border border-white/20 px-5 py-2 text-[14px] font-medium text-white/60 transition-colors hover:border-red-500/40 hover:text-red-400"
              >
                Log out
              </button>
            </div>
          </div>
        </section>
      </div>
    </div>
  );
}
