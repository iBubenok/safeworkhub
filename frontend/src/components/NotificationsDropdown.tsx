// src/components/NotificationsDropdown.tsx

import { useEffect, useRef } from "react";
import { Bell, BellDot, Check } from "lucide-react";
import { useNotificationStore } from "@/store/notificationStore";
import { useNotifications, useMarkAsRead, useMarkAllAsRead } from "@/hooks/useNotifications";
import { formatDistanceToNow } from "date-fns";
import { ru } from "date-fns/locale";

export function NotificationsDropdown() {
  const { notifications, unreadCount, isOpen, toggleOpen, setOpen } =
    useNotificationStore();

  const dropdownRef = useRef<HTMLDivElement>(null);
  const { isLoading } = useNotifications();
  const markAsRead = useMarkAsRead();
  const markAllAsRead = useMarkAllAsRead();

  // Закрытие по клику вне
  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, [setOpen]);

  const typeStyles = {
    info: "bg-blue-50 border-blue-200",
    warning: "bg-yellow-50 border-yellow-200",
    error: "bg-red-50 border-red-200",
    success: "bg-green-50 border-green-200",
  };

  return (
    <div className="relative" ref={dropdownRef}>
      {/* Кнопка */}
      <button
        onClick={toggleOpen}
        className="relative rounded-full p-2 hover:bg-gray-100 transition"
      >
        <Bell size={24} className="text-gray-900" />

        {unreadCount > 0 && (
          <span className="absolute -top-1 -right-1 flex h-5 w-5 items-center justify-center rounded-full bg-red-500 text-[10px] font-bold text-white">
            {unreadCount > 99 ? "99+" : unreadCount}
          </span>
        )}
      </button>

      {/* Dropdown */}
      {isOpen && (
        <div className="absolute right-0 mt-2 w-96 rounded-xl border border-gray-200 bg-white shadow-xl z-50">
          {/* Header */}
          <div className="flex items-center justify-between border-b px-4 py-3">
            <h3 className="text-sm font-semibold text-gray-900">
              Уведомления
              {unreadCount > 0 && (
                <span className="ml-2 rounded-full bg-red-100 px-2 py-0.5 text-xs text-red-600">
                  {unreadCount}
                </span>
              )}
            </h3>
            {unreadCount > 0 && (
              <button
                onClick={() => markAllAsRead.mutate()}
                className="flex items-center gap-1 text-xs text-blue-600 hover:text-blue-700"
              >
                <Check size={12} />
                Прочитать все
              </button>
            )}
          </div>

          {/* Список */}
          <div className="max-h-[400px] overflow-y-auto">
            {isLoading && (
              <div className="px-4 py-8 text-center text-sm text-gray-500">
                Загрузка...
              </div>
            )}

            {!isLoading && notifications.length === 0 && (
              <div className="px-4 py-8 text-center">
                <Bell size={32} className="mx-auto mb-2 text-gray-300" />
                <p className="text-sm text-gray-500">Уведомлений нет</p>
              </div>
            )}

            {notifications.map((n) => (
              <div
                key={n.id}
                onClick={() => !n.is_read && markAsRead.mutate(n.id)}
                className={`
                  cursor-pointer border-b border-l-4 px-4 py-3 transition hover:bg-gray-50
                  ${!n.is_read ? typeStyles[n.type] : "border-l-transparent"}
                `}
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <p
                      className={`text-sm ${
                        !n.is_read ? "font-semibold text-gray-900" : "text-gray-700"
                      }`}
                    >
                      {n.title}
                    </p>
                    <p className="mt-0.5 text-xs text-gray-500">{n.message}</p>
                    <p className="mt-1 text-[10px] text-gray-400">
                      {formatDistanceToNow(new Date(n.created_at), {
                        addSuffix: true,
                        locale: ru,
                      })}
                    </p>
                  </div>

                  {!n.is_read && (
                    <span className="ml-2 mt-1 h-2 w-2 flex-shrink-0 rounded-full bg-blue-500" />
                  )}
                </div>
              </div>
            ))}
          </div>

          {/* Footer */}
          <div className="border-t px-4 py-3 text-center">
            <button className="text-sm text-blue-600 hover:text-blue-700">
              Смотреть все уведомления
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
