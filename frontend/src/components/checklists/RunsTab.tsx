import { useState } from 'react';
import { Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { ClipboardCheck, ClipboardList, Search, User } from 'lucide-react';

import * as runsApi from '@/api/checklistRuns';
import { checklistRunResultLabels, checklistRunStatusLabels } from '@/utils/checklistLabels';
import type { ChecklistRunListItem, ChecklistRunStatus } from '@/types';

const statusFilters: { value: ChecklistRunStatus; label: string }[] = [
  { value: 'in_progress', label: 'В процессе' },
  { value: 'completed', label: 'Завершённые' },
];

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString('ru-RU', { dateStyle: 'medium' });
}

function RunCard({ run }: { run: ChecklistRunListItem }) {
  return (
    <Link to={`/checks/runs/${run.id}`} className="card flex flex-col gap-3 transition-shadow hover:shadow-md">
      <div className="flex items-start gap-3">
        <ClipboardCheck className="h-5 w-5 shrink-0 text-primary-500" />
        <div className="min-w-0 flex-1">
          <p className="block font-medium text-gray-900 line-clamp-2">{run.title || run.checklist_title}</p>
          <p className="mt-1 text-sm text-gray-500 line-clamp-1">{run.checklist_title}</p>
          <div className="mt-2 flex flex-wrap items-center gap-x-3 gap-y-1.5 text-xs text-gray-500">
            <span className="rounded-full bg-gray-100 px-2 py-1 uppercase tracking-wide">
              {checklistRunStatusLabels[run.status]}
            </span>
            {run.result && (
              <span
                className={`rounded-full px-2 py-1 font-medium ${
                  run.result === 'passed' ? 'bg-green-50 text-green-700' : 'bg-red-50 text-red-700'
                }`}
              >
                {checklistRunResultLabels[run.result]}
                {run.score !== null && ` · ${run.score}%`}
              </span>
            )}
            <span>{formatDate(run.created_at)}</span>
          </div>
        </div>
      </div>
      {run.conducted_by_name && (
        <div className="mt-auto flex items-center gap-1.5 border-t border-gray-100 pt-2 text-xs text-gray-400">
          <User className="h-3.5 w-3.5 shrink-0" />
          <span className="truncate">{run.conducted_by_name}</span>
        </div>
      )}
    </Link>
  );
}

export function RunsTab({ emptyMessage = 'Проверки не найдены' }: { emptyMessage?: string } = {}) {
  const [status, setStatus] = useState<ChecklistRunStatus | null>(null);
  const [search, setSearch] = useState('');

  const query = useQuery({
    queryKey: ['checklist-runs', status, search],
    queryFn: () => runsApi.getRuns({ status: status ?? undefined, q: search || undefined }),
  });

  return (
    <div className="space-y-4">
      <div className="card">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
          <form onSubmit={(e) => e.preventDefault()} className="flex gap-3 sm:flex-1">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 h-5 w-5 -translate-y-1/2 text-gray-400" />
              <input
                type="text"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Поиск по названию проверки или чек-листа..."
                className="input pl-10"
              />
            </div>
            <button type="submit" className="btn-primary">
              Найти
            </button>
          </form>

          <div className="inline-flex shrink-0 self-start overflow-x-auto rounded-lg border border-gray-200 bg-gray-50 p-0.5 sm:ml-auto sm:self-auto">
            <button
              type="button"
              onClick={() => setStatus(null)}
              className={`whitespace-nowrap rounded-md px-3 py-1.5 text-sm font-medium transition-colors ${
                status === null ? 'bg-white text-primary-700 shadow-sm' : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              Все
            </button>
            {statusFilters.map((s) => (
              <button
                key={s.value}
                type="button"
                onClick={() => setStatus(s.value)}
                className={`whitespace-nowrap rounded-md px-3 py-1.5 text-sm font-medium transition-colors ${
                  status === s.value ? 'bg-white text-primary-700 shadow-sm' : 'text-gray-600 hover:text-gray-900'
                }`}
              >
                {s.label}
              </button>
            ))}
          </div>
        </div>
      </div>

      {query.isLoading ? (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {[...Array(3)].map((_, i) => (
            <div key={i} className="card h-28 animate-pulse" />
          ))}
        </div>
      ) : !query.data || query.data.items.length === 0 ? (
        <div className="card flex flex-col items-center gap-2 py-10 text-center">
          <ClipboardList className="h-8 w-8 text-gray-300" />
          <p className="text-gray-500">{emptyMessage}</p>
        </div>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {query.data.items.map((run) => (
            <RunCard key={run.id} run={run} />
          ))}
        </div>
      )}
    </div>
  );
}
