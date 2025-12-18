import axios, { AxiosError, AxiosRequestHeaders, InternalAxiosRequestConfig } from 'axios';

import { useAuthStore } from '@/store/authStore';
import type { ErrorResponse, TokenResponse } from '@/types';

type RetriableRequest = InternalAxiosRequestConfig & { _retry?: boolean };

const apiBaseUrl = (import.meta.env.VITE_API_URL as string | undefined)?.replace(/\/$/, '');

export const apiClient = axios.create({
  baseURL: apiBaseUrl || '/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true,
  timeout: 15000,
});

const refreshClient = axios.create({
  baseURL: apiBaseUrl || '/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true,
  timeout: 15000,
});

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

async function refreshSession(): Promise<TokenResponse> {
  const response = await refreshClient.post<TokenResponse>('/auth/refresh');
  return response.data;
}

apiClient.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const token = useAuthStore.getState().accessToken;
  const headers = (config.headers ?? {}) as AxiosRequestHeaders;
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }
  config.headers = headers;
  return config;
});

apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError<ErrorResponse>) => {
    const originalRequest = error.config as RetriableRequest | undefined;

    if (
      error.response?.status === 401 &&
      originalRequest &&
      !originalRequest._retry &&
      originalRequest.url &&
      !originalRequest.url.includes('/auth/login') &&
      !originalRequest.url.includes('/auth/register') &&
      !originalRequest.url.includes('/auth/refresh')
    ) {
      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          failedQueue.push({
            resolve: (token: string) => {
              const headers = (originalRequest.headers ?? {}) as AxiosRequestHeaders;
              headers.Authorization = `Bearer ${token}`;
              originalRequest.headers = headers;
              resolve(apiClient(originalRequest));
            },
            reject,
          });
        });
      }

      originalRequest._retry = true;
      isRefreshing = true;

      try {
        const tokens = await refreshSession();
        useAuthStore.getState().setSession(tokens);
        processQueue(null, tokens.access_token);

        const headers = (originalRequest.headers ?? {}) as AxiosRequestHeaders;
        headers.Authorization = `Bearer ${tokens.access_token}`;
        originalRequest.headers = headers;
        return apiClient(originalRequest);
      } catch (refreshError) {
        processQueue(refreshError, null);
        useAuthStore.getState().clearAuth();
        return Promise.reject(refreshError);
      } finally {
        isRefreshing = false;
      }
    }

    return Promise.reject(error);
  },
);

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
