import { Link, useNavigate, useParams } from 'react-router-dom';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { Archive, ArrowLeft, BookText, CheckCircle2, Pencil, Trash2 } from 'lucide-react';

import * as checklistsApi from '@/api/checklists';
import { getErrorMessage } from '@/api/client';
import { useAuth } from '@/hooks/useAuth';
import { ChecklistBuilderDialog } from '@/components/checklists/ChecklistBuilderDialog';
import { checklistAnswerTypeShort, checklistStatusLabels } from '@/utils/checklistLabels';

export function ChecklistDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { role } = useAuth();
  const isOwner = role === 'org_owner';

  const { data, isLoading, isError } = useQuery({
    queryKey: ['checklist', id],
    queryFn: () => checklistsApi.getChecklist(id as string),
    enabled: !!id,
  });

  const invalidate = () => {
    queryClient.invalidateQueries({ queryKey: ['checklist', id] });
    queryClient.invalidateQueries({ queryKey: ['checklists'] });
  };

  const publish = useMutation({
    mutationFn: () => checklistsApi.publishChecklist(id as string),
    onSuccess: invalidate,
    onError: (e) => alert(getErrorMessage(e)),
  });
  const archive = useMutation({
    mutationFn: () => checklistsApi.archiveChecklist(id as string),
    onSuccess: invalidate,
    onError: (e) => alert(getErrorMessage(e)),
  });
  const remove = useMutation({
    mutationFn: () => checklistsApi.deleteChecklist(id as string),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['checklists'] });
      navigate('/checks');
    },
    onError: (e) => alert(getErrorMessage(e)),
  });

  if (isLoading) {
    return <div className="card h-40 animate-pulse" />;
  }
  if (isError || !data) {
    return (
      <div className="card text-center">
        <p className="text-gray-500">Чек-лист не найден</p>
        <Link to="/checks" className="btn-secondary mt-4 inline-block">
          К списку
        </Link>
      </div>
    );
  }

  const busy = publish.isPending || archive.isPending || remove.isPending;

  const handleDelete = () => {
    if (window.confirm('Удалить чек-лист без возможности восстановления?')) remove.mutate();
  };

  return (
    <div className="space-y-4">
      <Link to="/checks" className="inline-flex items-center gap-1 text-sm text-gray-600 hover:text-gray-900">
        <ArrowLeft size={16} /> К проверкам и чек-листам
      </Link>

      <article className="card">
        <div className="flex flex-wrap items-center gap-3 text-xs text-gray-500">
          <span className="rounded-full bg-gray-100 px-2 py-1 uppercase tracking-wide">
            {checklistStatusLabels[data.status]}
          </span>
          <span>{data.items.length} пунктов</span>
          <span>{data.views_count} просмотров</span>
          {(data.organization_name || data.author_name) && (
            <span>Автор: {[data.organization_name, data.author_name].filter(Boolean).join(' · ')}</span>
          )}

          <div className="ml-auto flex items-center gap-2">
            <button
              type="button"
              className="btn-secondary flex items-center gap-1 px-3 py-1 text-xs"
              disabled
              title="Скоро: проведение проверки по чек-листу"
            >
              <CheckCircle2 size={14} /> Использовать
            </button>
            {isOwner && (
              <>
                <ChecklistBuilderDialog
                  checklist={data}
                  trigger={
                    <button
                      type="button"
                      title="Редактировать"
                      aria-label="Редактировать"
                      className="rounded p-1.5 text-gray-500 transition hover:bg-gray-100 hover:text-gray-700"
                    >
                      <Pencil size={16} />
                    </button>
                  }
                />
                {data.status !== 'published' && (
                  <button
                    type="button"
                    title="Опубликовать"
                    aria-label="Опубликовать"
                    onClick={() => publish.mutate()}
                    disabled={busy}
                    className="rounded p-1.5 text-gray-500 transition hover:bg-gray-100 hover:text-gray-700 disabled:opacity-40"
                  >
                    <CheckCircle2 size={16} />
                  </button>
                )}
                {data.status !== 'archived' && (
                  <button
                    type="button"
                    title="В архив"
                    aria-label="В архив"
                    onClick={() => archive.mutate()}
                    disabled={busy}
                    className="rounded p-1.5 text-gray-500 transition hover:bg-gray-100 hover:text-gray-700 disabled:opacity-40"
                  >
                    <Archive size={16} />
                  </button>
                )}
                <button
                  type="button"
                  title="Удалить"
                  aria-label="Удалить"
                  onClick={handleDelete}
                  disabled={busy}
                  className="rounded p-1.5 text-gray-500 transition hover:bg-red-50 hover:text-red-600 disabled:opacity-40"
                >
                  <Trash2 size={16} />
                </button>
              </>
            )}
          </div>
        </div>

        <h1 className="mt-2 text-2xl font-bold text-gray-900">{data.title}</h1>
        {data.description && <p className="mt-1 text-gray-600">{data.description}</p>}

        <ol className="mt-5 space-y-3">
          {data.items.map((item, index) => (
            <li key={item.id} className="rounded-lg border border-gray-200 p-3">
              <div className="flex items-start gap-3">
                <span className="mt-0.5 text-sm font-medium text-gray-400">{index + 1}</span>
                <div className="min-w-0 flex-1">
                  <p className="text-gray-900">
                    {item.text}
                    {item.required && <span className="ml-1 text-red-500" title="Обязательный">*</span>}
                  </p>
                  <div className="mt-2 flex flex-wrap items-center gap-2 text-xs text-gray-500">
                    <span className="rounded-full bg-primary-50 px-2 py-0.5 font-medium text-primary-700">
                      {checklistAnswerTypeShort[item.answer_type]}
                    </span>
                    {item.help_text && <span className="text-gray-400">{item.help_text}</span>}
                  </div>
                  {(item.reference_material_id || item.reference_note) && (
                    <div className="mt-2 flex flex-wrap items-center gap-1.5 text-xs text-gray-500">
                      <BookText className="h-3.5 w-3.5 shrink-0 text-gray-400" />
                      {item.reference_material_id && (
                        <Link
                          to={`/materials/${item.reference_material_id}`}
                          className="text-primary-600 underline"
                        >
                          {item.reference_material_title ?? 'Материал'}
                        </Link>
                      )}
                      {item.reference_note && <span>{item.reference_note}</span>}
                    </div>
                  )}
                </div>
              </div>
            </li>
          ))}
        </ol>
      </article>
    </div>
  );
}
