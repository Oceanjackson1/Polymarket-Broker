"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import dynamic from "next/dynamic";
import { useAuthContext, useLocale } from "@/lib/providers";
import { useAuth } from "@/lib/hooks/useAuth";
import { useWallet } from "@/lib/hooks/useWallet";
import { shortenAddress } from "@/lib/utils";

const ConnectButton = dynamic(
  () => import("@rainbow-me/rainbowkit").then((mod) => mod.ConnectButton),
  { ssr: false }
);

type Tab = "account" | "wallet" | "apikeys";

export default function SettingsPage() {
  const { api, token, user } = useAuthContext();
  const { t } = useLocale();
  const { address, isConnected, bindWallet } = useWallet();
  const queryClient = useQueryClient();
  const [activeTab, setActiveTab] = useState<Tab>("account");
  const [newKeyName, setNewKeyName] = useState("");
  const [bindLoading, setBindLoading] = useState(false);
  const [bindError, setBindError] = useState("");

  const { data: keysData } = useQuery({
    queryKey: ["api-keys"],
    queryFn: () => api.listApiKeys(),
    enabled: !!token && activeTab === "apikeys",
  });

  const { data: usage } = useQuery({
    queryKey: ["usage"],
    queryFn: () => api.getUsage(),
    enabled: !!token && activeTab === "account",
  });

  const createKeyMutation = useMutation({
    mutationFn: () =>
      api.createApiKey(newKeyName || "Default", ["markets:read", "data:read", "orders:write"]),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["api-keys"] });
      setNewKeyName("");
    },
  });

  const revokeKeyMutation = useMutation({
    mutationFn: (keyId: string) => api.revokeApiKey(keyId),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["api-keys"] }),
  });

  const handleBind = async () => {
    setBindError("");
    setBindLoading(true);
    try {
      await bindWallet();
    } catch (err: unknown) {
      setBindError(err instanceof Error ? err.message : "Bind failed");
    } finally {
      setBindLoading(false);
    }
  };

  const tabs: { key: Tab; label: string }[] = [
    { key: "account", label: t("settings.account") },
    { key: "wallet", label: t("settings.wallet") },
    { key: "apikeys", label: t("settings.apiKeys") },
  ];

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">{t("nav.settings")}</h1>

      {/* Tabs */}
      <div className="flex gap-1 rounded-lg bg-zinc-900 p-1">
        {tabs.map((tab) => (
          <button
            key={tab.key}
            onClick={() => setActiveTab(tab.key)}
            className={`flex-1 rounded-md px-4 py-2 text-sm font-medium transition-colors ${
              activeTab === tab.key
                ? "bg-zinc-800 text-white"
                : "text-zinc-400 hover:text-white"
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Account */}
      {activeTab === "account" && (
        <div className="space-y-4 rounded-lg border border-zinc-800 bg-zinc-900 p-4">
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <span className="text-zinc-500">{t("auth.email")}</span>
              <div className="text-white">{user?.email || "—"}</div>
            </div>
            <div>
              <span className="text-zinc-500">{t("settings.tier")}</span>
              <div className="text-white">{user?.tier || "Free"}</div>
            </div>
          </div>
          {usage && (
            <div className="grid grid-cols-2 gap-4 border-t border-zinc-800 pt-4 text-sm">
              <div>
                <span className="text-zinc-500">API Calls Today</span>
                <div className="text-white">{usage.calls_today}</div>
              </div>
              <div>
                <span className="text-zinc-500">Remaining</span>
                <div className="text-white">{usage.calls_remaining}</div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Wallet */}
      {activeTab === "wallet" && (
        <div className="space-y-4 rounded-lg border border-zinc-800 bg-zinc-900 p-4">
          {isConnected && address ? (
            <div>
              <span className="text-sm text-zinc-500">Connected Wallet</span>
              <div className="text-white font-mono">{shortenAddress(address)}</div>
              <div className="mt-4">
                <ConnectButton />
              </div>
            </div>
          ) : (
            <div className="space-y-3">
              <p className="text-sm text-zinc-400">{t("auth.bindWallet")}</p>
              <ConnectButton />
              {isConnected && (
                <button
                  onClick={handleBind}
                  disabled={bindLoading}
                  className="rounded-md bg-purple-600 px-4 py-2 text-sm font-medium text-white hover:bg-purple-700 disabled:opacity-50"
                >
                  {bindLoading ? t("common.loading") : t("auth.bindWallet")}
                </button>
              )}
            </div>
          )}
          {bindError && (
            <div className="rounded-md bg-red-900/50 px-3 py-2 text-sm text-red-300">{bindError}</div>
          )}
        </div>
      )}

      {/* API Keys */}
      {activeTab === "apikeys" && (
        <div className="space-y-4">
          {/* Create key */}
          <div className="flex gap-2">
            <input
              value={newKeyName}
              onChange={(e) => setNewKeyName(e.target.value)}
              placeholder={t("settings.keyName")}
              className="flex-1 rounded-md border border-zinc-700 bg-zinc-800 px-3 py-2 text-sm text-white placeholder-zinc-500 focus:border-blue-500 focus:outline-none"
            />
            <button
              onClick={() => createKeyMutation.mutate()}
              disabled={createKeyMutation.isPending}
              className="rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
            >
              {t("settings.createKey")}
            </button>
          </div>

          {/* Show newly created key */}
          {createKeyMutation.data && (
            <div className="rounded-md bg-green-900/30 p-3">
              <p className="text-xs text-green-400">Key created. Copy it now — you won&apos;t see it again:</p>
              <code className="mt-1 block break-all text-sm text-green-300">
                {createKeyMutation.data.key}
              </code>
            </div>
          )}

          {/* Keys list */}
          <div className="rounded-lg border border-zinc-800 bg-zinc-900">
            {keysData?.keys && keysData.keys.length > 0 ? (
              <div className="divide-y divide-zinc-800">
                {keysData.keys.map((key) => (
                  <div key={key.id} className="flex items-center justify-between px-4 py-3">
                    <div>
                      <div className="text-sm text-white">{key.name}</div>
                      <div className="text-xs text-zinc-500">
                        {key.scopes.join(", ")} · {new Date(key.created_at).toLocaleDateString()}
                      </div>
                    </div>
                    <button
                      onClick={() => revokeKeyMutation.mutate(key.id)}
                      disabled={revokeKeyMutation.isPending}
                      className="rounded-md px-2 py-1 text-xs text-red-400 hover:bg-red-900/30"
                    >
                      {t("settings.revokeKey")}
                    </button>
                  </div>
                ))}
              </div>
            ) : (
              <div className="px-4 py-8 text-center text-sm text-zinc-500">
                {t("common.noData")}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
