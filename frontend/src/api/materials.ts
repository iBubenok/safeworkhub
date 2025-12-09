/**
 * API-методы для работы с базой знаний.
 */

import { apiClient } from './client';
import type { Material, MaterialListItem, MaterialSearchParams, PaginatedResponse } from '@/types';

/**
 * Получить список материалов.
 */
export async function getMaterials(
  params: MaterialSearchParams = {},
): Promise<PaginatedResponse<MaterialListItem>> {
  const response = await apiClient.get<PaginatedResponse<MaterialListItem>>('/materials', {
    params: {
      page: params.page || 1,
      page_size: params.pageSize || 20,
      type: params.type,
      category_id: params.categoryId,
    },
  });
  return response.data;
}

/**
 * Поиск материалов.
 */
export async function searchMaterials(
  params: MaterialSearchParams & { query: string },
): Promise<PaginatedResponse<MaterialListItem>> {
  const response = await apiClient.get<PaginatedResponse<MaterialListItem>>('/materials/search', {
    params: {
      q: params.query,
      page: params.page || 1,
      page_size: params.pageSize || 20,
      type: params.type,
      category_id: params.categoryId,
    },
  });
  return response.data;
}

/**
 * Получить материал по ID.
 */
export async function getMaterial(materialId: string): Promise<Material> {
  const response = await apiClient.get<Material>(`/materials/${materialId}`);
  return response.data;
}

/**
 * Получить популярные материалы.
 */
export async function getPopularMaterials(limit: number = 10): Promise<MaterialListItem[]> {
  const response = await apiClient.get<MaterialListItem[]>('/materials/popular', {
    params: { limit },
  });
  return response.data;
}
