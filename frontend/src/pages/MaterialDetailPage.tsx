import { Link, useNavigate, useParams } from 'react-router-dom';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { Archive, ArrowLeft, Trash2 } from 'lucide-react';

import * as materialsApi from '@/api/materials';
import { getErrorMessage } from '@/api/client';
import { Markdown } from '@/components/Markdown';
import { useAuth } from '@/hooks/useAuth';

const statusLabel: Record<string, string> = {
  published: 'Опубликован',
  archived: 'В архиве',
  draft: 'Черновик',
};

export function MaterialDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { user } = useAuth();

  const { data, isLoading, isError } = useQuery({
    queryKey: ['material', id],
    queryFn: () => materialsApi.getMaterial(id as string),
    enabled: !!id,
  });

  const archive = useMutation({
    mutationFn: () => materialsApi.archiveMaterial(id as string),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['material', id] });
      queryClient.invalidateQueries({ queryKey: ['materials'] });
    },
    onError: (e) => alert(getErrorMessage(e)),
  });

  const remove = useMutation({
    mutationFn: () => materialsApi.deleteMaterial(id as string),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['materials'] });
      navigate('/materials');
    },
    onError: (e) => alert(getErrorMessage(e)),
  });

  if (isLoading) {
    return <div className="card h-40 animate-pulse" />;
  }

  if (isError || !data) {
    return (
      <div className="card text-center">
        <p className="text-gray-500">Материал не найден</p>
        <Link to="/materials" className="btn-secondary mt-4 inline-block">
          К списку
        </Link>
      </div>
    );
  }

  const isAuthor = !!user && (user.id === data.author_id || user.is_superuser);
  const busy = archive.isPending || remove.isPending;

  const handleArchive = () => {
    if (window.confirm('Перенести статью в архив? Она пропадёт из общих списков.')) {
      archive.mutate();
    }
  };

  const handleDelete = () => {
    if (window.confirm('Удалить статью без возможности восстановления?')) {
      remove.mutate();
    }
  };

  return (
    <div className="space-y-4">
      <Link
        to="/materials"
        className="inline-flex items-center gap-1 text-sm text-gray-600 hover:text-gray-900"
      >
        <ArrowLeft size={16} /> К материалам
      </Link>

      <article className="card">
        <div className="flex flex-wrap items-center gap-3 text-xs text-gray-500">
          <span className="rounded-full bg-gray-100 px-2 py-1 uppercase tracking-wide">
            {statusLabel[data.status] ?? data.status}
          </span>
          {data.published_at && <span>{new Date(data.published_at).toLocaleDateString('ru-RU')}</span>}
          <span>{data.views_count} просмотров</span>
          {(data.organization_name || data.author_name) && (
            <span>
              Автор: {[data.organization_name, data.author_name].filter(Boolean).join(' · ')}
            </span>
          )}

          {isAuthor && (
            <div className="ml-auto flex items-center gap-2">
              {data.status !== 'archived' && (
                <button
                  type="button"
                  title="В архив"
                  aria-label="В архив"
                  onClick={handleArchive}
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
            </div>
          )}
        </div>

        <h1 className="mt-2 text-2xl font-bold text-gray-900">{data.title}</h1>
        {data.summary && <p className="mt-1 text-gray-600">{data.summary}</p>}

        <div className="mt-4 border-t pt-4">
          {data.content_format === 'markdown' ? (
            <Markdown>{data.content}</Markdown>
          ) : (
            <p className="text-sm text-gray-500">Формат HTML пока не поддерживается для просмотра.</p>
          )}
        </div>
      </article>
    </div>
  );
}
