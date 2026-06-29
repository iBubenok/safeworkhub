import { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { UserRound, Shield, Mail, Lock, Plus } from 'lucide-react';

import * as usersApi from '@/api/users';
import { getErrorMessage } from '@/api/client';
import { useAuth } from '@/hooks/useAuth';
import { roleLabel, roleLabels } from '@/utils/roleLabels';

export function UsersPage() {
  const queryClient = useQueryClient();
  const { role } = useAuth();
  const isOwner = role === 'org_owner';

  const [search, setSearch] = useState('');
  const [formError, setFormError] = useState<string | null>(null);
  const [newUser, setNewUser] = useState({
    name: '',
    email: '',
    password: '',
    role: 'member',
  });

  const usersQuery = useQuery({
    queryKey: ['users', search],
    queryFn: () => usersApi.searchUsers({ query: search }),
  });

  const createUser = useMutation({
    mutationFn: usersApi.createUser,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['users'] });
      setNewUser({ name: '', email: '', password: '', role: 'member' });
    },
    onError: (error) => setFormError(getErrorMessage(error)),
  });

  const deactivateUser = useMutation({
    mutationFn: usersApi.deactivateUser,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['users'] }),
  });

  const activateUser = useMutation({
    mutationFn: usersApi.activateUser,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['users'] }),
  });

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    setFormError(null);
    await createUser.mutateAsync(newUser);
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Пользователи организации</h1>
        <p className="mt-1 text-gray-600">Управление доступом и ролями</p>
      </div>

      <div className="card">
        <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
          <div className="relative flex-1">
            <input
              type="text"
              placeholder="Поиск по имени или email"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="input"
            />
          </div>
          {isOwner && (
            <button className="btn-primary" onClick={() => setSearch('')}>
              Сбросить фильтр
            </button>
          )}
        </div>
      </div>

      {isOwner && (
        <div className="card">
          <h3 className="card-title mb-3 text-lg">Создать пользователя</h3>
          {formError && (
            <div className="mb-3 rounded-md bg-red-50 p-3 text-sm text-red-600">
              {formError}
            </div>
          )}
          <form className="grid gap-3 md:grid-cols-2" onSubmit={handleCreate}>
            <div>
              <label className="label" htmlFor="userName">
                Имя
              </label>
              <div className="flex items-center gap-2">
                <UserRound className="h-5 w-5 text-gray-400" />
                <input
                  id="userName"
                  className="input"
                  value={newUser.name}
                  onChange={(e) => setNewUser((prev) => ({ ...prev, name: e.target.value }))}
                  required
                />
              </div>
            </div>
            <div>
              <label className="label" htmlFor="userEmail">
                Email
              </label>
              <div className="flex items-center gap-2">
                <Mail className="h-5 w-5 text-gray-400" />
                <input
                  id="userEmail"
                  className="input"
                  value={newUser.email}
                  onChange={(e) => setNewUser((prev) => ({ ...prev, email: e.target.value }))}
                  required
                  type="email"
                />
              </div>
            </div>
            <div>
              <label className="label" htmlFor="userPassword">
                Пароль
              </label>
              <div className="flex items-center gap-2">
                <Lock className="h-5 w-5 text-gray-400" />
                <input
                  id="userPassword"
                  className="input"
                  type="password"
                  value={newUser.password}
                  onChange={(e) => setNewUser((prev) => ({ ...prev, password: e.target.value }))}
                  minLength={8}
                  required
                />
              </div>
            </div>
            <div>
              <label className="label" htmlFor="userRole">
                Роль
              </label>
              <div className="flex items-center gap-2">
                <Shield className="h-5 w-5 text-gray-400" />
                <select
                  id="userRole"
                  className="input"
                  value={newUser.role}
                  onChange={(e) =>
                    setNewUser((prev) => ({ ...prev, role: e.target.value }))
                  }
                >
                  <option value="member">{roleLabels.member}</option>
                  <option value="org_owner">{roleLabels.org_owner}</option>
                </select>
              </div>
            </div>
            <div className="md:col-span-2 flex justify-end">
              <button className="btn-primary" type="submit" disabled={createUser.isPending}>
                <Plus className="mr-2 h-4 w-4" />
                {createUser.isPending ? 'Создание...' : 'Создать пользователя'}
              </button>
            </div>
          </form>
        </div>
      )}

      <div className="grid gap-3">
        {usersQuery.isLoading ? (
          <p className="text-sm text-gray-600">Загрузка пользователей...</p>
        ) : (
          usersQuery.data?.map((user) => (
            <div
              key={user.id}
              className="flex items-center justify-between rounded-md bg-white p-4 shadow-sm"
            >
              <div>
                <p className="text-sm font-semibold text-gray-900">{user.name}</p>
                <p className="text-xs text-gray-500">{user.email}</p>
                <p className="text-xs text-gray-500">{roleLabel(user.role)}</p>
                <p className="text-xs text-gray-500">
                  Статус: {user.is_active ? 'активен' : 'заблокирован'}
                </p>
              </div>
              {isOwner &&
                (user.is_active ? (
                  <button
                    className="btn-secondary"
                    onClick={() => deactivateUser.mutate(user.id)}
                    disabled={deactivateUser.isPending}
                  >
                    Деактивировать
                  </button>
                ) : (
                  <button
                    className="btn-primary"
                    onClick={() => activateUser.mutate(user.id)}
                    disabled={activateUser.isPending}
                  >
                    Активировать
                  </button>
                ))}
            </div>
          ))
        )}
      </div>
    </div>
  );
}
