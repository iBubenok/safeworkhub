import { apiClient } from './client';

export interface Notification {
  id: string;
  title: string;
  message: string;
  type: "info" | "warning" | "error" | "success";
  category: string;
  entity_type: string | null;
  entity_id: string | null;
  is_read: boolean;
  metadata: Record<string, unknown>;
  created_at: string;
}

export interface NotificationList {
  items: Notification[];
  unread_count: number;
  total: number;
}

export const notificationsApi = {
  getAll: (params?: { limit?: number; offset?: number; unread_only?: boolean }) =>
    apiClient.get<NotificationList>("/notifications", { params }),

  getUnreadCount: () =>
    apiClient.get<{ unread_count: number }>("/notifications/unread-count"),

  markAsRead: (id: string) =>
    apiClient.patch(`/notifications/${id}/read`),

  markAllAsRead: () =>
    apiClient.patch("/notifications/read-all"),

  delete: (id: string) =>
    apiClient.delete(`/notifications/${id}`),

  deleteMany: (ids: string[]) =>
    apiClient.post<{ deleted_count: number }>("/notifications/delete", { ids }),

  deleteAll: () =>
    apiClient.delete<{ deleted_count: number }>("/notifications"),
};