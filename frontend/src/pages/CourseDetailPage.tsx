import { useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { ArrowLeft, CheckCircle2, Clock3, Pencil, Save } from 'lucide-react';

import * as coursesApi from '@/api/courses';
import { handleActionError } from '@/api/errors';
import { ContentEditor } from '@/components/ContentEditor';
import { Markdown } from '@/components/Markdown';
import { toast } from '@/store/toastStore';
import { usePermissions } from '@/hooks/usePermissions';

export function CourseDetailPage() {
  const { id } = useParams<{ id: string }>();
  const courseId = Number(id);
  const queryClient = useQueryClient();
  const { isOwner } = usePermissions();

  const [editing, setEditing] = useState(false);
  const [form, setForm] = useState({ title: '', description: '', content: '' });

  const { data, isLoading, isError } = useQuery({
    queryKey: ['course', courseId],
    queryFn: () => coursesApi.getCourse(courseId),
    enabled: Number.isFinite(courseId),
  });

  const assignmentsQuery = useQuery({
    queryKey: ['my-assignments'],
    queryFn: coursesApi.myAssignments,
    staleTime: 30_000,
  });

  const invalidate = () => {
    queryClient.invalidateQueries({ queryKey: ['course', courseId] });
    queryClient.invalidateQueries({ queryKey: ['courses'] });
  };

  const save = useMutation({
    mutationFn: () =>
      coursesApi.updateCourse(courseId, {
        title: form.title,
        description: form.description || null,
        content: form.content || null,
      }),
    onSuccess: () => {
      setEditing(false);
      invalidate();
      toast.success('Курс сохранён');
    },
    onError: (e) => handleActionError(e),
  });

  const publish = useMutation({
    mutationFn: () => coursesApi.publishCourse(courseId),
    onSuccess: invalidate,
    onError: (e) => handleActionError(e),
  });

  const complete = useMutation({
    mutationFn: () => coursesApi.updateProgress(courseId, 100),
    onSuccess: () => {
      assignmentsQuery.refetch();
      toast.success('Курс отмечен как пройденный');
    },
    onError: (e) => handleActionError(e),
  });

  if (isLoading) return <div className="card h-40 animate-pulse" />;
  if (isError || !data) {
    return (
      <div className="card text-center">
        <p className="text-gray-500">Курс не найден</p>
        <Link to="/courses" className="btn-secondary mt-4 inline-block">
          К обучению
        </Link>
      </div>
    );
  }

  const assignment = assignmentsQuery.data?.find((a) => a.course_id === courseId);
  const startEdit = () => {
    setForm({ title: data.title, description: data.description ?? '', content: data.content ?? '' });
    setEditing(true);
  };

  return (
    <div className="space-y-4">
      <Link to="/courses" className="inline-flex items-center gap-1 text-sm text-gray-600 hover:text-gray-900">
        <ArrowLeft size={16} /> К обучению
      </Link>

      <article className="card">
        <div className="flex flex-wrap items-center gap-3 text-xs text-gray-500">
          <span className="rounded-full bg-gray-100 px-2 py-1 uppercase tracking-wide">
            {data.is_published ? 'Опубликован' : 'Черновик'}
          </span>
          <span className="inline-flex items-center gap-1">
            <Clock3 className="h-3.5 w-3.5" />
            {data.duration_minutes} мин
          </span>
          {assignment && <span>Ваш прогресс: {assignment.progress_percent}%</span>}

          <div className="ml-auto flex items-center gap-2">
            {isOwner && !editing && (
              <>
                <button
                  type="button"
                  className="btn-secondary flex items-center gap-1 px-3 py-1 text-xs"
                  onClick={startEdit}
                >
                  <Pencil size={14} /> Редактировать
                </button>
                {!data.is_published && (
                  <button
                    type="button"
                    className="btn-secondary flex items-center gap-1 px-3 py-1 text-xs"
                    onClick={() => publish.mutate()}
                    disabled={publish.isPending}
                  >
                    <CheckCircle2 size={14} /> Опубликовать
                  </button>
                )}
              </>
            )}
          </div>
        </div>

        {editing ? (
          <div className="mt-4 space-y-3">
            <div>
              <label className="label" htmlFor="edit-title">
                Название
              </label>
              <input
                id="edit-title"
                className="input"
                value={form.title}
                onChange={(e) => setForm((p) => ({ ...p, title: e.target.value }))}
              />
            </div>
            <div>
              <label className="label" htmlFor="edit-desc">
                Краткое описание
              </label>
              <textarea
                id="edit-desc"
                className="input min-h-[60px]"
                value={form.description}
                onChange={(e) => setForm((p) => ({ ...p, description: e.target.value }))}
              />
            </div>
            <div>
              <label className="label" htmlFor="edit-content">
                Содержимое курса
              </label>
              <ContentEditor
                id="edit-content"
                value={form.content}
                onChange={(v) => setForm((p) => ({ ...p, content: v }))}
              />
            </div>
            <div className="flex justify-end gap-2">
              <button type="button" className="btn-secondary" onClick={() => setEditing(false)}>
                Отмена
              </button>
              <button
                type="button"
                className="btn-primary flex items-center gap-1"
                onClick={() => save.mutate()}
                disabled={save.isPending}
              >
                <Save size={16} /> {save.isPending ? 'Сохранение…' : 'Сохранить'}
              </button>
            </div>
          </div>
        ) : (
          <>
            <h1 className="mt-2 text-2xl font-bold text-gray-900">{data.title}</h1>
            {data.description && <p className="mt-1 text-gray-600">{data.description}</p>}

            <div className="mt-4 border-t pt-4">
              {data.content ? (
                <Markdown>{data.content}</Markdown>
              ) : (
                <p className="text-sm text-gray-500">Содержимое курса пока не заполнено.</p>
              )}
            </div>

            {assignment && assignment.status !== 'completed' && (
              <div className="mt-6 border-t pt-4">
                <button
                  type="button"
                  className="btn-primary flex items-center gap-1"
                  onClick={() => complete.mutate()}
                  disabled={complete.isPending}
                >
                  <CheckCircle2 size={16} /> Завершить курс
                </button>
              </div>
            )}
            {assignment && assignment.status === 'completed' && (
              <div className="mt-6 flex items-center gap-2 border-t pt-4 text-sm text-green-700">
                <CheckCircle2 size={16} /> Курс пройден
              </div>
            )}
          </>
        )}
      </article>
    </div>
  );
}
