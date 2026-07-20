import { useState } from 'react';
import * as Dialog from '@radix-ui/react-dialog';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { Plus, X } from 'lucide-react';

import * as coursesApi from '@/api/courses';
import { getActionErrorMessage } from '@/api/errors';
import { ContentEditor } from '@/components/ContentEditor';

/** Кнопка «+ Создать курс» + модальное окно с формой создания (как у материалов). */
export function CreateCourseDialog() {
  const [open, setOpen] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [form, setForm] = useState({
    title: '',
    description: '',
    content: '',
    duration_minutes: 0,
    training_basis: '',
    training_basis_url: '',
  });

  const queryClient = useQueryClient();

  const reset = () => {
    setForm({ title: '', description: '', content: '', duration_minutes: 0, training_basis: '', training_basis_url: '' });
    setError(null);
  };

  const create = useMutation({
    mutationFn: async (publish: boolean) => {
      const course = await coursesApi.createCourse({
        title: form.title,
        description: form.description || null,
        content: form.content || null,
        duration_minutes: form.duration_minutes,
        training_basis: form.training_basis || null,
        training_basis_url: form.training_basis_url || null,
      });
      if (publish) {
        await coursesApi.publishCourse(course.id);
      }
      return course;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['courses'] });
      reset();
      setOpen(false);
    },
    onError: (e) => setError(getActionErrorMessage(e)),
  });

  const submit = (publish: boolean) => {
    setError(null);
    if (!form.title.trim()) {
      setError('Укажите название курса');
      return;
    }
    create.mutate(publish);
  };

  return (
    <Dialog.Root
      open={open}
      onOpenChange={(next) => {
        setOpen(next);
        if (!next) reset();
      }}
    >
      <Dialog.Trigger asChild>
        <button type="button" className="btn-primary flex items-center gap-2">
          <Plus size={18} /> Создать курс
        </button>
      </Dialog.Trigger>

      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 z-[60] bg-black/40" />
        <Dialog.Content className="fixed left-1/2 top-1/2 z-[70] flex max-h-[85vh] w-[calc(100vw-2rem)] max-w-2xl -translate-x-1/2 -translate-y-1/2 flex-col overflow-hidden rounded-2xl bg-white shadow-2xl focus:outline-none">
          <div className="flex items-center justify-between border-b px-5 py-4">
            <Dialog.Title className="text-lg font-semibold text-gray-900">Создать курс</Dialog.Title>
            <Dialog.Close asChild>
              <button
                type="button"
                aria-label="Закрыть"
                className="rounded p-1 text-gray-500 transition hover:bg-gray-100 hover:text-gray-700"
              >
                <X size={18} />
              </button>
            </Dialog.Close>
          </div>

          <div className="overflow-y-auto px-5 py-4">
            {error && <div className="mb-3 rounded-md bg-red-50 p-3 text-sm text-red-600">{error}</div>}

            <form
              className="space-y-3"
              onSubmit={(e) => {
                e.preventDefault();
                submit(false);
              }}
            >
              <div className="grid gap-3 md:grid-cols-2">
                <div>
                  <label className="label" htmlFor="course-title">
                    Название
                  </label>
                  <input
                    id="course-title"
                    className="input"
                    value={form.title}
                    onChange={(e) => setForm((p) => ({ ...p, title: e.target.value }))}
                    required
                  />
                </div>
                <div>
                  <label className="label" htmlFor="course-duration">
                    Длительность (мин)
                  </label>
                  <input
                    id="course-duration"
                    className="input"
                    type="number"
                    min={0}
                    value={form.duration_minutes}
                    onChange={(e) => setForm((p) => ({ ...p, duration_minutes: Number(e.target.value) }))}
                  />
                </div>
              </div>

              <div>
                <label className="label" htmlFor="course-description">
                  Краткое описание
                </label>
                <textarea
                  id="course-description"
                  className="input min-h-[60px]"
                  value={form.description}
                  onChange={(e) => setForm((p) => ({ ...p, description: e.target.value }))}
                />
              </div>

              <div className="grid gap-3 md:grid-cols-2">
                <div>
                  <label className="label" htmlFor="course-basis">
                    Основание обучения
                  </label>
                  <input
                    id="course-basis"
                    className="input"
                    placeholder="Например: Закон № 190-П"
                    value={form.training_basis}
                    onChange={(e) => setForm((p) => ({ ...p, training_basis: e.target.value }))}
                  />
                </div>
                <div>
                  <label className="label" htmlFor="course-basis-url">
                    Ссылка на основание (необязательно)
                  </label>
                  <input
                    id="course-basis-url"
                    type="url"
                    className="input"
                    placeholder="https://..."
                    value={form.training_basis_url}
                    onChange={(e) => setForm((p) => ({ ...p, training_basis_url: e.target.value }))}
                  />
                </div>
              </div>

              <div>
                <label className="label" htmlFor="course-content">
                  Содержимое курса
                </label>
                <p className="mb-2 text-xs text-gray-500">
                  Текст, фото, видео (YouTube/Vimeo/RuTube) — та же разметка, что и в статьях.
                </p>
                <ContentEditor
                  id="course-content"
                  value={form.content}
                  onChange={(v) => setForm((p) => ({ ...p, content: v }))}
                />
              </div>

              <div className="flex justify-end gap-2">
                <button type="submit" className="btn-secondary" disabled={create.isPending}>
                  {create.isPending ? 'Сохранение...' : 'Сохранить черновик'}
                </button>
                <button
                  type="button"
                  className="btn-primary"
                  disabled={create.isPending}
                  onClick={() => submit(true)}
                >
                  Опубликовать
                </button>
              </div>
            </form>
          </div>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}
