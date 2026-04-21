// src/hooks/useNotifications.ts

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { notificationsApi } from "@/api/notifications";
import { useNotificationStore } from "@/store/notificationStore";
import { useEffect } from "react";

export function useNotifications(limit = 20) {
  const setNotifications = useNotificationStore((s) => s.setNotifications);
  const setUnreadCount = useNotificationStore((s) => s.setUnreadCount);

  const query = useQuery({
    queryKey: ["notifications", limit],
    queryFn: () => notificationsApi.getAll({ limit }),
    refetchInterval: 30_000, // Фоллбэк: каждые 30 сек
  });

  useEffect(() => {
    if (query.data) {
      setNotifications(query.data.data.items);
      setUnreadCount(query.data.data.unread_count);
    }
  }, [query.data, setNotifications, setUnreadCount]);

  return query;
}

export function useMarkAsRead() {
  const queryClient = useQueryClient();
  const markAsRead = useNotificationStore((s) => s.markAsRead);

  return useMutation({
    mutationFn: notificationsApi.markAsRead,
    onSuccess: (_, id) => {
      markAsRead(id);
      queryClient.invalidateQueries({ queryKey: ["notifications"] });
    },
  });
}

export function useMarkAllAsRead() {
  const queryClient = useQueryClient();
  const markAllAsRead = useNotificationStore((s) => s.markAllAsRead);

  return useMutation({
    mutationFn: notificationsApi.markAllAsRead,
    onSuccess: () => {
      markAllAsRead();
      queryClient.invalidateQueries({ queryKey: ["notifications"] });
    },
  });
}