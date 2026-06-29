import { apiClient } from './client';
import type {
  ChecklistRun,
  ChecklistRunCreateInput,
  ChecklistRunListItem,
  ChecklistRunStatus,
  ChecklistRunUpdateInput,
  PaginatedResponse,
} from '@/types';

export async function getRuns(
  params: { status?: ChecklistRunStatus; q?: string; page?: number; page_size?: number } = {},
): Promise<PaginatedResponse<ChecklistRunListItem>> {
  const response = await apiClient.get<PaginatedResponse<ChecklistRunListItem>>('/checklist-runs', {
    params: {
      status: params.status,
      q: params.q || undefined,
      page: params.page ?? 1,
      page_size: params.page_size ?? 20,
    },
  });
  return response.data;
}

export async function getRun(runId: string): Promise<ChecklistRun> {
  const response = await apiClient.get<ChecklistRun>(`/checklist-runs/${runId}`);
  return response.data;
}

export async function startRun(payload: ChecklistRunCreateInput): Promise<ChecklistRun> {
  const response = await apiClient.post<ChecklistRun>('/checklist-runs', payload);
  return response.data;
}

export async function updateRun(runId: string, payload: ChecklistRunUpdateInput): Promise<ChecklistRun> {
  const response = await apiClient.patch<ChecklistRun>(`/checklist-runs/${runId}`, payload);
  return response.data;
}

export async function completeRun(runId: string): Promise<ChecklistRun> {
  const response = await apiClient.post<ChecklistRun>(`/checklist-runs/${runId}/complete`);
  return response.data;
}

export async function deleteRun(runId: string): Promise<void> {
  await apiClient.delete(`/checklist-runs/${runId}`);
}
