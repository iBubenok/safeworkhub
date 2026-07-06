import { useState } from 'react';
import { Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { Building2, ClipboardCheck, ClipboardList, Eye, Globe, ListChecks, Search } from 'lucide-react';

import * as checklistsApi from '@/api/checklists';
import { StartRunDialog } from '@/components/checklists/StartRunDialog';
import { usePermissions } from '@/hooks/usePermissions';
import { checklistStatusLabels } from '@/utils/checklistLabels';
import type { ChecklistListItem, ChecklistStatus } from '@/types';

const statusFilters: { value: ChecklistStatus; label: string }[] = [
  { value: 'published', label: 'Опубликованные' },
  { value: 'draft', label: 'Черновики' },
  { value: 'archived', label: 'Архив' },
];

function ChecklistCard({ checklist }: { checklist: ChecklistListItem }) {
  const [runOpen, setRunOpen] = useState(false);
  const published = checklist.status === 'published';

  return (
    <>
      <Link
        to={`/checks/checklists/${checklist.id}`}
        className="card flex flex-col gap-3 transition-shadow hover:shadow-md"
      >
        <div className="flex items-start gap-3">
          <ListChecks className="h-5 w-5 shrink-0 text-primary-500" />
          <div className="min-w-0 flex-1">
            <p className="block font-medium text-gray-900 line-clamp-2">{checklist.title}</p>
            {checklist.description && (
              <p className="mt-1 text-sm text-gray-500 line-clamp-2">{checklist.description}</p>
            )}
            <div className="mt-2 flex flex-wrap items-center gap-x-3 gap-y-1.5 text-xs text-gray-500">
              <span className="rounded-full bg-gray-100 px-2 py-1 uppercase tracking-wide">
                {checklistStatusLabels[checklist.status]}
              </span>
              {checklist.visibility === 'public' && (
                <span
                  className="inline-flex items-center gap-1 rounded-full bg-blue-50 px-2 py-1 font-medium text-blue-700"
                  title="Публичный — доступен всем организациям"
                >
                  <Globe className="h-3.5 w-3.5" />
                  Публичный
                </span>
              )}
              <span>{checklist.item_count} пунктов</span>
              <span className="inline-flex items-center gap-1" title="Просмотры">
                <Eye className="h-3.5 w-3.5" />
                {checklist.views_count}
              </span>
              <span className="inline-flex items-center gap-1" title="Проведено проверок">
                <ClipboardCheck className="h-3.5 w-3.5" />
                {checklist.runs_count}
              </span>
            </div>
          </div>
        </div>
        <button
          type="button"
          className="btn-secondary w-full"
          disabled={!published}
          title={
            published
              ? 'Провести проверку по чек-листу'
              : 'Проверку можно проводить только по опубликованному чек-листу'
          }
          onClick={(e) => {
            e.preventDefault();
            e.stopPropagation();
            setRunOpen(true);
          }}
        >
          Использовать
        </button>
        {checklist.organization_name && (
          <div className="mt-auto flex items-center gap-1.5 border-t border-gray-100 pt-2 text-xs text-gray-400">
            <Building2 className="h-3.5 w-3.5 shrink-0" />
            <span className="truncate" title={checklist.organization_name}>
              {checklist.organization_name}
            </span>
          </div>
        )}
      </Link>
      {/* Диалог вне <Link>: события из портала Radix всплывают по дереву React, */}
      {/* поэтому внутри ссылки клик по диалогу уводил бы на страницу чек-листа. */}
      <StartRunDialog checklistId={checklist.id} open={runOpen} onOpenChange={setRunOpen} />
    </>
  );
}

export function ChecklistsTab({ emptyMessage = 'Чек-листы не найдены' }: { emptyMessage?: string } = {}) {
  const { isOwner } = usePermissions();
  const [status, setStatus] = useState<ChecklistStatus>('published');
  const [search, setSearch] = useState('');

  const effectiveStatus = isOwner ? status : 'published';
  const query = useQuery({
    queryKey: ['checklists', effectiveStatus, search],
    queryFn: () => checklistsApi.getChecklists({ status: effectiveStatus, q: search || undefined }),
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
                placeholder="Поиск по названию или описанию..."
                className="input pl-10"
              />
            </div>
            <button type="submit" className="btn-primary">
              Найти
            </button>
          </form>

          {isOwner && (
            <div className="inline-flex shrink-0 self-start overflow-x-auto rounded-lg border border-gray-200 bg-gray-50 p-0.5 sm:ml-auto sm:self-auto">
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
          )}
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
          {query.data.items.map((checklist) => (
            <ChecklistCard key={checklist.id} checklist={checklist} />
          ))}
        </div>
      )}
    </div>
  );
}
