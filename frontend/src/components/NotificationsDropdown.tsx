// src/components/NotificationsDropdown.tsx

import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Bell, Check, ChevronRight, ExternalLink, MoreHorizontal, Trash2 } from "lucide-react";
import { useNotificationStore } from "@/store/notificationStore";
import type { Notification } from "@/api/notifications";
import {
  useNotifications,
  useMarkAsRead,
  useMarkAllAsRead,
  useDeleteNotification,
  useDeleteAllNotifications,
} from "@/hooks/useNotifications";
import { formatDistanceToNow } from "date-fns";
import { ru } from "date-fns/locale";

// Карта переходов к сущностям платформы по их типу.
//
// Это механизм «ссылки на сущность»: источник (например, уведомление) хранит не
// готовый URL, а пару «тип объекта (entity_type) + его идентификатор (entity_id)».
// По типу здесь строится внутренний маршрут к конкретному объекту. Так можно
// ссылаться на любую сущность платформы, не зашивая URL в данные, — он остаётся
// валидным, даже если структура маршрутов в будущем поменяется.
//
// Чтобы добавить новый тип: заведите запись `тип: (id) => '/путь/' + id`
// и убедитесь, что соответствующий маршрут существует во фронтенде.
//
// Курс пока не добавлен: на бэкенде нет эндпоинта получения курса по id
// (есть только список и операции /{id}/publish, /{id}/assign, /{id}/progress).
const entityRoutes: Record<string, (id: string) => string> = {
  // Материал/статья → страница просмотра /materials/:id (MaterialDetailPage).
  material: (id) => `/materials/${id}`,
};

// Определяет, куда ведёт уведомление. Приоритет: внешний URL -> внутренний путь -> сущность.
function notificationHref(n: Notification): { url: string; external: boolean } | null {
  const external = n.metadata?.external_url;
  if (typeof external === "string" && external.startsWith("https://")) {
    return { url: external, external: true };
  }
  const internal = n.metadata?.url;
  if (typeof internal === "string" && internal.startsWith("/")) {
    return { url: internal, external: false };
  }
  if (n.entity_type && n.entity_id) {
    const buildRoute = entityRoutes[n.entity_type];
    if (buildRoute) {
      return { url: buildRoute(n.entity_id), external: false };
    }
  }
  return null;
}

