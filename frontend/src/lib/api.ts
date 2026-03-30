// ─── Polydesk — Typed API Client ────────────────────────────────────────────

const API_BASE = "/api/v1";

// ─── Error ────────────────────────────────────────────────────────────────────

export class ApiError extends Error {
  constructor(
    public readonly status: number,
    public readonly statusText: string,
    message: string
  ) {
    super(message);
    this.name = "ApiError";
  }
}

// ─── Core fetch wrapper ───────────────────────────────────────────────────────

async function apiFetch<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  // Read API key from cookie (set by auth flow)
  let apiKey: string | null = null;
  if (typeof document !== "undefined") {
    const match = document.cookie.match(/(?:^|;\s*)pm_api_key=([^;]+)/);
    apiKey = match ? decodeURIComponent(match[1]) : null;
  }

  const headers: HeadersInit = {
    "Content-Type": "application/json",
    ...(apiKey ? { "X-API-Key": apiKey } : {}),
    ...options.headers,
  };

  const res = await fetch(`${API_BASE}${path}`, { ...options, headers });

  if (!res.ok) {
    let message = res.statusText;
    try {
      const body = (await res.json()) as { detail?: string; message?: string };
      message = body.detail ?? body.message ?? message;
    } catch {
      // non-JSON error body — keep statusText
    }
    throw new ApiError(res.status, res.statusText, message);
  }

  // 204 No Content
  if (res.status === 204) return undefined as T;

  return res.json() as Promise<T>;
}

// ─── Auth Types ───────────────────────────────────────────────────────────────

export interface UserResponse {
  id: string;
  email: string;
  tier: string;
  created_at: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface ApiKeyListItem {
  id: string;
  name: string;
  key: string;
  key_hint: string;
  scopes: string[];
  is_active: boolean;
  created_at: string;
  last_used_at: string | null;
}

export interface ApiKeyCreatedResponse {
  id: string;
  name: string;
  key: string;
  key_hint: string;
  scopes: string[];
  created_at: string;
}

export interface RegisterRequest {
  email: string;
  password: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface CreateApiKeyRequest {
  name: string;
  scopes?: string[];
}

// ─── Usage Types ─────────────────────────────────────────────────────────────

export interface UsageResponse {
  calls_today: number;
  calls_remaining: number | null;
  tier: string;
  reset_at: string;
}

// ─── Auth API ─────────────────────────────────────────────────────────────────

export const authApi = {
  register: (req: RegisterRequest): Promise<TokenResponse> =>
    apiFetch<TokenResponse>("/auth/register", {
      method: "POST",
      body: JSON.stringify(req),
    }),

  login: (req: LoginRequest): Promise<TokenResponse> =>
    apiFetch<TokenResponse>("/auth/login", {
      method: "POST",
      body: JSON.stringify(req),
    }),

  me: (): Promise<UserResponse> => apiFetch<UserResponse>("/auth/me"),

  apiKeys: (): Promise<ApiKeyListItem[]> =>
    apiFetch<ApiKeyListItem[]>("/auth/keys"),

  createApiKey: (req: CreateApiKeyRequest): Promise<ApiKeyCreatedResponse> =>
    apiFetch<ApiKeyCreatedResponse>("/auth/keys", {
      method: "POST",
      body: JSON.stringify(req),
    }),

  deleteApiKey: (id: string): Promise<void> =>
    apiFetch<void>(`/auth/keys/${id}`, { method: "DELETE" }),
};

// ─── Developer API ───────────────────────────────────────────────────────────

export const developerApi = {
  usage: (): Promise<UsageResponse> =>
    apiFetch<UsageResponse>("/developer/usage"),
};
