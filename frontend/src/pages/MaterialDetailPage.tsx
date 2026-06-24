import { Link, useParams } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { ArrowLeft } from 'lucide-react';

import * as materialsApi from '@/api/materials';
import { Markdown } from '@/components/Markdown';

export function MaterialDetailPage() {
  const { id } = useParams<{ id: string }>();

  const { data, isLoading, isError } = useQuery({
    queryKey: ['material', id],
    queryFn: () => materialsApi.getMaterial(id as string),
    enabled: !!id,
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

  return (
    <div className="space-y-4">
      <Link
        to="/materials"
        className="inline-flex items-center gap-1 text-sm text-gray-600 hover:text-gray-900"
      >
        <ArrowLeft size={16} /> К материалам
      </Link>

      <article className="card">
        <div className="flex items-center gap-3 text-xs text-gray-500">
          <span className="rounded-full bg-gray-100 px-2 py-1 uppercase tracking-wide">
            {data.status === 'published' ? 'Опубликован' : 'Черновик'}
          </span>
          {data.published_at && <span>{new Date(data.published_at).toLocaleDateString('ru-RU')}</span>}
          <span>{data.views_count} просмотров</span>
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
