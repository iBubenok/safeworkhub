/**
 * Основной layout для авторизованных пользователей.
 */

import { Outlet, NavLink, useNavigate } from 'react-router-dom';
import {
  LayoutDashboard,
  BookOpen,
  GraduationCap,
  Users,
  Settings,
  LogOut,
  Menu,
  X,
  Check,
  BookCheckIcon,
  Bell,
  BellDot
} from 'lucide-react';
import { useEffect, useRef, useState } from 'react';

import { useAuth } from '@/hooks/useAuth';
import { cn } from '@/utils/cn';

const navigation = [
  { name: 'Главная', href: '/dashboard', icon: LayoutDashboard },
  { name: 'Документы и журналы', href: '/materials', icon: BookOpen },
  { name: 'Проверки и чек-листы', href: '/checks', icon: Check },
  { name: 'Обучение', href: '/courses', icon: GraduationCap },
  { name: 'Отчеты', href: '/reports', icon: BookCheckIcon },
  { name: 'Пользователи', href: '/users', icon: Users },
  { name: 'Настройки', href: '/settings', icon: Settings },
];


export function NotificationsDropdown() {
  const [notificationsOpen, setNotificationsOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (
        dropdownRef.current &&
        !dropdownRef.current.contains(event.target as Node)
      ) {
        setNotificationsOpen(false);
      }
    }

    document.addEventListener("mousedown", handleClickOutside);
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, []);

  return (
    <div className="relative" ref={dropdownRef}>
      <button
        onClick={() => setNotificationsOpen(!notificationsOpen)}
        className="rounded-full p-2 hover:bg-gray-100 transition"
      >
        {!notificationsOpen ? (
          <Bell size={24} color="black" />
        ) : (
            <div style={{ position: 'relative' }}>
              <BellDot size={24} color="black" />
              <span style={{
                position: 'absolute',
                top: 4,
                right: 2,
                width: '8px',
                height: '8px',
                backgroundColor: 'red',
                borderRadius: '50%'
              }} />
          </div>
        )}
      </button>

      {notificationsOpen && (
        <div className="absolute right-0 mt-2 w-80 rounded-xl border border-gray-200 bg-white shadow-lg z-50">
          <div className="flex items-center justify-between border-b px-4 py-3">
            <h3 className="text-sm font-semibold text-gray-900">Уведомления</h3>
            <button className="text-xs text-blue-600 hover:text-blue-700">
              Отметить все
            </button>
          </div>

          <div className="max-h-96 overflow-y-auto">
            <button className="w-full px-4 py-3 text-left hover:bg-gray-50 transition border-b">
              <p className="text-sm font-medium text-gray-900">
                Новая проверка добавлена
              </p>
              <p className="text-xs text-gray-500 mt-1">
                Чек-лист по технике безопасности был обновлён.
              </p>
            </button>

            <button className="w-full px-4 py-3 text-left hover:bg-gray-50 transition border-b">
              <p className="text-sm font-medium text-gray-900">
                Напоминание
              </p>
              <p className="text-xs text-gray-500 mt-1">
                Завтра запланирована проверка оборудования.
              </p>
            </button>

            <button className="w-full px-4 py-3 text-left hover:bg-gray-50 transition">
              <p className="text-sm font-medium text-gray-900">
                Система
              </p>
              <p className="text-xs text-gray-500 mt-1">
                Новая версия чек-листов доступна для использования.
              </p>
            </button>
          </div>

          <div className="border-t px-4 py-3 text-center">
            <button className="text-sm text-blue-600 hover:text-blue-700">
              Смотреть все
            </button>
          </div>
        </div>
      )}
    </div>
  );
}



export function MainLayout() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Мобильное меню */}
      <div
        className={cn(
          'fixed inset-0 z-50 bg-gray-900/50 lg:hidden',
          sidebarOpen ? 'block' : 'hidden',
        )}
        onClick={() => setSidebarOpen(false)}
      />

      {/* Боковая панель */}
      <aside
        className={cn(
          'fixed inset-y-0 left-0 z-50 w-64 transform bg-white shadow-lg transition-transform lg:translate-x-0',
          sidebarOpen ? 'translate-x-0' : '-translate-x-full',
        )}
      >
        <div className="flex h-full flex-col">
          {/* Логотип */}
          <div className="flex h-16 items-center justify-between border-b px-4">
            <span className="text-xl font-bold text-primary-600">SafeWorkHub</span>
            <button
              className="rounded-md p-1 lg:hidden"
              onClick={() => setSidebarOpen(false)}
            >
              <X className="h-6 w-6" />
            </button>
          </div>

          {/* Навигация */}
          <nav className="flex-1 space-y-1 px-2 py-4">
            {navigation.map((item) => (
              <NavLink
                key={item.name}
                to={item.href}
                className={({ isActive }) =>
                  cn('nav-link', isActive && 'nav-link-active')
                }
                onClick={() => setSidebarOpen(false)}
              >
                <item.icon className="h-5 w-5" />
                {item.name}
              </NavLink>
            ))}
          </nav>

          {/* Профиль пользователя */}
          <div className="border-t p-4">
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-full bg-primary-100 text-primary-600">
                {user?.name?.charAt(0).toUpperCase()}
              </div>
              <div className="flex-1 truncate">
                <p className="truncate text-sm font-medium text-gray-900">
                  {user?.name}
                </p>
                <p className="truncate text-xs text-gray-500">{user?.email}</p>
              </div>
            </div>
            <button
              onClick={handleLogout}
              className="mt-3 flex w-full items-center gap-2 rounded-md px-3 py-2 text-sm text-gray-700 hover:bg-gray-100"
            >
              <LogOut className="h-4 w-4" />
              Выйти
            </button>
          </div>
        </div>
      </aside>

      {/* Основной контент */}
      <div className="lg:pl-64">
        {/* Шапка */}
        <header className="sticky top-0 z-40 flex h-16 items-center gap-4 border-b bg-white px-4 shadow-sm lg:px-6">
          <button
            className="rounded-md p-1 lg:hidden"
            onClick={() => setSidebarOpen(true)}>
            <Menu className="h-6 w-6" />
          </button>

          <div className="flex-1" />
          {/* Здесь можно добавить поиск, уведомления и т.д. */}

            <NotificationsDropdown />
            
        </header>

        {/* Контент страницы */}
        <main className="p-4 lg:p-6">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
