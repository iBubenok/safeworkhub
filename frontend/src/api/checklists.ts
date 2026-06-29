import { apiClient } from './client';
import type {
  Checklist,
  ChecklistCreateInput,
  ChecklistListItem,
  ChecklistStatus,
  ChecklistUpdateInput,
  PaginatedResponse,
} from '@/types';

export async function getChecklists(
  params: { status?: ChecklistStatus; q?: string; page?: number; page_size?: number } = {},
): Promise<PaginatedResponse<ChecklistListItem>> {
  const response = await apiClient.get<PaginatedResponse<ChecklistListItem>>('/checklists', {
    params: {
      status: params.status,
      q: params.q || undefined,
      page: params.page ?? 1,
      page_size: params.page_size ?? 20,
    },
  });
  return response.data;
}

export async function getChecklist(checklistId: string): Promise<Checklist> {
  const response = await apiClient.get<Checklist>(`/checklists/${checklistId}`);
  return response.data;
}

export async function createChecklist(payload: ChecklistCreateInput): Promise<Checklist> {
  const response = await apiClient.post<Checklist>('/checklists', payload);
  return response.data;
}

export async function updateChecklist(checklistId: string, payload: ChecklistUpdateInput): Promise<Checklist> {
  const response = await apiClient.patch<Checklist>(`/checklists/${checklistId}`, payload);
  return response.data;
}

export async function publishChecklist(checklistId: string): Promise<Checklist> {
  const response = await apiClient.post<Checklist>(`/checklists/${checklistId}/publish`);
  return response.data;
}

export async function archiveChecklist(checklistId: string): Promise<Checklist> {
  const response = await apiClient.post<Checklist>(`/checklists/${checklistId}/archive`);
  return response.data;
}

export async function deleteChecklist(checklistId: string): Promise<void> {
  await apiClient.delete(`/checklists/${checklistId}`);
}
