import { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { Eye, Pencil } from 'lucide-react';

import * as materialsApi from '@/api/materials';
import { getErrorMessage } from '@/api/client';
import { Markdown } from '@/components/Markdown';
import type { Category, MaterialStatus } from '@/types';

/**
 * Форма создания статьи (Markdown). Самодостаточный per-type компонент:
 * позже без переделки переносится во вкладку Radix Tabs.
 */
export function ArticleForm({ categories }: { categories: Category[] }) {
  const [title, setTitle] = useState('');
  const [summary, setSummary] = useState('');
  const [content, setContent] = useState('');
  const [categoryId, setCategoryId] = useState<number | undefined>(undefined);
  const [showPreview, setShowPreview] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const queryClient = useQueryClient();
  const navigate = useNavigate();

  const create = useMutation({
    mutationFn: materialsApi.createArticle,
    onSuccess: (material) => {
      queryClient.invalidateQueries({ queryKey: ['materials'] });
      navigate(`/materials/${material.id}`);
    },
    onError: (e) => setError(getErrorMessage(e)),
  });

  const submit = (status: MaterialStatus) => {
    setError(null);
    create.mutate({
      title,
      summary: summary || null,
      content,
      category_id: categoryId,
      status,
    });
  };

  return (
    <form
      className="space-y-3"
      onSubmit={(e) => {
        e.preventDefault();
        submit('draft');
      }}
    >
      {error && <div className="rounded-md bg-red-50 p-3 text-sm text-red-600">{error}</div>}

      <div className="grid gap-3 md:grid-cols-2">
        <div>
          <label className="label" htmlFor="article-title">
            Заголовок
          </label>
          <input
            id="article-title"
            className="input"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            required
          />
        </div>
        <div>
          <label className="label" htmlFor="article-category">
            Категория
          </label>
          <select
            id="article-category"
            className="input"
            value={categoryId ?? ''}
            onChange={(e) => setCategoryId(e.target.value ? Number(e.target.value) : undefined)}
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
        <label className="label" htmlFor="article-summary">
          Краткое описание
        </label>
        <input
          id="article-summary"
          className="input"
          value={summary}
          onChange={(e) => setSummary(e.target.value)}
        />
      </div>

      <div>
        <div className="mb-1 flex items-center justify-between">
          <label className="text-sm font-medium text-gray-700" htmlFor="article-content">
            Текст (Markdown)
          </label>
          <button
            type="button"
            onClick={() => setShowPreview((v) => !v)}
            className="flex items-center gap-1 text-xs text-primary-600 hover:text-primary-700"
          >
            {showPreview ? (
              <>
                <Pencil size={14} /> Редактор
              </>
            ) : (
              <>
                <Eye size={14} /> Превью
              </>
            )}
          </button>
        </div>
        {showPreview ? (
          <div className="min-h-[160px] rounded-md border border-gray-200 p-3">
            {content ? <Markdown>{content}</Markdown> : <p className="text-sm text-gray-400">Нечего показать</p>}
          </div>
        ) : (
          <textarea
            id="article-content"
            className="input min-h-[160px] font-mono"
            value={content}
            onChange={(e) => setContent(e.target.value)}
            placeholder={'## Заголовок\n\nТекст с **разметкой** и [ссылкой](https://...)'}
            required
          />
        )}
      </div>

      <div className="flex justify-end gap-2">
        <button type="submit" className="btn-secondary" disabled={create.isPending}>
          {create.isPending ? 'Сохранение...' : 'Сохранить черновик'}
        </button>
        <button
          type="button"
          className="btn-primary"
          disabled={create.isPending}
          onClick={() => submit('published')}
        >
          Опубликовать
        </button>
      </div>
    </form>
  );
}
