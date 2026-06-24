import { useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { Archive, ArrowLeft, Check, Pencil, Trash2, X } from 'lucide-react';

import * as materialsApi from '@/api/materials';
import { getErrorMessage } from '@/api/client';
import { Markdown } from '@/components/Markdown';
import { MarkdownEditor } from '@/components/MarkdownEditor';
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

  const [editing, setEditing] = useState(false);
  const [title, setTitle] = useState('');
  const [summary, setSummary] = useState('');
  const [content, setContent] = useState('');
  const [error, setError] = useState<string | null>(null);

  const { data, isLoading, isError } = useQuery({
    queryKey: ['material', id],
    queryFn: () => materialsApi.getMaterial(id as string),
    enabled: !!id,
  });

  const update = useMutation({
    mutationFn: (payload: { title?: string; summary?: string | null; content?: string }) =>
      materialsApi.updateMaterial(id as string, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['material', id] });
      queryClient.invalidateQueries({ queryKey: ['materials'] });
      setEditing(false);
    },
    onError: (e) => setError(getErrorMessage(e)),
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
  const busy = archive.isPending || remove.isPending || update.isPending;

  const startEdit = () => {
    setError(null);
    setTitle(data.title);
    setSummary(data.summary ?? '');
    setContent(data.content);
    setEditing(true);
  };

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

  const handleApply = () => {
    setError(null);
    if (!title.trim() || !content.trim()) {
      setError('Заголовок и текст не могут быть пустыми');
      return;
    }
    // Отправляем только реально изменённые поля; если изменений нет —
    // просто выходим из режима правки, не помечая статью изменённой.
    const payload: { title?: string; summary?: string | null; content?: string } = {};
    if (title !== data.title) payload.title = title;
    if ((summary || '') !== (data.summary ?? '')) payload.summary = summary || null;
    if (content !== data.content) payload.content = content;

    if (Object.keys(payload).length === 0) {
      setEditing(false);
      return;
    }
    update.mutate(payload);
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
          {new Date(data.updated_at).getTime() !== new Date(data.created_at).getTime() && (
            <span>
              Изменено:{' '}
              {new Date(data.updated_at).toLocaleString('ru-RU', {
                dateStyle: 'short',
                timeStyle: 'short',
              })}
              {data.updated_by_name && ` · ${data.updated_by_name}`}
            </span>
          )}

          {isAuthor && !editing && (
            <div className="ml-auto flex items-center gap-2">
              <button
                type="button"
                title="Редактировать"
                aria-label="Редактировать"
                onClick={startEdit}
                disabled={busy}
                className="rounded p-1.5 text-gray-500 transition hover:bg-gray-100 hover:text-gray-700 disabled:opacity-40"
              >
                <Pencil size={16} />
              </button>
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

          {isAuthor && editing && (
            <div className="ml-auto flex items-center gap-2">
              <button
                type="button"
                onClick={handleApply}
                disabled={update.isPending}
                className="btn-primary flex items-center gap-1 px-3 py-1 text-xs"
              >
                <Check size={14} /> {update.isPending ? 'Сохранение...' : 'Применить'}
              </button>
              <button
                type="button"
                onClick={() => {
                  setEditing(false);
                  setError(null);
                }}
                disabled={update.isPending}
                className="btn-secondary flex items-center gap-1 px-3 py-1 text-xs"
              >
                <X size={14} /> Отменить
              </button>
            </div>
          )}
        </div>

        {error && <div className="mt-3 rounded-md bg-red-50 p-3 text-sm text-red-600">{error}</div>}

        {editing ? (
          <div className="mt-3 space-y-3">
            <div>
              <label className="label" htmlFor="edit-title">
                Заголовок
              </label>
              <input
                id="edit-title"
                className="input"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
              />
            </div>
            <div>
              <label className="label" htmlFor="edit-summary">
                Краткое описание
              </label>
              <input
                id="edit-summary"
                className="input"
                value={summary}
                onChange={(e) => setSummary(e.target.value)}
              />
            </div>
            <div>
              <label className="label" htmlFor="edit-content">
                Текст (Markdown)
              </label>
              <MarkdownEditor id="edit-content" value={content} onChange={setContent} />
            </div>
          </div>
        ) : (
          <>
            <h1 className="mt-2 text-2xl font-bold text-gray-900">{data.title}</h1>
            {data.summary && <p className="mt-1 text-gray-600">{data.summary}</p>}

            <div className="mt-4 border-t pt-4">
              {data.content_format === 'markdown' ? (
                <Markdown>{data.content}</Markdown>
              ) : (
                <p className="text-sm text-gray-500">
                  Формат HTML пока не поддерживается для просмотра.
                </p>
              )}
            </div>
          </>
        )}
      </article>
    </div>
  );
}
