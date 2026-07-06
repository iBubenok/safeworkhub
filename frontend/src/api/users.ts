import { apiClient } from './client';
import type { OrgMemberOption, User } from '@/types';

export async function searchUsers(params: {
  query?: string;
  limit?: number;
  offset?: number;
} = {}): Promise<User[]> {
  const response = await apiClient.get<User[]>('/users', {
    params: {
      q: params.query ?? '',
      limit: params.limit ?? 20,
      offset: params.offset ?? 0,
    },
  });
  return response.data;
}

/** Активные участники организации (краткий список) — доступно любому участнику. */
export async function getOrgMembers(): Promise<OrgMemberOption[]> {
  const response = await apiClient.get<OrgMemberOption[]>('/users/members');
  return response.data;
}

export async function createUser(data: {
  email: string;
  name: string;
  password: string;
  role: string;
}): Promise<User> {
  const response = await apiClient.post<User>('/users', data);
  return response.data;
}

export async function deactivateUser(userId: string): Promise<void> {
  await apiClient.delete(`/users/${userId}`);
}

export async function activateUser(userId: string): Promise<void> {
  await apiClient.post(`/users/${userId}/activate`);
}
