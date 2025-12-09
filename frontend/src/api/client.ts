/**
 * HTTP-клиент для работы с API.
 */

import axios, { AxiosError, InternalAxiosRequestConfig } from 'axios';

import type { ErrorResponse, TokenResponse } from '@/types';

// Создание axios-инстанса
export const apiClient = axios.create({
  baseURL: '/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Ключи для localStorage
const ACCESS_TOKEN_KEY = 'accessToken';
const REFRESH_TOKEN_KEY = 'refreshToken';

/**
 * Получить access token из localStorage.
 */
export function getAccessToken(): string | null {
  return localStorage.getItem(ACCESS_TOKEN_KEY);
}

/**
 * Получить refresh token из localStorage.
 */
export function getRefreshToken(): string | null {
  return localStorage.getItem(REFRESH_TOKEN_KEY);
}

/**
 * Сохранить токены в localStorage.
 */
export function setTokens(tokens: TokenResponse): void {
  localStorage.setItem(ACCESS_TOKEN_KEY, tokens.accessToken);
  localStorage.setItem(REFRESH_TOKEN_KEY, tokens.refreshToken);
}

/**
 * Удалить токены из localStorage.
 */
export function clearTokens(): void {
  localStorage.removeItem(ACCESS_TOKEN_KEY);
  localStorage.removeItem(REFRESH_TOKEN_KEY);
}

// Request interceptor — добавление токена
apiClient.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const token = getAccessToken();
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error),
);

// Response interceptor — обработка ошибок и обновление токена
let isRefreshing = false;
let failedQueue: Array<{
  resolve: (token: string) => void;
  reject: (error: unknown) => void;
}> = [];

const processQueue = (error: unknown, token: string | null = null) => {
  failedQueue.forEach((prom) => {
    if (error) {
      prom.reject(error);
    } else if (token) {
      prom.resolve(token);
    }
  });
  failedQueue = [];
};

apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError<ErrorResponse>) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & {
      _retry?: boolean;
    };

    // Если 401 и есть refresh token — пробуем обновить
    if (error.response?.status === 401 && !originalRequest._retry) {
      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          failedQueue.push({
            resolve: (token: string) => {
              originalRequest.headers.Authorization = `Bearer ${token}`;
              resolve(apiClient(originalRequest));
            },
            reject,
          });
        });
      }

      originalRequest._retry = true;
      isRefreshing = true;

      const refreshToken = getRefreshToken();
      if (!refreshToken) {
        clearTokens();
        window.location.href = '/login';
        return Promise.reject(error);
      }

      try {
        const response = await axios.post<TokenResponse>('/api/v1/auth/refresh', {
          refreshToken,
        });

        const tokens = response.data;
        setTokens(tokens);
        processQueue(null, tokens.accessToken);

        originalRequest.headers.Authorization = `Bearer ${tokens.accessToken}`;
        return apiClient(originalRequest);
      } catch (refreshError) {
        processQueue(refreshError, null);
        clearTokens();
        window.location.href = '/login';
        return Promise.reject(refreshError);
      } finally {
        isRefreshing = false;
      }
    }

    return Promise.reject(error);
  },
);

/**
 * Извлечь сообщение об ошибке из ответа API.
 */
export function getErrorMessage(error: unknown): string {
  if (axios.isAxiosError(error)) {
    const data = error.response?.data as ErrorResponse | undefined;
    if (data?.error?.message) {
      return data.error.message;
    }
    if (error.response?.status === 401) {
      return 'Требуется авторизация';
    }
    if (error.response?.status === 403) {
      return 'Доступ запрещён';
    }
    if (error.response?.status === 404) {
      return 'Ресурс не найден';
    }
    if (error.response?.status === 500) {
      return 'Внутренняя ошибка сервера';
    }
  }
  return 'Произошла ошибка';
}
