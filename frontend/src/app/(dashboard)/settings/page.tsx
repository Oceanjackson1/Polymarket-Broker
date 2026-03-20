"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { authApi, type ApiKeyListItem } from "@/lib/api";
import { Shimmer } from "@/components/ui/shimmer";

export default function SettingsPage() {
  const queryClient = useQueryClient();
  const [newKeyName, setNewKeyName] = useState("");
  const [newKeyVisible, setNewKeyVisible] = useState<string | null>(null);

  // Fetch user profile
  const user = useQuery({
    queryKey: ["auth", "me"],
    queryFn: () => authApi.me(),
    staleTime: 60_000,
  });

  // Fetch API keys
  const keysQuery = useQuery({
    queryKey: ["auth", "api-keys"],
    queryFn: () => authApi.apiKeys(),
    staleTime: 30_000,
  });

  // Create API key
  const createKey = useMutation({
    mutationFn: (name: string) => authApi.createApiKey({ name }),
    onSuccess: (data) => {
      setNewKeyVisible(data.key);
      setNewKeyName("");
      queryClient.invalidateQueries({ queryKey: ["auth", "api-keys"] });
    },
  });

  // Delete API key
  const deleteKey = useMutation({
    mutationFn: (id: string) => authApi.deleteApiKey(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["auth", "api-keys"] });
    },
  });

  const apiKeys: ApiKeyListItem[] = keysQuery.data ?? [];
  const profile = user.data;

  function handleCreateKey() {
    if (!newKeyName.trim() || createKey.isPending) return;
    createKey.mutate(newKeyName.trim());
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
            {user.isLoading ? (
              <div className="px-5 py-4">
                <Shimmer className="h-4 w-48" />
              </div>
            ) : user.error ? (
              <div className="px-5 py-4 text-sm text-loss">
                Failed to load profile — are you logged in?
              </div>
            ) : (
              <>
                {[
                  { label: "Email", value: profile?.email ?? "—" },
                  { label: "User ID", value: profile?.id ?? "—" },
                  { label: "Tier", value: (profile?.tier ?? "free").toUpperCase() },
                  {
                    label: "Joined",
                    value: profile?.created_at
                      ? new Date(profile.created_at).toLocaleDateString()
                      : "—",
                  },
                ].map((row) => (
                  <div
                    key={row.label}
                    className="flex items-center justify-between px-5 py-4"
                  >
                    <span className="text-sm text-text-secondary">
                      {row.label}
                    </span>
                    <span className="font-mono text-sm text-text-primary">
                      {row.value}
                    </span>
                  </div>
                ))}
              </>
            )}
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
                  onClick={() => navigator.clipboard.writeText(newKeyVisible)}
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

          {/* Error */}
          {createKey.isError && (
            <div className="mb-4 rounded-lg border border-loss/30 bg-loss-bg/30 p-3">
              <p className="text-xs text-loss">
                Failed to create key: {createKey.error?.message ?? "Unknown error"}
              </p>
            </div>
          )}

          {/* Key List */}
          <div className="rounded-lg border border-border-subtle bg-bg-card">
            {keysQuery.isLoading ? (
              <div className="space-y-0">
                {[0, 1].map((i) => (
                  <div key={i} className="border-b border-border-subtle px-5 py-4 last:border-0">
                    <Shimmer className="h-4 w-64" />
                  </div>
                ))}
              </div>
            ) : keysQuery.error ? (
              <div className="px-5 py-8 text-center text-sm text-loss">
                Failed to load API keys
              </div>
            ) : apiKeys.length === 0 ? (
              <div className="px-5 py-8 text-center text-sm text-text-muted">
                No API keys. Create one below.
              </div>
            ) : (
              apiKeys.map((key, i) => (
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
                        {key.key_hint}
                      </code>
                      {!key.is_active && (
                        <span className="rounded bg-loss-bg px-1.5 py-0.5 text-[10px] text-loss">
                          INACTIVE
                        </span>
                      )}
                    </div>
                    <p className="mt-0.5 text-xs text-text-muted">
                      Created {new Date(key.created_at).toLocaleDateString()}
                      {key.last_used_at
                        ? ` · Last used ${new Date(key.last_used_at).toLocaleDateString()}`
                        : " · Never used"}
                    </p>
                  </div>
                  <button
                    onClick={() => deleteKey.mutate(key.id)}
                    disabled={deleteKey.isPending}
                    className="ml-4 rounded-md border border-border-default px-3 py-1 text-xs font-medium text-text-secondary transition-colors hover:border-loss hover:text-loss disabled:opacity-50"
                  >
                    {deleteKey.isPending ? "Deleting…" : "Delete"}
                  </button>
                </div>
              ))
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
              disabled={createKey.isPending || !newKeyName.trim()}
              className="rounded-md bg-accent-gold px-4 py-2 text-sm font-semibold text-bg-base transition-colors hover:bg-accent-gold-hover disabled:opacity-50"
            >
              {createKey.isPending ? "Creating…" : "Create Key"}
            </button>
          </div>
        </section>

        {/* Appearance */}
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
