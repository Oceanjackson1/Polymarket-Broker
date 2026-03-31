export type WalletType = "metamask" | "okx";

export class WalletError extends Error {
  constructor(
    public readonly code: string,
    message: string
  ) {
    super(message);
    this.name = "WalletError";
  }
}

/**
 * Get the EIP-1193 provider for the requested wallet.
 */
function getProvider(wallet: WalletType): EIP1193Provider {
  if (typeof window === "undefined") {
    throw new WalletError("NO_WINDOW", "Not running in a browser environment.");
  }

  if (wallet === "okx") {
    const provider = (window as Window).okxwallet;
    if (!provider) {
      throw new WalletError(
        "NOT_INSTALLED",
        "OKX Wallet is not installed. Please install it from okx.com/web3"
      );
    }
    return provider;
  }

  // MetaMask
  const provider = (window as Window).ethereum;
  if (!provider || !provider.isMetaMask) {
    throw new WalletError(
      "NOT_INSTALLED",
      "MetaMask is not installed. Please install it from metamask.io"
    );
  }
  return provider;
}

/**
 * Request wallet connection and return the first account address.
 */
export async function connectWallet(wallet: WalletType): Promise<string> {
  const provider = getProvider(wallet);

  try {
    const accounts = (await provider.request({
      method: "eth_requestAccounts",
    })) as string[];

    if (!accounts || accounts.length === 0) {
      throw new WalletError("NO_ACCOUNTS", "No accounts returned by wallet.");
    }

    return accounts[0].toLowerCase();
  } catch (err: unknown) {
    if (err instanceof WalletError) throw err;

    // EIP-1193 user rejection error code
    const rpcErr = err as { code?: number };
    if (rpcErr.code === 4001) {
      throw new WalletError("USER_REJECTED", "Connection rejected by wallet.");
    }
    throw new WalletError(
      "CONNECT_FAILED",
      `Failed to connect wallet: ${err instanceof Error ? err.message : "Unknown error"}`
    );
  }
}

/**
 * Sign a message using personal_sign (EIP-191).
 */
export async function signMessage(
  wallet: WalletType,
  address: string,
  message: string
): Promise<string> {
  const provider = getProvider(wallet);

  try {
    // personal_sign params: [message_hex, address]
    const hexMessage =
      "0x" +
      Array.from(new TextEncoder().encode(message))
        .map((b) => b.toString(16).padStart(2, "0"))
        .join("");

    const signature = (await provider.request({
      method: "personal_sign",
      params: [hexMessage, address],
    })) as string;

    return signature;
  } catch (err: unknown) {
    if (err instanceof WalletError) throw err;

    const rpcErr = err as { code?: number };
    if (rpcErr.code === 4001) {
      throw new WalletError("USER_REJECTED", "Signature rejected.");
    }
    throw new WalletError(
      "SIGN_FAILED",
      `Failed to sign message: ${err instanceof Error ? err.message : "Unknown error"}`
    );
  }
}

/**
 * Full wallet login flow:
 * connect → challenge → sign → verify → return access token
 */
export async function walletLogin(wallet: WalletType): Promise<string> {
  // 1. Connect wallet
  const address = await connectWallet(wallet);

  // 2. Request challenge nonce from backend
  const challengeRes = await fetch("/api/v1/auth/wallet/challenge", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ wallet_address: address }),
  });

  if (!challengeRes.ok) {
    throw new WalletError(
      "CHALLENGE_FAILED",
      "Failed to get authentication challenge."
    );
  }

  const { nonce } = (await challengeRes.json()) as { nonce: string };

  // 3. Sign the challenge message (must match backend exactly)
  const message = `Sign in to Polydesk\nNonce: ${nonce}`;
  const signature = await signMessage(wallet, address, message);

  // 4. Verify signature with backend
  const verifyRes = await fetch("/api/v1/auth/wallet/verify", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ wallet_address: address, signature }),
  });

  if (!verifyRes.ok) {
    throw new WalletError(
      "VERIFY_FAILED",
      "Verification failed. Please try again."
    );
  }

  const { access_token } = (await verifyRes.json()) as {
    access_token: string;
  };

  return access_token;
}
