import { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';

import * as materialsApi from '@/api/materials';
import { getErrorMessage } from '@/api/client';
import { ContentEditor } from '@/components/ContentEditor';
import type { Category, MaterialStatus } from '@/types';

/** Форма создания новости: базовые поля + новостные (источник, дата, обложка, теги). */
export function NewsForm({ categories }: { categories: Category[] }) {
  const [title, setTitle] = useState('');
  const [summary, setSummary] = useState('');
  const [content, setContent] = useState('');
  const [categoryId, setCategoryId] = useState<number | undefined>(undefined);
  const [sourceUrl, setSourceUrl] = useState('');
  const [eventDate, setEventDate] = useState('');
  const [coverUrl, setCoverUrl] = useState('');
  const [tagsInput, setTagsInput] = useState('');
  const [error, setError] = useState<string | null>(null);

  const queryClient = useQueryClient();
  const navigate = useNavigate();

  const create = useMutation({
    mutationFn: materialsApi.createNews,
    onSuccess: (material) => {
      queryClient.invalidateQueries({ queryKey: ['materials'] });
      navigate(`/materials/${material.id}`);
    },
    onError: (e) => setError(getErrorMessage(e)),
  });

  const submit = (status: MaterialStatus) => {
    setError(null);
    if (!title.trim() || !content.trim()) {
      setError('Заполните заголовок и текст новости');
      return;
    }
    const tags = tagsInput
      .split(',')
      .map((t) => t.trim())
      .filter(Boolean);
    create.mutate({
      title,
      summary: summary || null,
      content,
      category_id: categoryId,
      status,
      source_url: sourceUrl.trim() || null,
      event_date: eventDate || null,
      cover_image_url: coverUrl.trim() || null,
      tags,
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
          <label className="label" htmlFor="news-title">
            Заголовок
          </label>
          <input id="news-title" className="input" value={title} onChange={(e) => setTitle(e.target.value)} required />
        </div>
        <div>
          <label className="label" htmlFor="news-category">
            Категория
          </label>
          <select
            id="news-category"
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
        <label className="label" htmlFor="news-summary">
          Краткое описание
        </label>
        <input id="news-summary" className="input" value={summary} onChange={(e) => setSummary(e.target.value)} />
      </div>

      <div className="grid gap-3 md:grid-cols-2">
        <div>
          <label className="label" htmlFor="news-source">
            Источник (ссылка)
          </label>
          <input
            id="news-source"
            className="input"
            placeholder="https://..."
            value={sourceUrl}
            onChange={(e) => setSourceUrl(e.target.value)}
          />
        </div>
        <div>
          <label className="label" htmlFor="news-date">
            Дата новости
          </label>
          <input
            id="news-date"
            type="date"
            className="input"
            value={eventDate}
            onChange={(e) => setEventDate(e.target.value)}
          />
        </div>
      </div>

      <div className="grid gap-3 md:grid-cols-2">
        <div>
          <label className="label" htmlFor="news-cover">
            Обложка (ссылка на картинку)
          </label>
          <input
            id="news-cover"
            className="input"
            placeholder="https://..."
            value={coverUrl}
            onChange={(e) => setCoverUrl(e.target.value)}
          />
        </div>
        <div>
          <label className="label" htmlFor="news-tags">
            Теги (через запятую)
          </label>
          <input
            id="news-tags"
            className="input"
            placeholder="охрана труда, приказ"
            value={tagsInput}
            onChange={(e) => setTagsInput(e.target.value)}
          />
        </div>
      </div>

      <div>
        <label className="label" htmlFor="news-content">
          Текст
        </label>
        <ContentEditor id="news-content" value={content} onChange={setContent} />
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
