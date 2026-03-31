interface EIP1193Provider {
  isMetaMask?: boolean;
  isOkxWallet?: boolean;
  request: (args: { method: string; params?: unknown[] }) => Promise<unknown>;
  on: (event: string, handler: (...args: unknown[]) => void) => void;
  removeListener: (event: string, handler: (...args: unknown[]) => void) => void;
}

interface Window {
  ethereum?: EIP1193Provider;
  okxwallet?: EIP1193Provider;
}
