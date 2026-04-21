// src/hooks/useNotificationSSE.ts

import { useEffect } from "react";
import { useNotificationStore } from "@/store/notificationStore";
import type { Notification } from "@/api/notifications";

export function useNotificationSSE() {
  const addNotification = useNotificationStore((s) => s.addNotification);

  useEffect(() => {
    const token = localStorage.getItem("access_token");
    if (!token) {
      return;
    }
    const apiBaseUrl =
      (import.meta.env.VITE_API_URL as string | undefined)?.replace(/\/$/, "") ||
      "/api/v1";
    const eventSource = new EventSource(
      `${apiBaseUrl}/notifications/stream?token=${token}`
    );

    eventSource.onmessage = (event) => {
      try {
        const notification: Notification = JSON.parse(event.data);
        addNotification(notification);

        // Браузерное уведомление
        if (Notification.permission === "granted") {
          new window.Notification(notification.title, {
            body: notification.message,
          });
        }
      } catch {
        // heartbeat, игнорируем
      }
    };

    eventSource.onerror = () => {
      eventSource.close();
      // Переподключение через 5 сек
      setTimeout(() => {
        // reconnect logic
      }, 5000);
    };

    return () => eventSource.close();
  }, [addNotification]);
}
