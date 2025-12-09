/**
 * Хук для работы с аутентификацией.
 */

import { useCallback, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';

import { useAuthStore } from '@/store/authStore';
import * as authApi from '@/api/auth';
import { getAccessToken, clearTokens } from '@/api/client';
import type { LoginRequest, RegisterRequest, User } from '@/types';

export function useAuth() {
  const queryClient = useQueryClient();
  const { user, setUser, clearAuth, isInitialized, setInitialized } = useAuthStore();

  // Запрос текущего пользователя
  const {
    data: currentUser,
    isLoading: isLoadingUser,
    error: userError,
  } = useQuery({
    queryKey: ['currentUser'],
    queryFn: authApi.getCurrentUser,
    enabled: !!getAccessToken() && !user,
    retry: false,
    staleTime: 5 * 60 * 1000, // 5 минут
  });

  // Синхронизация с store
  useEffect(() => {
    if (currentUser) {
      setUser(currentUser);
    }
    if (userError) {
      clearAuth();
      clearTokens();
    }
    if (!isInitialized) {
      setInitialized(true);
    }
  }, [currentUser, userError, isInitialized, setUser, clearAuth, setInitialized]);

  // Мутация входа
  const loginMutation = useMutation({
    mutationFn: authApi.login,
    onSuccess: async () => {
      const userData = await authApi.getCurrentUser();
      setUser(userData);
      queryClient.invalidateQueries({ queryKey: ['currentUser'] });
    },
  });

  // Мутация регистрации
  const registerMutation = useMutation({
    mutationFn: authApi.register,
  });

  // Функция входа
  const login = useCallback(
    async (data: LoginRequest) => {
      await loginMutation.mutateAsync(data);
    },
    [loginMutation],
  );

  // Функция регистрации
  const register = useCallback(
    async (data: RegisterRequest) => {
      return registerMutation.mutateAsync(data);
    },
    [registerMutation],
  );

  // Функция выхода
  const logout = useCallback(async () => {
    try {
      await authApi.logout();
    } finally {
      clearAuth();
      queryClient.clear();
    }
  }, [clearAuth, queryClient]);

  return {
    user: user || currentUser,
    isAuthenticated: !!(user || currentUser),
    isLoading: isLoadingUser && !isInitialized,
    login,
    logout,
    register,
    loginError: loginMutation.error,
    registerError: registerMutation.error,
    isLoggingIn: loginMutation.isPending,
    isRegistering: registerMutation.isPending,
  };
}
