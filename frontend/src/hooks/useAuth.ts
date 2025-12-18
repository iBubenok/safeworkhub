import { useCallback, useEffect } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';

import * as authApi from '@/api/auth';
import { useAuthStore } from '@/store/authStore';
import type { LoginRequest, RegisterRequest } from '@/types';

export function useAuth() {
  const queryClient = useQueryClient();
  const { user, accessToken, role, isInitialized } = useAuthStore();
  const setSession = useAuthStore((state) => state.setSession);
  const clearAuth = useAuthStore((state) => state.clearAuth);
  const setInitialized = useAuthStore((state) => state.setInitialized);

  const bootstrapSession = useCallback(async () => {
    try {
      const tokens = await authApi.refreshSession();
      setSession(tokens);
    } catch {
      clearAuth();
    } finally {
      setInitialized(true);
    }
  }, [clearAuth, setInitialized, setSession]);

  useEffect(() => {
    if (!isInitialized) {
      void bootstrapSession();
    }
  }, [bootstrapSession, isInitialized]);

  const loginMutation = useMutation({
    mutationFn: authApi.login,
    onSuccess: (tokens) => {
      setSession(tokens);
      setInitialized(true);
    },
  });

  const registerMutation = useMutation({
    mutationFn: authApi.register,
  });

  const login = useCallback(
    async (data: LoginRequest) => {
      await loginMutation.mutateAsync(data);
    },
    [loginMutation],
  );

  const register = useCallback(
    async (data: RegisterRequest) => registerMutation.mutateAsync(data),
    [registerMutation],
  );

  const logout = useCallback(async () => {
    try {
      await authApi.logout();
    } finally {
      clearAuth();
      queryClient.clear();
    }
  }, [clearAuth, queryClient]);

  return {
    user,
    accessToken,
    role,
    isAuthenticated: Boolean(user && accessToken),
    isLoading: !isInitialized,
    login,
    logout,
    register,
    loginError: loginMutation.error,
    registerError: registerMutation.error,
    isLoggingIn: loginMutation.isPending,
    isRegistering: registerMutation.isPending,
  };
}
