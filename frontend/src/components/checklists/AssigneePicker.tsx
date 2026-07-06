import { useQuery } from '@tanstack/react-query';

import * as usersApi from '@/api/users';

/**
 * Список активных сотрудников организации с чекбоксами для выбора назначенных.
 * `excludeIds` — кого не показывать (создатель проверки и/или текущий пользователь:
 * они и так редакторы, назначать их повторно не нужно).
 */
export function AssigneePicker({
  selected,
  onChange,
  excludeIds = [],
}: {
  selected: string[];
  onChange: (ids: string[]) => void;
  excludeIds?: string[];
}) {
  const membersQuery = useQuery({
    queryKey: ['org-members'],
    queryFn: usersApi.getOrgMembers,
    staleTime: 60_000,
  });

  const exclude = new Set(excludeIds);
  const members = (membersQuery.data ?? []).filter((m) => !exclude.has(m.id));

  const toggle = (id: string) => {
    onChange(selected.includes(id) ? selected.filter((x) => x !== id) : [...selected, id]);
  };

  if (membersQuery.isLoading) {
    return <p className="text-sm text-gray-500">Загрузка сотрудников…</p>;
  }
  if (members.length === 0) {
    return <p className="text-sm text-gray-500">В организации нет других сотрудников для назначения.</p>;
  }

  return (
    <div className="max-h-56 space-y-1 overflow-y-auto rounded-lg border border-gray-200 p-1">
      {members.map((m) => (
        <label
          key={m.id}
          className="flex cursor-pointer items-center gap-3 rounded-md px-2 py-2 hover:bg-gray-50"
        >
          <input
            type="checkbox"
            className="h-4 w-4 shrink-0"
            checked={selected.includes(m.id)}
            onChange={() => toggle(m.id)}
          />
          <span className="min-w-0 flex-1">
            <span className="block truncate text-sm font-medium text-gray-900">{m.name}</span>
            <span className="block truncate text-xs text-gray-500">{m.email}</span>
          </span>
        </label>
      ))}
    </div>
  );
}
