"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { authApi, type ApiKeyListItem } from "@/lib/api";
import { Shimmer } from "@/components/ui/shimmer";

function CopyButton({ text }: { text: string }) {
  const [copied, setCopied] = useState(false);

  function handleCopy() {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }

  return (
    <button
      onClick={handleCopy}
      className={`flex items-center gap-1.5 rounded-full px-3 py-1.5 text-[13px] transition-all ${
        copied
          ? "bg-emerald-500/10 text-emerald-400"
          : "text-white/40 hover:text-white hover:bg-white/10"
      }`}
    >
      {copied ? (
        <>
          <svg className="h-3.5 w-3.5" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M3 8.5l3 3 7-7" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
          Copied
        </>
      ) : (
        <>
          <svg className="h-3.5 w-3.5" viewBox="0 0 16 16" fill="currentColor">
            <path d="M0 6.75C0 5.784.784 5 1.75 5h1.5a.75.75 0 0 1 0 1.5h-1.5a.25.25 0 0 0-.25.25v7.5c0 .138.112.25.25.25h7.5a.25.25 0 0 0 .25-.25v-1.5a.75.75 0 0 1 1.5 0v1.5A1.75 1.75 0 0 1 9.25 16h-7.5A1.75 1.75 0 0 1 0 14.25ZM5 1.75C5 .784 5.784 0 6.75 0h7.5C15.216 0 16 .784 16 1.75v7.5A1.75 1.75 0 0 1 14.25 11h-7.5A1.75 1.75 0 0 1 5 9.25Zm1.75-.25a.25.25 0 0 0-.25.25v7.5c0 .138.112.25.25.25h7.5a.25.25 0 0 0 .25-.25v-7.5a.25.25 0 0 0-.25-.25Z" />
          </svg>
          Copy
        </>
      )}
    </button>
  );
}

function KeyDisplay({ value }: { value: string }) {
  const [revealed, setRevealed] = useState(false);
  const masked = value.slice(0, 14) + "\u2022\u2022\u2022\u2022\u2022\u2022\u2022\u2022" + value.slice(-4);

  return (
    <div className="flex items-center rounded-xl bg-white/[0.03] border border-white/10 overflow-hidden">
      <code className="flex-1 truncate px-4 py-2.5 font-mono text-[14px] text-white/60 select-all">
        {revealed ? value : masked}
      </code>
      <div className="flex items-center border-l border-white/10">
        <button
          onClick={() => setRevealed(!revealed)}
          className="px-3 py-2.5 text-white/30 hover:text-white/60 transition-colors"
          title={revealed ? "Hide" : "Reveal"}
        >
          {revealed ? (
            <svg className="h-4 w-4" viewBox="0 0 16 16" fill="currentColor">
              <path d="M.143 2.31a.75.75 0 0 1 1.047-.167l14 10a.75.75 0 1 1-.88 1.214l-2.248-1.606C10.773 12.539 9.427 13 8 13c-3.314 0-6.045-2.09-7.657-4.4a.85.85 0 0 1 0-.9c.624-.893 1.4-1.74 2.3-2.449L.31 3.357A.75.75 0 0 1 .143 2.31ZM4.015 6.367A5.97 5.97 0 0 0 3.2 7.75 10.07 10.07 0 0 0 8 11.5c.956 0 1.874-.18 2.734-.507L9.26 9.904A2.5 2.5 0 0 1 5.81 7.296l-1.795-1.29Z" />
            </svg>
          ) : (
            <svg className="h-4 w-4" viewBox="0 0 16 16" fill="currentColor">
              <path d="M8 2c3.314 0 6.045 2.09 7.657 4.4a.85.85 0 0 1 0 .9C14.045 9.61 11.314 12 8 12s-6.045-2.09-7.657-4.4a.85.85 0 0 1 0-.9C1.955 4.39 4.686 2 8 2Zm0 1.5C5.6 3.5 3.517 5.09 2.2 6.9c-.1.14-.1.36 0 .5C3.517 9.21 5.6 10.5 8 10.5s4.483-1.29 5.8-3.1c.1-.14.1-.36 0-.5C12.483 5.09 10.4 3.5 8 3.5ZM8 5a2.5 2.5 0 1 1 0 5 2.5 2.5 0 0 1 0-5Zm0 1.5a1 1 0 1 0 0 2 1 1 0 0 0 0-2Z" />
            </svg>
          )}
        </button>
        <CopyButton text={value} />
      </div>
    </div>
  );
}

