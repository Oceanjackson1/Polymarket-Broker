"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { walletLogin, WalletError, type WalletType } from "@/lib/wallet";

const ALL_SCOPES = [
  "data:read", "markets:read", "orders:write", "portfolio:read",
  "analysis:read", "strategies:execute", "webhooks:write",
];

export default function LoginPage() {
  const router = useRouter();
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState<WalletType | null>(null);

  async function createKeyAndRedirect(accessToken: string) {
    const keyRes = await fetch("/api/v1/auth/keys", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${accessToken}`,
      },
      body: JSON.stringify({ name: "browser-session", scopes: ALL_SCOPES }),
    });

    if (!keyRes.ok) {
      let msg = "Failed to create API key";
      try {
        const body = (await keyRes.json()) as { detail?: string };
        msg = body.detail ?? msg;
      } catch {}
      throw new Error(msg);
    }

    const keyData = (await keyRes.json()) as { key: string };
    document.cookie = `pm_api_key=${encodeURIComponent(keyData.key)}; path=/; SameSite=Lax`;
    router.push("/console");
  }

  async function handleWalletLogin(wallet: WalletType) {
    setError(null);
    setLoading(wallet);
    try {
      const accessToken = await walletLogin(wallet);
      await createKeyAndRedirect(accessToken);
    } catch (err) {
      if (err instanceof WalletError) {
        setError(err.message);
      } else if (err instanceof Error) {
        setError(err.message);
      } else {
        setError("An unexpected error occurred.");
      }
    } finally {
      setLoading(null);
    }
  }

  const isDisabled = loading !== null;

  return (
    <section className="flex min-h-[calc(100vh-4rem)] items-center justify-center bg-black px-4 py-16">
      <div className="w-full max-w-md">
        <div className="rounded-2xl border border-white/[0.08] bg-white/[0.02] p-8">
          <div className="mb-8 text-center">
            <h1 className="text-2xl font-semibold text-white">
              Sign in to Polydesk
            </h1>
            <p className="mt-2 text-[15px] text-white/50">
              Connect your wallet to continue.
            </p>
          </div>

          <div className="space-y-3">
            {/* MetaMask */}
            <button
              onClick={() => handleWalletLogin("metamask")}
              disabled={isDisabled}
              className="flex w-full items-center justify-center gap-3 rounded-xl border border-white/[0.08] bg-white/[0.04] px-4 py-3 text-[15px] font-medium text-white transition-all hover:bg-white/[0.08] active:scale-[0.98] disabled:cursor-not-allowed disabled:opacity-50"
            >
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img src="https://upload.wikimedia.org/wikipedia/commons/3/36/MetaMask_Fox.svg" alt="MetaMask" width="24" height="24" />
              {loading === "metamask" ? "Connecting..." : "Continue with MetaMask"}
            </button>

            {/* OKX Wallet */}
            <button
              onClick={() => handleWalletLogin("okx")}
              disabled={isDisabled}
              className="flex w-full items-center justify-center gap-3 rounded-xl border border-white/[0.08] bg-white/[0.04] px-4 py-3 text-[15px] font-medium text-white transition-all hover:bg-white/[0.08] active:scale-[0.98] disabled:cursor-not-allowed disabled:opacity-50"
            >
              <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
                <rect width="20" height="20" rx="4" fill="white" />
                <rect x="3.5" y="3.5" width="5" height="5" rx="0.5" fill="black" />
                <rect x="7.5" y="7.5" width="5" height="5" rx="0.5" fill="black" />
                <rect x="11.5" y="3.5" width="5" height="5" rx="0.5" fill="black" />
                <rect x="3.5" y="11.5" width="5" height="5" rx="0.5" fill="black" />
                <rect x="11.5" y="11.5" width="5" height="5" rx="0.5" fill="black" />
              </svg>
              {loading === "okx" ? "Connecting..." : "Continue with OKX Wallet"}
            </button>
          </div>

          {error && (
            <p className="mt-5 rounded-xl border border-red-500/20 bg-red-500/10 px-4 py-2.5 text-sm text-red-400">
              {error}
            </p>
          )}

          <p className="mt-6 text-center text-xs text-white/25">
            Free plan: 500 API calls/day · No credit card required
          </p>
        </div>
      </div>
    </section>
  );
}
