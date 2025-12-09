/**
 * Тесты для хука useAuth.
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import type { ReactNode } from 'react';

import { useAuthStore } from '@/store/authStore';

// Мок API
vi.mock('@/api/auth', () => ({
  login: vi.fn(),
  register: vi.fn(),
  logout: vi.fn(),
  refreshToken: vi.fn(),
  getProfile: vi.fn(),
}));

// Обёртка с QueryClientProvider
function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  });

  return function Wrapper({ children }: { children: ReactNode }) {
    return (
      <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    );
  };
}

describe('useAuthStore', () => {
  beforeEach(() => {
    // Сбрасываем состояние store перед каждым тестом
    useAuthStore.getState().logout();
    localStorage.clear();
  });

  it('изначально пользователь не авторизован', () => {
    const { isAuthenticated, user, accessToken } = useAuthStore.getState();

    expect(isAuthenticated).toBe(false);
    expect(user).toBeNull();
    expect(accessToken).toBeNull();
  });

  it('setAuth устанавливает данные авторизации', () => {
    const testUser = {
      id: '1',
      email: 'test@example.com',
      name: 'Тестовый пользователь',
      isActive: true,
      createdAt: new Date().toISOString(),
    };

    useAuthStore.getState().setAuth({
      user: testUser,
      accessToken: 'test-access-token',
      refreshToken: 'test-refresh-token',
    });

    const { isAuthenticated, user, accessToken } = useAuthStore.getState();

    expect(isAuthenticated).toBe(true);
    expect(user).toEqual(testUser);
    expect(accessToken).toBe('test-access-token');
  });

  it('logout очищает данные авторизации', () => {
    // Сначала авторизуемся
    useAuthStore.getState().setAuth({
      user: {
        id: '1',
        email: 'test@example.com',
        name: 'Тестовый пользователь',
        isActive: true,
        createdAt: new Date().toISOString(),
      },
      accessToken: 'test-access-token',
      refreshToken: 'test-refresh-token',
    });

    // Выходим
    useAuthStore.getState().logout();

    const { isAuthenticated, user, accessToken } = useAuthStore.getState();

    expect(isAuthenticated).toBe(false);
    expect(user).toBeNull();
    expect(accessToken).toBeNull();
  });

  it('updateUser обновляет данные пользователя', () => {
    // Авторизуемся
    useAuthStore.getState().setAuth({
      user: {
        id: '1',
        email: 'test@example.com',
        name: 'Старое имя',
        isActive: true,
        createdAt: new Date().toISOString(),
      },
      accessToken: 'test-access-token',
      refreshToken: 'test-refresh-token',
    });

    // Обновляем имя
    useAuthStore.getState().updateUser({ name: 'Новое имя' });

    const { user } = useAuthStore.getState();

    expect(user?.name).toBe('Новое имя');
    expect(user?.email).toBe('test@example.com');
  });
});