export default function ApiKeysPage() {
  const queryClient = useQueryClient();
  const [newKeyName, setNewKeyName] = useState("");
  const [newKeyVisible, setNewKeyVisible] = useState<string | null>(null);

  const keysQuery = useQuery({
    queryKey: ["auth", "api-keys"],
    queryFn: () => authApi.apiKeys(),
    staleTime: 30_000,
  });

  const createKey = useMutation({
    mutationFn: (name: string) => authApi.createApiKey({ name }),
    onSuccess: (data) => {
      setNewKeyVisible(data.key);
      setNewKeyName("");
      queryClient.invalidateQueries({ queryKey: ["auth", "api-keys"] });
    },
  });

  const deleteKey = useMutation({
    mutationFn: (id: string) => authApi.deleteApiKey(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["auth", "api-keys"] });
    },
  });

  const apiKeys: ApiKeyListItem[] = keysQuery.data ?? [];

  function handleCreateKey() {
    if (!newKeyName.trim() || createKey.isPending) return;
    createKey.mutate(newKeyName.trim());
  }

  return (
    <div>
      <div className="mb-10">
        <h1 className="text-2xl font-semibold tracking-tight text-white">API Keys</h1>
        <p className="mt-2 text-[15px] text-white/50">
          Create and manage API keys to access the Polydesk API.
        </p>
      </div>

      {/* Create Key */}
      <div className="mb-8 flex items-center gap-3">
        <input
          type="text"
          placeholder="Key name (e.g. Production)"
          value={newKeyName}
          onChange={(e) => setNewKeyName(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleCreateKey()}
          className="flex-1 rounded-xl border border-white/20 bg-white/[0.04] px-5 py-3 text-[15px] text-white placeholder-white/25 outline-none transition-colors focus:border-white/40"
        />
        <button
          onClick={handleCreateKey}
          disabled={createKey.isPending || !newKeyName.trim()}
          className="rounded-full bg-white px-7 py-3 text-[15px] font-medium text-black transition-all hover:bg-white/90 active:scale-[0.98] disabled:opacity-40 disabled:cursor-not-allowed"
        >
          {createKey.isPending ? "Creating..." : "Create Key"}
        </button>
      </div>

      {/* New key revealed */}
      {newKeyVisible && (
        <div className="mb-8 rounded-2xl border border-emerald-500/30 bg-emerald-500/5 p-5">
          <div className="mb-3 flex items-center gap-2">
            <svg className="h-4 w-4 text-emerald-400" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M3 8.5l3 3 7-7" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
            <p className="text-[15px] font-medium text-emerald-400">API key created</p>
          </div>
          <div className="flex items-center gap-3">
            <code className="flex-1 overflow-x-auto rounded-xl bg-black/50 border border-white/10 px-4 py-2.5 font-mono text-[14px] text-white select-all">
              {newKeyVisible}
            </code>
            <CopyButton text={newKeyVisible} />
          </div>
          <button
            onClick={() => setNewKeyVisible(null)}
            className="mt-3 text-[13px] text-white/30 hover:text-white/50 transition-colors"
          >
            Dismiss
          </button>
        </div>
      )}

      {/* Error */}
      {createKey.isError && (
        <div className="mb-8 rounded-2xl border border-red-500/30 bg-red-500/5 p-4">
          <p className="text-[14px] text-red-400">
            Failed to create key: {createKey.error?.message ?? "Unknown error"}
          </p>
        </div>
      )}

      {/* Keys List */}
      <div className="rounded-2xl border border-white/20 bg-white/[0.03]">
        {keysQuery.isLoading ? (
          <div>
            {[0, 1].map((i) => (
              <div key={i} className="border-b border-white/10 px-6 py-5 last:border-0">
                <Shimmer className="h-5 w-64" />
              </div>
            ))}
          </div>
        ) : keysQuery.error ? (
          <div className="px-6 py-10 text-center text-[15px] text-red-400">
            Failed to load API keys
          </div>
        ) : apiKeys.length === 0 ? (
          <div className="px-6 py-14 text-center">
            <p className="text-[15px] text-white/40">No API keys yet. Create one above to get started.</p>
            <p className="mt-2 text-[14px] text-white/25">
              Use your API key with the{" "}
              <code className="rounded-md bg-white/10 px-2 py-0.5 font-mono text-white/50">X-API-Key</code>{" "}
              header.
            </p>
          </div>
        ) : (
          apiKeys.map((key, i) => (
            <div
              key={key.id}
              className={`px-6 py-5 ${i < apiKeys.length - 1 ? "border-b border-white/10" : ""}`}
            >
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-3">
                  <span className="text-[15px] font-medium text-white">{key.name}</span>
                  {!key.is_active && (
                    <span className="rounded-full bg-red-500/10 px-2 py-0.5 text-[11px] text-red-400">INACTIVE</span>
                  )}
                  <span className="text-[13px] text-white/25">
                    {new Date(key.created_at).toLocaleDateString()}
                    {key.last_used_at
                      ? ` \u00b7 Last used ${new Date(key.last_used_at).toLocaleDateString()}`
                      : " \u00b7 Never used"}
                  </span>
                </div>
                <button
                  onClick={() => deleteKey.mutate(key.id)}
                  disabled={deleteKey.isPending}
                  className="rounded-full px-3 py-1 text-[13px] text-white/25 transition-colors hover:text-red-400 disabled:opacity-50"
                >
                  Delete
                </button>
              </div>
              <KeyDisplay value={key.key} />
            </div>
          ))
        )}
      </div>

      {/* Quick Start */}
      <div className="mt-10 rounded-2xl border border-white/20 bg-white/[0.03] p-6">
        <h3 className="mb-4 text-[15px] font-medium text-white">Quick Start</h3>
        <div className="overflow-hidden rounded-xl border border-white/10 bg-[#0a0a0a]">
          <div className="flex items-center gap-2 border-b border-white/10 px-5 py-2.5">
            <div className="flex gap-1.5">
              <div className="h-3 w-3 rounded-full bg-[#ff5f57]" />
              <div className="h-3 w-3 rounded-full bg-[#febc2e]" />
              <div className="h-3 w-3 rounded-full bg-[#28c840]" />
            </div>
            <span className="ml-3 text-[12px] text-white/30">terminal</span>
          </div>
          <pre className="p-5 text-[14px] leading-7">
            <code>
              <span className="text-blue-400">curl</span>{" "}
              <span className="text-emerald-400">&quot;https://polydesk.eu.cc/api/v1/markets?limit=5&quot;</span>{" "}
              \{"\n"}
              {"  "}-H <span className="text-emerald-400">&quot;X-API-Key: YOUR_KEY&quot;</span>
            </code>
          </pre>
        </div>
      </div>
    </div>
  );
}
