"use client";

import { useCallback } from "react";
import { useAuthContext } from "@/lib/providers";

export function useAuth() {
  const { user, token, setAuth, logout: ctxLogout, api } = useAuthContext();

  const login = useCallback(
    async (email: string, password: string) => {
      const res = await api.login(email, password);
      setAuth({ id: email, email }, res.access_token);
      return res;
    },
    [api, setAuth]
  );

  const register = useCallback(
    async (email: string, password: string) => {
      await api.register(email, password);
      // Auto-login after registration
      return login(email, password);
    },
    [api, login]
  );

  const logout = useCallback(() => {
    ctxLogout();
  }, [ctxLogout]);

  return {
    user,
    token,
    isAuthenticated: !!token,
    login,
    register,
    logout,
    api,
  };
}
