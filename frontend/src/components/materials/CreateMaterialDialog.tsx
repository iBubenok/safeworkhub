import { useState } from 'react';
import * as Dialog from '@radix-ui/react-dialog';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { Plus, X } from 'lucide-react';

import * as materialsApi from '@/api/materials';
import { getErrorMessage } from '@/api/client';
import { ArticleForm } from '@/components/materials/ArticleForm';
import { NewsForm } from '@/components/materials/NewsForm';
import { TemplateForm } from '@/components/materials/TemplateForm';
import type { MaterialType } from '@/types';

const createTypes: { value: MaterialType; label: string }[] = [
  { value: 'article', label: 'Статьи' },
  { value: 'npa', label: 'НПА' },
  { value: 'template', label: 'Шаблоны' },
  { value: 'news', label: 'Новости' },
];

/** Кнопка «+ Создать материал» + модальное окно с формой создания. */
export function CreateMaterialDialog() {
  const [open, setOpen] = useState(false);
  const [createType, setCreateType] = useState<MaterialType>('article');
  const [formError, setFormError] = useState<string | null>(null);
  const [newMaterial, setNewMaterial] = useState({
    title: '',
    summary: '',
    content: '',
    category_id: undefined as number | undefined,
  });

  const queryClient = useQueryClient();

  const categoriesQuery = useQuery({
    queryKey: ['categories'],
    queryFn: materialsApi.getCategories,
    enabled: open,
    staleTime: 5 * 60 * 1000,
  });

  const createMaterial = useMutation({
    mutationFn: materialsApi.createMaterial,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['materials'] });
      setNewMaterial({ title: '', summary: '', content: '', category_id: undefined });
      setOpen(false);
    },
    onError: (error) => setFormError(getErrorMessage(error)),
  });

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    setFormError(null);
    await createMaterial.mutateAsync({
      ...newMaterial,
      type: createType,
      summary: newMaterial.summary || null,
      status: 'draft',
    });
  };

  const categories = categoriesQuery.data ?? [];

  return (
    <Dialog.Root open={open} onOpenChange={setOpen}>
      <Dialog.Trigger asChild>
        <button type="button" className="btn-primary flex items-center gap-2">
          <Plus size={18} /> Создать материал
        </button>
      </Dialog.Trigger>

      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 z-[60] bg-black/40" />
        <Dialog.Content className="fixed left-1/2 top-1/2 z-[70] flex max-h-[85vh] w-[calc(100vw-2rem)] max-w-2xl -translate-x-1/2 -translate-y-1/2 flex-col overflow-hidden rounded-2xl bg-white shadow-2xl focus:outline-none">
          <div className="flex items-center justify-between border-b px-5 py-4">
            <Dialog.Title className="text-lg font-semibold text-gray-900">
              Создать материал
            </Dialog.Title>
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
            <div className="mb-4 max-w-xs">
            <label className="label" htmlFor="create-type">
              Тип материала
            </label>
            <select
              id="create-type"
              className="input"
              value={createType}
              onChange={(e) => {
                setCreateType(e.target.value as MaterialType);
                setFormError(null);
              }}
            >
              {createTypes.map((item) => (
                <option key={item.value} value={item.value}>
                  {item.label}
                </option>
              ))}
            </select>
          </div>

          {createType === 'article' ? (
            <ArticleForm categories={categories} />
          ) : createType === 'news' ? (
            <NewsForm categories={categories} />
          ) : createType === 'template' ? (
            <TemplateForm categories={categories} />
          ) : (
            <>
              {formError && (
                <div className="mb-3 rounded-md bg-red-50 p-3 text-sm text-red-600">{formError}</div>
              )}
              <form className="space-y-3" onSubmit={handleCreate}>
                <div className="grid gap-3 md:grid-cols-2">
                  <div>
                    <label className="label" htmlFor="title">
                      Заголовок
                    </label>
                    <input
                      id="title"
                      className="input"
                      value={newMaterial.title}
                      onChange={(e) => setNewMaterial((prev) => ({ ...prev, title: e.target.value }))}
                      required
                    />
                  </div>
                  <div>
                    <label className="label" htmlFor="category">
                      Категория
                    </label>
                    <select
                      id="category"
                      className="input"
                      value={newMaterial.category_id ?? ''}
                      onChange={(e) =>
                        setNewMaterial((prev) => ({
                          ...prev,
                          category_id: e.target.value ? Number(e.target.value) : undefined,
                        }))
                      }
                    >
                      <option value="">Без категории</option>
                      {categories.map((category) => (
                        <option key={category.id} value={category.id}>
                          {category.name}
                        </option>
                      ))}
                    </select>
                  </div>
                </div>

                <div>
                  <label className="label" htmlFor="summary">
                    Краткое описание
                  </label>
                  <input
                    id="summary"
                    className="input"
                    value={newMaterial.summary}
                    onChange={(e) => setNewMaterial((prev) => ({ ...prev, summary: e.target.value }))}
                  />
                </div>

                <div>
                  <label className="label" htmlFor="content">
                    Содержимое
                  </label>
                  <textarea
                    id="content"
                    className="input min-h-[120px]"
                    value={newMaterial.content}
                    onChange={(e) => setNewMaterial((prev) => ({ ...prev, content: e.target.value }))}
                    required
                  />
                </div>

                <div className="flex justify-end">
                  <button type="submit" className="btn-primary" disabled={createMaterial.isPending}>
                    {createMaterial.isPending ? 'Сохранение...' : 'Сохранить черновик'}
                  </button>
                </div>
              </form>
            </>
          )}
          </div>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}
