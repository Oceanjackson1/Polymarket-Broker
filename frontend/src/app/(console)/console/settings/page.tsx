"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { authApi } from "@/lib/api";
import { Shimmer } from "@/components/ui/shimmer";

export default function SettingsPage() {
  const router = useRouter();
  const queryClient = useQueryClient();

  const user = useQuery({
    queryKey: ["auth", "me"],
    queryFn: () => authApi.me(),
    staleTime: 60_000,
  });

  const profile = user.data;

  // Display name editing
  const [editingName, setEditingName] = useState(false);
  const [nameValue, setNameValue] = useState("");

  useEffect(() => {
    if (profile) {
      setNameValue(profile.display_name || defaultDisplayName(profile));
    }
  }, [profile]);

  function defaultDisplayName(p: typeof profile) {
    if (!p) return "";
    if (p.wallet_address) {
      return `${p.wallet_address.slice(0, 6)}...${p.wallet_address.slice(-4)}`;
    }
    return p.email.split("@")[0];
  }

  const updateName = useMutation({
    mutationFn: (name: string) => authApi.updateProfile({ display_name: name }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["auth", "me"] });
      setEditingName(false);
    },
  });

  function handleSaveName() {
    if (!nameValue.trim()) return;
    updateName.mutate(nameValue.trim());
  }

  function handleLogout() {
    document.cookie =
      "pm_api_key=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT";
    router.push("/login");
  }

  // Derive display values
  const displayName = profile?.display_name || defaultDisplayName(profile);
  const emailOrWallet = profile?.wallet_address
    ? `${profile.wallet_address.slice(0, 6)}...${profile.wallet_address.slice(-4)}`
    : profile?.email ?? "\u2014";

  return (
    <div>
      <div className="mb-10">
        <h1 className="text-2xl font-semibold tracking-tight text-white">Settings</h1>
        <p className="mt-2 text-[15px] text-white/50">Manage your account.</p>
      </div>

      <div className="space-y-10">
        {/* Profile */}
        <section>
          <h2 className="mb-4 text-[13px] font-medium uppercase tracking-widest text-white/30">
            Profile
          </h2>
          <div className="rounded-2xl border border-white/20 bg-white/[0.03] divide-y divide-white/10">
            {user.isLoading ? (
              <div className="px-6 py-5">
                <Shimmer className="h-5 w-48" />
              </div>
            ) : (
              <>
                {/* Display Name — editable */}
                <div className="flex items-center justify-between px-6 py-4">
                  <span className="text-[15px] text-white/40">Display Name</span>
                  {editingName ? (
                    <div className="flex items-center gap-2">
                      <input
                        type="text"
                        value={nameValue}
                        onChange={(e) => setNameValue(e.target.value)}
                        onKeyDown={(e) => e.key === "Enter" && handleSaveName()}
                        className="rounded-lg border border-white/20 bg-white/[0.04] px-3 py-1.5 text-[15px] text-white outline-none focus:border-white/40 w-48"
                        autoFocus
                      />
                      <button
                        onClick={handleSaveName}
                        disabled={updateName.isPending}
                        className="rounded-lg bg-white px-3 py-1.5 text-[13px] font-medium text-black hover:bg-white/90 disabled:opacity-50"
                      >
                        {updateName.isPending ? "..." : "Save"}
                      </button>
                      <button
                        onClick={() => {
                          setEditingName(false);
                          setNameValue(profile?.display_name || defaultDisplayName(profile));
                        }}
                        className="text-[13px] text-white/30 hover:text-white/50"
                      >
                        Cancel
                      </button>
                    </div>
                  ) : (
                    <div className="flex items-center gap-3">
                      <span className="text-[15px] text-white">{displayName}</span>
                      <button
                        onClick={() => setEditingName(true)}
                        className="rounded-lg px-2.5 py-1 text-[13px] text-white/30 hover:text-white/60 hover:bg-white/[0.05] transition-colors"
                      >
                        Edit
                      </button>
                    </div>
                  )}
                </div>

                {/* Account identifier */}
                <div className="flex items-center justify-between px-6 py-4">
                  <span className="text-[15px] text-white/40">
                    {profile?.wallet_address ? "Wallet" : "Email"}
                  </span>
                  <span className="font-mono text-[15px] text-white">
                    {emailOrWallet}
                  </span>
                </div>

                {/* Full wallet address if applicable */}
                {profile?.wallet_address && (
                  <div className="flex items-center justify-between px-6 py-4">
                    <span className="text-[15px] text-white/40">Full Address</span>
                    <span className="font-mono text-[13px] text-white/50">
                      {profile.wallet_address}
                    </span>
                  </div>
                )}

                {/* Tier */}
                <div className="flex items-center justify-between px-6 py-4">
                  <span className="text-[15px] text-white/40">Tier</span>
                  <span className="text-[15px] text-white">
                    {(profile?.tier ?? "free").toUpperCase()}
                  </span>
                </div>

                {/* Joined */}
                <div className="flex items-center justify-between px-6 py-4">
                  <span className="text-[15px] text-white/40">Joined</span>
                  <span className="font-mono text-[15px] text-white">
                    {profile?.created_at
                      ? new Date(profile.created_at).toLocaleDateString()
                      : "\u2014"}
                  </span>
                </div>
              </>
            )}
          </div>

          {updateName.isError && (
            <p className="mt-3 text-[13px] text-red-400">
              Failed to update name. Please try again.
            </p>
          )}
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
