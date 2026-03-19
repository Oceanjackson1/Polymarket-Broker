import WalletLoginButton from "@/components/auth/WalletLoginButton";

export default function WalletPage() {
  return (
    <div className="space-y-4">
      <h1 className="text-xl font-bold text-white">Connect Wallet</h1>
      <p className="text-sm text-zinc-400">
        Connect your wallet to sign in and start trading on Polymarket.
      </p>
      <WalletLoginButton />
    </div>
  );
}
