"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import dynamic from "next/dynamic";
import { useWallet } from "@/lib/hooks/useWallet";
import { useLocale } from "@/lib/providers";

const ConnectButton = dynamic(
  () => import("@rainbow-me/rainbowkit").then((mod) => mod.ConnectButton),
  { ssr: false }
);

export default function WalletLoginButton() {
  const { isConnected, loginWithWallet } = useWallet();
  const { t } = useLocale();
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleWalletLogin = async () => {
    setError("");
    setLoading(true);
    try {
      await loginWithWallet();
      router.push("/markets");
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Wallet login failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-3">
      {error && (
        <div className="rounded-md bg-red-900/50 px-3 py-2 text-sm text-red-300">
          {error}
        </div>
      )}

      {!isConnected ? (
        <div className="flex justify-center">
          <ConnectButton />
        </div>
      ) : (
        <button
          onClick={handleWalletLogin}
          disabled={loading}
          className="w-full rounded-md bg-purple-600 px-4 py-2 text-sm font-medium text-white hover:bg-purple-700 disabled:opacity-50"
        >
          {loading ? t("common.loading") : t("auth.connectWallet")}
        </button>
      )}
    </div>
  );
}
