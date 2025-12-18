import { ShieldCheck, Server } from 'lucide-react';

import { useAuth } from '@/hooks/useAuth';

export function SettingsPage() {
  const { user, role, accessToken } = useAuth();

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Настройки и доступ</h1>
        <p className="mt-1 text-gray-600">
          Техническая информация о сессии и подсказки по эксплуатации
        </p>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <div className="card">
          <div className="flex items-center gap-3">
            <ShieldCheck className="h-5 w-5 text-primary-600" />
            <div>
              <p className="text-sm font-semibold text-gray-900">Текущий пользователь</p>
              <p className="text-sm text-gray-600">{user?.email}</p>
            </div>
          </div>
          <ul className="mt-3 space-y-1 text-sm text-gray-600">
            <li>Роль в организации: {role ?? 'не определена'}</li>
            <li>Организация: {user?.primary_organization_id ?? '—'}</li>
          </ul>
        </div>

        <div className="card">
          <div className="flex items-center gap-3">
            <Server className="h-5 w-5 text-primary-600" />
            <div>
              <p className="text-sm font-semibold text-gray-900">Состояние сессии</p>
              <p className="text-sm text-gray-600">
                Токен доступа: {accessToken ? 'получен' : 'нет'}
              </p>
            </div>
          </div>
          <p className="mt-3 text-sm text-gray-600">
            Обновление токена происходит автоматически через защищённый httpOnly cookie. При
            проблемах с авторизацией выйдите из системы и войдите снова.
          </p>
        </div>
      </div>
    </div>
  );
}
