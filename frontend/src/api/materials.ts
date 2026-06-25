import { apiClient } from './client';
import type {
  ArticleCreateInput,
  AttachmentResponse,
  Category,
  Material,
  MaterialContentFormat,
  MaterialListItem,
  MaterialType,
  MaterialSearchParams,
  NewsCreateInput,
  PaginatedResponse,
  TemplateCreateInput,
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
      status: params.status,
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
      status: params.status,
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

export async function createArticle(payload: ArticleCreateInput): Promise<Material> {
  const response = await apiClient.post<Material>('/materials/articles', payload);
  return response.data;
}

export async function createNews(payload: NewsCreateInput): Promise<Material> {
  const response = await apiClient.post<Material>('/materials/news', payload);
  return response.data;
}

export async function createTemplate(payload: TemplateCreateInput): Promise<Material> {
  const response = await apiClient.post<Material>('/materials/templates', payload);
  return response.data;
}

export async function uploadAttachment(materialId: string, file: File): Promise<AttachmentResponse> {
  const formData = new FormData();
  formData.append('file', file);
  const response = await apiClient.post<AttachmentResponse>(
    `/materials/${materialId}/attachments`,
    formData,
    // Перекрываем глобальный application/json, чтобы axios выставил multipart-boundary.
    { headers: { 'Content-Type': 'multipart/form-data' } },
  );
  return response.data;
}

export async function deleteAttachment(materialId: string, attachmentId: string): Promise<void> {
  await apiClient.delete(`/materials/${materialId}/attachments/${attachmentId}`);
}

export async function downloadAttachment(
  materialId: string,
  attachment: { id: string; filename: string },
): Promise<void> {
  const response = await apiClient.get<Blob>(
    `/materials/${materialId}/attachments/${attachment.id}`,
    { responseType: 'blob' },
  );
  const url = URL.createObjectURL(response.data);
  const link = document.createElement('a');
  link.href = url;
  link.download = attachment.filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
}

export async function publishMaterial(materialId: string): Promise<Material> {
  const response = await apiClient.post<Material>(`/materials/${materialId}/publish`);
  return response.data;
}

export async function updateMaterial(
  materialId: string,
  payload: {
    title?: string;
    summary?: string | null;
    content?: string;
    content_format?: MaterialContentFormat;
  },
): Promise<Material> {
  const response = await apiClient.patch<Material>(`/materials/${materialId}`, payload);
  return response.data;
}

export async function archiveMaterial(materialId: string): Promise<Material> {
  const response = await apiClient.post<Material>(`/materials/${materialId}/archive`);
  return response.data;
}

export async function restoreMaterial(materialId: string): Promise<Material> {
  const response = await apiClient.post<Material>(`/materials/${materialId}/restore`);
  return response.data;
}

export async function deleteMaterial(materialId: string): Promise<void> {
  await apiClient.delete(`/materials/${materialId}`);
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
