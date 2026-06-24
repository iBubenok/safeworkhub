import { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';

import * as materialsApi from '@/api/materials';
import { getErrorMessage } from '@/api/client';
import { ContentEditor } from '@/components/ContentEditor';
import type { Category, MaterialContentFormat, MaterialStatus } from '@/types';

/**
 * Форма создания статьи (Markdown). Самодостаточный per-type компонент:
 * позже без переделки переносится во вкладку Radix Tabs.
 */
export function ArticleForm({ categories }: { categories: Category[] }) {
  const [title, setTitle] = useState('');
  const [summary, setSummary] = useState('');
  const [content, setContent] = useState('');
  const [format, setFormat] = useState<MaterialContentFormat>('markdown');
  const [categoryId, setCategoryId] = useState<number | undefined>(undefined);
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
    if (!title.trim() || !content.trim()) {
      setError('Заполните заголовок и текст статьи');
      return;
    }
    create.mutate({
      title,
      summary: summary || null,
      content,
      content_format: format,
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
        <label className="label" htmlFor="article-content">
          Текст
        </label>
        <ContentEditor
          id="article-content"
          value={content}
          onChange={setContent}
          format={format}
          onFormatChange={setFormat}
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
          onClick={() => submit('published')}
        >
          Опубликовать
        </button>
      </div>
    </form>
  );
}
