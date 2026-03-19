"use client";

import { useCallback } from "react";
import { useAccount, useSignMessage } from "wagmi";
import { useAuthContext } from "@/lib/providers";

export function useWallet() {
  const { address, isConnected } = useAccount();
  const { signMessageAsync } = useSignMessage();
  const { setAuth, api } = useAuthContext();

  const loginWithWallet = useCallback(async () => {
    if (!address) throw new Error("No wallet connected");

    // 1. Get challenge nonce
    const { nonce } = await api.walletChallenge(address);

    // 2. Sign nonce with wallet
    const signature = await signMessageAsync({ message: nonce });

    // 3. Verify and get JWT
    const res = await api.walletVerify(address, signature);
    setAuth({ id: address }, res.access_token);

    return res;
  }, [address, api, signMessageAsync, setAuth]);

  const bindWallet = useCallback(async () => {
    if (!address) throw new Error("No wallet connected");
    // Bind wallet uses the same challenge-response flow
    return loginWithWallet();
  }, [address, loginWithWallet]);

  return {
    address: address ?? null,
    isConnected,
    loginWithWallet,
    bindWallet,
    canTrade: isConnected && !!address,
  };
}
