"use client";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import {
  useState,
  useEffect,
  createContext,
  useContext,
  useCallback,
} from "react";
import dynamic from "next/dynamic";
import BrokerAPI, { createAPI } from "./api-client";

// Dynamically import wallet providers to avoid SSR localStorage issues
const WalletProviders = dynamic(() => import("./wallet-providers"), {
  ssr: false,
  loading: () => null,
});

// --- Auth Context ---
type AuthUser = { id: string; email?: string; tier?: string } | null;

type AuthContextType = {
  user: AuthUser;
  token: string | null;
  setAuth: (user: AuthUser, token: string | null) => void;
  logout: () => void;
  api: BrokerAPI;
};

const AuthContext = createContext<AuthContextType>({
  user: null,
  token: null,
  setAuth: () => {},
  logout: () => {},
  api: createAPI(),
});

export function useAuthContext() {
  return useContext(AuthContext);
}

// --- Locale Context ---
type LocaleContextType = {
  locale: string;
  setLocale: (l: string) => void;
  t: (key: string) => string;
};

const LocaleContext = createContext<LocaleContextType>({
  locale: "en",
  setLocale: () => {},
  t: (k) => k,
});

export function useLocale() {
  return useContext(LocaleContext);
}

// --- Providers ---
export function Providers({ children }: { children: React.ReactNode }) {
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: { staleTime: 10_000, retry: 1 },
        },
      })
  );

  const [user, setUser] = useState<AuthUser>(null);
  const [token, setToken] = useState<string | null>(null);
  const [locale, setLocaleState] = useState(
    process.env.NEXT_PUBLIC_DEFAULT_LOCALE || "en"
  );
  const [messages, setMessages] = useState<Record<string, unknown>>({});

  useEffect(() => {
    import(`@/i18n/${locale}.json`).then((m) => setMessages(m.default || m));
  }, [locale]);

  const setLocale = useCallback((l: string) => {
    setLocaleState(l);
    if (typeof document !== "undefined") {
      document.cookie = `locale=${l};path=/;max-age=31536000`;
    }
  }, []);

  const t = useCallback(
    (key: string): string => {
      const parts = key.split(".");
      let val: unknown = messages;
      for (const p of parts) {
        if (val && typeof val === "object") {
          val = (val as Record<string, unknown>)[p];
        } else {
          return key;
        }
      }
      return typeof val === "string" ? val : key;
    },
    [messages]
  );

  const [api] = useState(() => createAPI(() => token));

  const setAuth = useCallback((u: AuthUser, tok: string | null) => {
    setUser(u);
    setToken(tok);
  }, []);

  const logout = useCallback(() => {
    setUser(null);
    setToken(null);
  }, []);

  return (
    <QueryClientProvider client={queryClient}>
      <AuthContext.Provider value={{ user, token, setAuth, logout, api }}>
        <LocaleContext.Provider value={{ locale, setLocale, t }}>
          <WalletProviders>{children}</WalletProviders>
        </LocaleContext.Provider>
      </AuthContext.Provider>
    </QueryClientProvider>
  );
}
