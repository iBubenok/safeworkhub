/**
 * API-методы для аутентификации.
 */

import { apiClient, setTokens, clearTokens } from './client';
import type { LoginRequest, RegisterRequest, TokenResponse, User } from '@/types';

/**
 * Вход в систему.
 */
export async function login(data: LoginRequest): Promise<TokenResponse> {
  const response = await apiClient.post<TokenResponse>('/auth/login', data);
  setTokens(response.data);
  return response.data;
}

/**
 * Регистрация организации.
 */
export async function register(
  data: RegisterRequest,
): Promise<{ organizationId: number; userId: string; message: string }> {
  const response = await apiClient.post('/auth/register', {
    organization_name: data.organizationName,
    inn: data.inn,
    admin_email: data.adminEmail,
    admin_password: data.adminPassword,
    admin_name: data.adminName,
  });
  return response.data;
}

/**
 * Выход из системы.
 */
export async function logout(): Promise<void> {
  try {
    await apiClient.post('/auth/logout');
  } finally {
    clearTokens();
  }
}

/**
 * Получить текущего пользователя.
 */
export async function getCurrentUser(): Promise<User> {
  const response = await apiClient.get<User>('/users/me');
  return response.data;
}

/**
 * Обновить токены.
 */
export async function refreshTokens(refreshToken: string): Promise<TokenResponse> {
  const response = await apiClient.post<TokenResponse>('/auth/refresh', {
    refresh_token: refreshToken,
  });
  setTokens(response.data);
  return response.data;
}