export function NotificationsDropdown() {
  const { notifications, unreadCount, isOpen, toggleOpen, setOpen } =
    useNotificationStore();

  const dropdownRef = useRef<HTMLDivElement>(null);
  const menuRef = useRef<HTMLDivElement>(null);
  const [menuOpen, setMenuOpen] = useState(false);
  const navigate = useNavigate();
  const { isLoading } = useNotifications();
  const markAsRead = useMarkAsRead();
  const markAllAsRead = useMarkAllAsRead();
  const deleteNotification = useDeleteNotification();
  const deleteAll = useDeleteAllNotifications();

  // Клик по уведомлению: помечаем прочитанным и, если есть назначение, переходим.
  function handleClick(n: Notification) {
    if (!n.is_read) markAsRead.mutate(n.id);
    const href = notificationHref(n);
    if (!href) return;
    if (href.external) {
      window.open(href.url, "_blank", "noopener,noreferrer");
    } else {
      setOpen(false);
      navigate(href.url);
    }
  }

  // Удаление одного уведомления: stopPropagation, чтобы клик не сработал как переход.
  function handleDelete(e: React.MouseEvent, id: string) {
    e.stopPropagation();
    deleteNotification.mutate(id);
  }

  // Закрытие по клику вне: сначала меню действий, затем сам дропдаун.
  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      const target = e.target as Node;
      if (menuRef.current && !menuRef.current.contains(target)) {
        setMenuOpen(false);
      }
      if (dropdownRef.current && !dropdownRef.current.contains(target)) {
        setOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, [setOpen]);

  // Закрытие дропдауна сбрасывает и состояние меню действий.
  useEffect(() => {
    if (!isOpen) setMenuOpen(false);
  }, [isOpen]);

  // На мобильной версии блокируем прокрутку страницы за окном (как у модалки).
  // Реагируем на изменение ширины, пока окно открыто (например, ресайз окна).
  useEffect(() => {
    if (!isOpen) return;
    const mq = window.matchMedia("(max-width: 639px)");
    const prev = document.body.style.overflow;
    const apply = () => {
      document.body.style.overflow = mq.matches ? "hidden" : prev;
    };
    apply();
    mq.addEventListener("change", apply);
    return () => {
      mq.removeEventListener("change", apply);
      document.body.style.overflow = prev;
    };
  }, [isOpen]);

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
        <>
          <button
            aria-label="Закрыть уведомления"
            className="fixed inset-0 z-40 bg-black/40 sm:hidden"
            onClick={() => setOpen(false)}
            type="button"
          />

          <div className="fixed left-3 right-3 top-16 z-50 max-h-[calc(100dvh-5rem)] overflow-hidden rounded-2xl border border-gray-200 bg-white shadow-2xl sm:absolute sm:left-auto sm:right-0 sm:mt-2 sm:w-96 sm:max-h-[32rem]">
            {/* Header */}
            <div className="flex items-center justify-between border-b px-3 py-3 sm:px-4">
              <h3 className="text-sm font-semibold text-gray-900 sm:text-base">
                Уведомления
                {unreadCount > 0 && (
                  <span className="ml-2 rounded-full bg-red-100 px-2 py-0.5 text-[11px] text-red-600 sm:text-xs">
                    {unreadCount}
                  </span>
                )}
              </h3>
              {notifications.length > 0 && (
                <div className="relative" ref={menuRef}>
                  <button
                    type="button"
                    aria-label="Действия с уведомлениями"
                    aria-haspopup="menu"
                    aria-expanded={menuOpen}
                    onClick={() => setMenuOpen((v) => !v)}
                    className="rounded-full p-1.5 text-gray-500 transition hover:bg-gray-100"
                  >
                    <MoreHorizontal size={18} />
                  </button>

                  {menuOpen && (
                    <div
                      role="menu"
                      className="absolute right-0 z-50 mt-1 w-48 overflow-hidden rounded-lg border border-gray-200 bg-white py-1 shadow-lg"
                    >
                      {unreadCount > 0 && (
                        <button
                          type="button"
                          role="menuitem"
                          onClick={() => {
                            markAllAsRead.mutate();
                            setMenuOpen(false);
                          }}
                          className="flex w-full items-center gap-2 px-3 py-2 text-left text-sm text-gray-700 transition hover:bg-gray-50"
                        >
                          <Check size={16} className="text-blue-600" />
                          Прочитать все
                        </button>
                      )}
                      <button
                        type="button"
                        role="menuitem"
                        onClick={() => {
                          deleteAll.mutate();
                          setMenuOpen(false);
                        }}
                        className="flex w-full items-center gap-2 px-3 py-2 text-left text-sm text-red-600 transition hover:bg-red-50"
                      >
                        <Trash2 size={16} />
                        Очистить все
                      </button>
                    </div>
                  )}
                </div>
              )}
            </div>

            {/* Список */}
            <div className="max-h-[calc(100dvh-12rem)] overflow-y-auto sm:max-h-[24rem]">
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

              {notifications.map((n) => {
                const href = notificationHref(n);
                return (
                <div
                  key={n.id}
                  onClick={() => handleClick(n)}
                  className={`
                  cursor-pointer border-b border-l-4 px-3 py-3 transition hover:bg-gray-50 sm:px-4
                  ${!n.is_read ? typeStyles[n.type] : "border-l-transparent"}
                `}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <p
                        className={`text-sm leading-5 ${
                          !n.is_read ? "font-semibold text-gray-900" : "text-gray-700"
                        }`}
                      >
                        {n.title}
                      </p>
                      <p className="mt-0.5 text-xs leading-5 text-gray-500">
                        {n.message}
                      </p>
                      <p className="mt-1 text-[10px] text-gray-400">
                        {formatDistanceToNow(new Date(n.created_at), {
                          addSuffix: true,
                          locale: ru,
                        })}
                      </p>
                    </div>

                    <div className="ml-2 mt-1 flex flex-shrink-0 items-center gap-2">
                      {!n.is_read && (
                        <span className="h-2 w-2 rounded-full bg-blue-500" />
                      )}
                      {href &&
                        (href.external ? (
                          <ExternalLink size={14} className="text-gray-400" />
                        ) : (
                          <ChevronRight size={14} className="text-gray-400" />
                        ))}
                      <button
                        type="button"
                        aria-label="Удалить уведомление"
                        onClick={(e) => handleDelete(e, n.id)}
                        className="rounded p-1 text-gray-400 transition hover:bg-red-50 hover:text-red-600"
                      >
                        <Trash2 size={14} />
                      </button>
                    </div>
                  </div>
                </div>
                );
              })}
            </div>
          </div>
        </>
      )}
    </div>
  );
}
