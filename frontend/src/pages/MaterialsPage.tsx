/**
 * Страница базы знаний.
 */

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Search, Filter, FileText, Book, Newspaper, File } from 'lucide-react';

import * as materialsApi from '@/api/materials';
import type { MaterialType, MaterialListItem } from '@/types';

const materialTypes: { value: MaterialType | ''; label: string; icon: typeof FileText }[] = [
  { value: '', label: 'Все материалы', icon: File },
  { value: 'article', label: 'Статьи', icon: FileText },
  { value: 'npa', label: 'НПА', icon: Book },
  { value: 'template', label: 'Шаблоны', icon: File },
  { value: 'news', label: 'Новости', icon: Newspaper },
];

function MaterialTypeIcon({ type }: { type: MaterialType }) {
  switch (type) {
    case 'article':
      return <FileText className="h-5 w-5 text-blue-500" />;
    case 'npa':
      return <Book className="h-5 w-5 text-green-500" />;
    case 'template':
      return <File className="h-5 w-5 text-purple-500" />;
    case 'news':
      return <Newspaper className="h-5 w-5 text-orange-500" />;
    default:
      return <FileText className="h-5 w-5 text-gray-500" />;
  }
}

function MaterialCard({ material }: { material: MaterialListItem }) {
  return (
    <a
      href={`/materials/${material.id}`}
      className="card block transition-shadow hover:shadow-md"
    >
      <div className="flex items-start gap-3">
        <MaterialTypeIcon type={material.type} />
        <div className="flex-1">
          <h3 className="font-medium text-gray-900 line-clamp-2">{material.title}</h3>
          {material.summary && (
            <p className="mt-1 text-sm text-gray-500 line-clamp-2">{material.summary}</p>
          )}
          <div className="mt-2 flex items-center gap-4 text-xs text-gray-400">
            <span>{material.viewsCount} просмотров</span>
            {material.publishedAt && (
              <span>
                {new Date(material.publishedAt).toLocaleDateString('ru-RU')}
              </span>
            )}
          </div>
        </div>
      </div>
    </a>
  );
}

export function MaterialsPage() {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedType, setSelectedType] = useState<MaterialType | ''>('');
  const [page, setPage] = useState(1);

  // Запрос материалов или поиск
  const { data, isLoading } = useQuery({
    queryKey: ['materials', searchQuery, selectedType, page],
    queryFn: () =>
      searchQuery
        ? materialsApi.searchMaterials({
            query: searchQuery,
            type: selectedType || undefined,
            page,
            pageSize: 20,
          })
        : materialsApi.getMaterials({
            type: selectedType || undefined,
            page,
            pageSize: 20,
          }),
  });

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    setPage(1);
  };

  return (
    <div className="space-y-6">
      {/* Заголовок */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">База знаний</h1>
        <p className="mt-1 text-gray-600">
          Поиск по материалам, нормативным документам и шаблонам
        </p>
      </div>

      {/* Поиск и фильтры */}
      <div className="card">
        <form onSubmit={handleSearch} className="flex gap-3">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 h-5 w-5 -translate-y-1/2 text-gray-400" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Введите поисковый запрос..."
              className="input pl-10"
            />
          </div>
          <button type="submit" className="btn-primary">
            Найти
          </button>
        </form>

        <div className="mt-4 flex flex-wrap gap-2">
          {materialTypes.map((type) => (
            <button
              key={type.value}
              onClick={() => {
                setSelectedType(type.value);
                setPage(1);
              }}
              className={`flex items-center gap-2 rounded-full px-4 py-2 text-sm font-medium transition-colors ${
                selectedType === type.value
                  ? 'bg-primary-100 text-primary-700'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              <type.icon className="h-4 w-4" />
              {type.label}
            </button>
          ))}
        </div>
      </div>

      {/* Результаты */}
      {isLoading ? (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {[...Array(6)].map((_, i) => (
            <div key={i} className="card animate-pulse">
              <div className="h-4 w-3/4 rounded bg-gray-200" />
              <div className="mt-2 h-3 w-full rounded bg-gray-200" />
              <div className="mt-2 h-3 w-2/3 rounded bg-gray-200" />
            </div>
          ))}
        </div>
      ) : data?.items.length === 0 ? (
        <div className="card text-center">
          <p className="text-gray-500">Материалы не найдены</p>
        </div>
      ) : (
        <>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {data?.items.map((material) => (
              <MaterialCard key={material.id} material={material} />
            ))}
          </div>

          {/* Пагинация */}
          {data && data.pages > 1 && (
            <div className="flex justify-center gap-2">
              <button
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={page === 1}
                className="btn-secondary"
              >
                Назад
              </button>
              <span className="flex items-center px-4 text-sm text-gray-600">
                Страница {page} из {data.pages}
              </span>
              <button
                onClick={() => setPage((p) => Math.min(data.pages, p + 1))}
                disabled={page === data.pages}
                className="btn-secondary"
              >
                Вперёд
              </button>
            </div>
          )}
        </>
      )}
    </div>
  );
}
