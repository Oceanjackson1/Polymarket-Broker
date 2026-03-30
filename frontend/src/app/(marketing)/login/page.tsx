"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { authApi, ApiError } from "@/lib/api";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      // Step 1: Login → get access token
      const auth = await authApi.login({ email, password });
      const accessToken = auth.access_token;

      // Step 2: Create an API key using the Bearer token
      const keyRes = await fetch("/api/v1/auth/keys", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${accessToken}`,
        },
        body: JSON.stringify({
          name: "browser-session",
          scopes: ["data:read", "markets:read", "orders:write", "portfolio:read", "analysis:read", "strategies:execute", "webhooks:write"],
        }),
      });

      if (!keyRes.ok) {
        let msg = "Failed to create API key";
        try {
          const body = await keyRes.json() as { detail?: string };
          msg = body.detail ?? msg;
        } catch {
          // ignore
        }
        throw new Error(msg);
      }

      const keyData = await keyRes.json() as { key: string };

      // Step 3: Store API key in cookie
      document.cookie = `pm_api_key=${encodeURIComponent(keyData.key)}; path=/; SameSite=Lax`;

      // Step 4: Redirect to dashboard
      router.push("/console");
    } catch (err) {
      if (err instanceof ApiError) {
        if (err.status === 401 || err.status === 422) {
          setError("Invalid email or password.");
        } else {
          setError(err.message);
        }
      } else if (err instanceof Error) {
        setError(err.message);
      } else {
        setError("An unexpected error occurred.");
      }
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="flex min-h-[calc(100vh-4rem)] items-center justify-center bg-black px-4 py-16">
      <div className="w-full max-w-md">
        <div className="rounded-2xl border border-white/[0.08] bg-white/[0.02] p-8">
          <div className="mb-8 text-center">
            <h1 className="text-2xl font-semibold text-white">
              Sign in to Polydesk
            </h1>
            <p className="mt-2 text-[15px] text-white/60">
              Don&apos;t have an account?{" "}
              <Link
                href="/register"
                className="text-white transition-colors hover:text-white/80"
              >
                Create one free
              </Link>
            </p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-5">
            <div>
              <label
                htmlFor="email"
                className="mb-1.5 block text-[15px] font-medium text-white/60"
              >
                Email
              </label>
              <input
                id="email"
                type="email"
                autoComplete="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="you@example.com"
                className="w-full rounded-xl border border-white/[0.08] bg-white/[0.04] px-4 py-2.5 text-[15px] text-white placeholder-white/25 outline-none transition-colors focus:border-white/20 focus:ring-0"
              />
            </div>

            <div>
              <label
                htmlFor="password"
                className="mb-1.5 block text-[15px] font-medium text-white/60"
              >
                Password
              </label>
              <input
                id="password"
                type="password"
                autoComplete="current-password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                className="w-full rounded-xl border border-white/[0.08] bg-white/[0.04] px-4 py-2.5 text-[15px] text-white placeholder-white/25 outline-none transition-colors focus:border-white/20 focus:ring-0"
              />
            </div>

            {error && (
              <p className="rounded-xl border border-red-500/20 bg-red-500/10 px-4 py-2.5 text-sm text-red-400">
                {error}
              </p>
            )}

            <button
              type="submit"
              disabled={loading}
              className="w-full rounded-full bg-white px-4 py-2.5 text-[15px] font-medium text-black transition-all hover:bg-white/90 active:scale-[0.98] disabled:cursor-not-allowed disabled:opacity-50"
            >
              {loading ? "Signing in…" : "Sign in"}
            </button>
          </form>
        </div>
      </div>
    </section>
  );
}
