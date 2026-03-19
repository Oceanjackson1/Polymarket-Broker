"use client";

import { useState } from "react";

interface ApiKey {
  id: string;
  name: string;
  prefix: string;
  created: string;
  lastUsed: string;
}

const initialApiKeys: ApiKey[] = [
  {
    id: "key-1",
    name: "Production",
    prefix: "pm_live_sk_a3f…",
    created: "Jan 14, 2026",
    lastUsed: "Mar 19, 2026",
  },
  {
    id: "key-2",
    name: "Development",
    prefix: "pm_test_sk_b7c…",
    created: "Feb 2, 2026",
    lastUsed: "Mar 18, 2026",
  },
];

export default function SettingsPage() {
  const [apiKeys, setApiKeys] = useState<ApiKey[]>(initialApiKeys);
  const [creating, setCreating] = useState(false);
  const [newKeyName, setNewKeyName] = useState("");
  const [newKeyVisible, setNewKeyVisible] = useState<string | null>(null);
  const [deleting, setDeleting] = useState<string | null>(null);

  function handleCreateKey() {
    if (!newKeyName.trim()) return;
    setCreating(true);
    setTimeout(() => {
      const newKey: ApiKey = {
        id: `key-${Date.now()}`,
        name: newKeyName.trim(),
        prefix: `pm_live_sk_${Math.random().toString(36).slice(2, 5)}…`,
        created: "Mar 19, 2026",
        lastUsed: "Never",
      };
      const fullKey = `pm_live_sk_${Math.random().toString(36).slice(2, 18)}`;
      setApiKeys((prev) => [...prev, newKey]);
      setNewKeyVisible(fullKey);
      setNewKeyName("");
      setCreating(false);
    }, 900);
  }

  function handleDeleteKey(id: string) {
    setDeleting(id);
    setTimeout(() => {
      setApiKeys((prev) => prev.filter((k) => k.id !== id));
      setDeleting(null);
    }, 600);
  }

  return (
    <div className="p-6">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-xl font-semibold text-text-primary">Settings</h1>
        <p className="mt-1 text-sm text-text-secondary">
          Manage your account, API keys, and preferences.
        </p>
      </div>

      <div className="space-y-8 max-w-3xl">
        {/* Account Info */}
        <section>
          <h2 className="mb-4 text-sm font-semibold text-text-muted uppercase tracking-wider">
            Account
          </h2>
          <div className="rounded-lg border border-border-subtle bg-bg-card divide-y divide-border-subtle">
            {[
              { label: "Email", value: "trader@example.com" },
              { label: "User ID", value: "usr_8a3f9c2d1e" },
              { label: "Joined", value: "January 14, 2026" },
              { label: "Wallet", value: "0x1a2b…9f3e (linked)" },
            ].map((row) => (
              <div
                key={row.label}
                className="flex items-center justify-between px-5 py-4"
              >
                <span className="text-sm text-text-secondary">{row.label}</span>
                <span className="font-mono text-sm text-text-primary">
                  {row.value}
                </span>
              </div>
            ))}
          </div>
        </section>

        {/* Subscription Tier */}
        <section>
          <h2 className="mb-4 text-sm font-semibold text-text-muted uppercase tracking-wider">
            Subscription
          </h2>
          <div className="rounded-lg border border-accent-gold/30 bg-bg-card p-5">
            <div className="flex items-center justify-between">
              <div>
                <div className="flex items-center gap-2">
                  <span className="text-base font-semibold text-text-primary">
                    Pro Plan
                  </span>
                  <span className="rounded bg-accent-gold-bg px-2 py-0.5 text-xs font-semibold text-accent-gold">
                    ACTIVE
                  </span>
                </div>
                <p className="mt-1 text-sm text-text-secondary">
                  $99 / month · Renews Apr 14, 2026
                </p>
              </div>
              <button className="rounded-md border border-border-default px-4 py-2 text-sm text-text-secondary transition-colors hover:bg-bg-elevated">
                Manage
              </button>
            </div>
            <div className="mt-4 grid grid-cols-3 gap-4 border-t border-border-subtle pt-4">
              {[
                { label: "API Calls Today", value: "1,240 / ∞" },
                { label: "Broker Fee", value: "+5 bps" },
                { label: "AI Analyses Today", value: "38 / ∞" },
              ].map((stat) => (
                <div key={stat.label}>
                  <p className="text-xs text-text-muted">{stat.label}</p>
                  <p className="mt-0.5 font-mono text-sm font-medium text-text-primary">
                    {stat.value}
                  </p>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* API Keys */}
        <section>
          <h2 className="mb-4 text-sm font-semibold text-text-muted uppercase tracking-wider">
            API Keys
          </h2>

          {/* New key revealed */}
          {newKeyVisible && (
            <div className="mb-4 rounded-lg border border-profit/30 bg-profit-bg/30 p-4">
              <p className="mb-2 text-xs font-medium text-profit">
                Key created — copy it now, it will not be shown again.
              </p>
              <div className="flex items-center gap-3">
                <code className="flex-1 overflow-x-auto font-mono text-sm text-text-primary">
                  {newKeyVisible}
                </code>
                <button
                  onClick={() => {
                    navigator.clipboard.writeText(newKeyVisible);
                  }}
                  className="rounded-md border border-border-default px-3 py-1 text-xs text-text-secondary transition-colors hover:bg-bg-elevated"
                >
                  Copy
                </button>
                <button
                  onClick={() => setNewKeyVisible(null)}
                  className="text-xs text-text-muted hover:text-text-secondary"
                >
                  Dismiss
                </button>
              </div>
            </div>
          )}

          {/* Key List */}
          <div className="rounded-lg border border-border-subtle bg-bg-card">
            {apiKeys.map((key, i) => (
              <div
                key={key.id}
                className={`flex items-center justify-between px-5 py-4 ${
                  i < apiKeys.length - 1 ? "border-b border-border-subtle" : ""
                }`}
              >
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-medium text-text-primary">
                      {key.name}
                    </span>
                    <code className="font-mono text-xs text-text-muted">
                      {key.prefix}
                    </code>
                  </div>
                  <p className="mt-0.5 text-xs text-text-muted">
                    Created {key.created} · Last used {key.lastUsed}
                  </p>
                </div>
                <button
                  onClick={() => handleDeleteKey(key.id)}
                  disabled={deleting === key.id}
                  className="ml-4 rounded-md border border-border-default px-3 py-1 text-xs font-medium text-text-secondary transition-colors hover:border-loss hover:text-loss disabled:opacity-50"
                >
                  {deleting === key.id ? "Deleting…" : "Delete"}
                </button>
              </div>
            ))}

            {apiKeys.length === 0 && (
              <div className="px-5 py-8 text-center text-sm text-text-muted">
                No API keys. Create one below.
              </div>
            )}
          </div>

          {/* Create new key */}
          <div className="mt-4 flex items-center gap-3">
            <input
              type="text"
              placeholder="Key name (e.g. Production)"
              value={newKeyName}
              onChange={(e) => setNewKeyName(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleCreateKey()}
              className="flex-1 rounded-md border border-border-default bg-bg-elevated px-3 py-2 text-sm text-text-primary placeholder:text-text-muted focus:border-accent-gold focus:outline-none"
            />
            <button
              onClick={handleCreateKey}
              disabled={creating || !newKeyName.trim()}
              className="rounded-md bg-accent-gold px-4 py-2 text-sm font-semibold text-bg-base transition-colors hover:bg-accent-gold-hover disabled:opacity-50"
            >
              {creating ? "Creating…" : "Create Key"}
            </button>
          </div>
        </section>

        {/* Theme */}
        <section>
          <h2 className="mb-4 text-sm font-semibold text-text-muted uppercase tracking-wider">
            Appearance
          </h2>
          <div className="rounded-lg border border-border-subtle bg-bg-card px-5 py-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-text-primary">Theme</p>
                <p className="mt-0.5 text-xs text-text-muted">
                  Light mode coming soon. Terminal dark is the only option.
                </p>
              </div>
              <div className="flex items-center gap-2 rounded-md border border-accent-gold/30 bg-bg-elevated px-3 py-1.5">
                <span className="h-2.5 w-2.5 rounded-full bg-accent-gold" />
                <span className="text-sm text-text-primary">Dark</span>
              </div>
            </div>
          </div>
        </section>
      </div>
    </div>
  );
}
