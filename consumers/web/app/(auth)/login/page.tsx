import LoginForm from "@/components/auth/LoginForm";
import WalletLoginButton from "@/components/auth/WalletLoginButton";

export default function LoginPage() {
  return (
    <div className="space-y-6">
      <LoginForm />
      <div className="relative">
        <div className="absolute inset-0 flex items-center">
          <div className="w-full border-t border-zinc-700" />
        </div>
        <div className="relative flex justify-center text-sm">
          <span className="bg-zinc-900 px-2 text-zinc-500">or</span>
        </div>
      </div>
      <WalletLoginButton />
    </div>
  );
}
