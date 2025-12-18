import { apiClient } from './client';
import type {
  LoginRequest,
  RegisterRequest,
  RegisterResponse,
  TokenResponse,
  User,
} from '@/types';

export async function login(data: LoginRequest): Promise<TokenResponse> {
  const response = await apiClient.post<TokenResponse>('/auth/login', {
    email: data.email,
    password: data.password,
    organization_id: data.organization_id,
  });
  return response.data;
}

export async function register(data: RegisterRequest): Promise<RegisterResponse> {
  const response = await apiClient.post<RegisterResponse>('/auth/register', data);
  return response.data;
}

export async function logout(): Promise<void> {
  await apiClient.post('/auth/logout');
}

export async function getCurrentUser(): Promise<User> {
  const response = await apiClient.get<User>('/users/me');
  return response.data;
}

export async function refreshSession(): Promise<TokenResponse> {
  const response = await apiClient.post<TokenResponse>('/auth/refresh');
  return response.data;
}
