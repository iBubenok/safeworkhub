import { apiClient } from './client';
import type {
  Category,
  Material,
  MaterialListItem,
  MaterialType,
  MaterialSearchParams,
  PaginatedResponse,
} from '@/types';

export async function getMaterials(
  params: MaterialSearchParams = {},
): Promise<PaginatedResponse<MaterialListItem>> {
  const response = await apiClient.get<PaginatedResponse<MaterialListItem>>('/materials', {
    params: {
      page: params.page ?? 1,
      page_size: params.page_size ?? 20,
      type: params.type,
      category_id: params.category_id,
    },
  });
  return response.data;
}

export async function searchMaterials(
  params: MaterialSearchParams & { query: string },
): Promise<PaginatedResponse<MaterialListItem>> {
  const response = await apiClient.get<PaginatedResponse<MaterialListItem>>('/materials/search', {
    params: {
      q: params.query,
      page: params.page ?? 1,
      page_size: params.page_size ?? 20,
      type: params.type,
      category_id: params.category_id,
    },
  });
  return response.data;
}

export async function getMaterial(materialId: string): Promise<Material> {
  const response = await apiClient.get<Material>(`/materials/${materialId}`);
  return response.data;
}

export async function createMaterial(payload: {
  title: string;
  summary: string | null;
  content: string;
  type: MaterialType;
  category_id?: number | null;
  status?: string;
}): Promise<Material> {
  const response = await apiClient.post<Material>('/materials', payload);
  return response.data;
}

export async function publishMaterial(materialId: string): Promise<Material> {
  const response = await apiClient.post<Material>(`/materials/${materialId}/publish`);
  return response.data;
}

export async function getCategories(): Promise<Category[]> {
  const response = await apiClient.get<Category[]>('/materials/categories');
  return response.data;
}

export async function getPopularMaterials(limit: number = 10): Promise<MaterialListItem[]> {
  const response = await apiClient.get<MaterialListItem[]>('/materials/popular', {
    params: { limit },
  });
  return response.data;
}
