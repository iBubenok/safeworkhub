import { useState } from 'react';
import { useMutation, useQuery } from '@tanstack/react-query';
import { KeyRound, ShieldCheck, Server } from 'lucide-react';

import * as authApi from '@/api/auth';
import * as usersApi from '@/api/users';
import { handleActionError } from '@/api/errors';
import { toast } from '@/store/toastStore';
import { useAuth } from '@/hooks/useAuth';

function formatDateTime(iso: string | null | undefined): string {
  if (!iso) return 'ещё не менялся';
  return new Date(iso).toLocaleString('ru-RU', { dateStyle: 'medium', timeStyle: 'short' });
}

export function SettingsPage() {
  const { user, role, accessToken } = useAuth();

  const meQuery = useQuery({ queryKey: ['me'], queryFn: authApi.getCurrentUser });

  const [current, setCurrent] = useState('');
  const [next, setNext] = useState('');
  const [confirm, setConfirm] = useState('');
  const [error, setError] = useState<string | null>(null);

  const changePassword = useMutation({
    mutationFn: () => usersApi.changeOwnPassword({ current_password: current, new_password: next }),
    onSuccess: () => {
      toast.success('Пароль изменён');
      setCurrent('');
      setNext('');
      setConfirm('');
      setError(null);
      meQuery.refetch();
    },
    onError: (e) => handleActionError(e),
  });

  const submit = (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    if (next.length < 8) {
      setError('Новый пароль должен быть не короче 8 символов');
      return;
    }
    if (next !== confirm) {
      setError('Новый пароль и подтверждение не совпадают');
      return;
    }
    changePassword.mutate();
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Настройки и доступ</h1>
        <p className="mt-1 text-gray-600">Управление паролем и информация о сессии</p>
      </div>

      {/* Смена пароля */}
      <div className="card max-w-xl">
        <div className="flex items-center gap-3">
          <KeyRound className="h-5 w-5 text-primary-600" />
          <div>
            <p className="text-sm font-semibold text-gray-900">Смена пароля</p>
            <p className="text-sm text-gray-600">
              Последняя смена: {formatDateTime(meQuery.data?.password_changed_at)}
            </p>
          </div>
        </div>

        {error && <div className="mt-3 rounded-md bg-red-50 p-3 text-sm text-red-600">{error}</div>}

        <form className="mt-4 space-y-3" onSubmit={submit}>
          <div>
            <label className="label" htmlFor="cur-pass">
              Текущий пароль
            </label>
            <input
              id="cur-pass"
              type="password"
              className="input"
              value={current}
              onChange={(e) => setCurrent(e.target.value)}
              autoComplete="current-password"
              required
            />
          </div>
          <div>
            <label className="label" htmlFor="new-pass">
              Новый пароль
            </label>
            <input
              id="new-pass"
              type="password"
              className="input"
              value={next}
              onChange={(e) => setNext(e.target.value)}
              minLength={8}
              autoComplete="new-password"
              required
            />
          </div>
          <div>
            <label className="label" htmlFor="confirm-pass">
              Повторите новый пароль
            </label>
            <input
              id="confirm-pass"
              type="password"
              className="input"
              value={confirm}
              onChange={(e) => setConfirm(e.target.value)}
              minLength={8}
              autoComplete="new-password"
              required
            />
          </div>
          <div className="flex justify-end">
            <button type="submit" className="btn-primary" disabled={changePassword.isPending}>
              {changePassword.isPending ? 'Сохранение…' : 'Сменить пароль'}
            </button>
          </div>
        </form>
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
              <p className="text-sm text-gray-600">Токен доступа: {accessToken ? 'получен' : 'нет'}</p>
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
