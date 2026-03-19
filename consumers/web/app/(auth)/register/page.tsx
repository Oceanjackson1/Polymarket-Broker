import RegisterForm from "@/components/auth/RegisterForm";
import WalletLoginButton from "@/components/auth/WalletLoginButton";

export default function RegisterPage() {
  return (
    <div className="space-y-6">
      <RegisterForm />
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
