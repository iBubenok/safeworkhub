import { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { Search, FileText, Book, Newspaper, File } from 'lucide-react';

import * as materialsApi from '@/api/materials';
import { getErrorMessage } from '@/api/client';
import { useAuth } from '@/hooks/useAuth';
import type { MaterialListItem, MaterialType } from '@/types';

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

function MaterialCard({
  material,
  onPublish,
  isOwner,
  isPublishing,
}: {
  material: MaterialListItem;
  onPublish?: (id: string) => void;
  isOwner: boolean;
  isPublishing: boolean;
}) {
  return (
    <div className="card block transition-shadow hover:shadow-md">
      <div className="flex items-start gap-3">
        <MaterialTypeIcon type={material.type} />
        <div className="flex-1">
          <h3 className="font-medium text-gray-900 line-clamp-2">{material.title}</h3>
          {material.summary && (
            <p className="mt-1 text-sm text-gray-500 line-clamp-2">{material.summary}</p>
          )}
          <div className="mt-2 flex items-center gap-3 text-xs text-gray-500">
            <span className="rounded-full bg-gray-100 px-2 py-1 text-xs uppercase tracking-wide">
              {material.status === 'published' ? 'Опубликован' : 'Черновик'}
            </span>
            <span>{material.views_count} просмотров</span>
            {material.published_at && (
              <span>
                {new Date(material.published_at).toLocaleDateString('ru-RU')}
              </span>
            )}
          </div>
          {isOwner && material.status !== 'published' && onPublish && (
            <button
              onClick={() => onPublish(material.id)}
              className="btn-secondary mt-3"
              disabled={isPublishing}
            >
              Опубликовать
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

export function MaterialsPage() {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedType, setSelectedType] = useState<MaterialType | ''>('');
  const [page, setPage] = useState(1);
  const [formError, setFormError] = useState<string | null>(null);
  const [newMaterial, setNewMaterial] = useState({
    title: '',
    summary: '',
    content: '',
    type: 'article' as MaterialType,
    category_id: undefined as number | undefined,
  });
  const pageSize = 12;

  const queryClient = useQueryClient();
  const { role } = useAuth();
  const isOwner = role === 'org_owner';

  const materialsQuery = useQuery({
    queryKey: ['materials', searchQuery, selectedType, page],
    queryFn: () =>
      searchQuery
        ? materialsApi.searchMaterials({
            query: searchQuery,
            type: selectedType || undefined,
            page,
            page_size: pageSize,
          })
        : materialsApi.getMaterials({
            type: selectedType || undefined,
            page,
            page_size: pageSize,
          }),
  });

  const categoriesQuery = useQuery({
    queryKey: ['categories'],
    queryFn: materialsApi.getCategories,
    enabled: isOwner,
    staleTime: 5 * 60 * 1000,
  });

  const createMaterial = useMutation({
    mutationFn: materialsApi.createMaterial,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['materials'] });
      setNewMaterial({
        title: '',
        summary: '',
        content: '',
        type: 'article',
        category_id: undefined,
      });
    },
    onError: (error) => setFormError(getErrorMessage(error)),
  });

  const publishMaterial = useMutation({
    mutationFn: materialsApi.publishMaterial,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['materials'] }),
  });

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    setPage(1);
  };

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    setFormError(null);
    await createMaterial.mutateAsync({
      ...newMaterial,
      summary: newMaterial.summary || null,
      status: 'draft',
    });
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">База знаний</h1>
        <p className="mt-1 text-gray-600">
          Поиск по материалам, нормативным документам и шаблонам
        </p>
      </div>

      {isOwner && (
        <div className="card">
          <h3 className="card-title mb-3 text-lg">Создать материал</h3>
          {formError && (
            <div className="mb-3 rounded-md bg-red-50 p-3 text-sm text-red-600">
              {formError}
            </div>
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
                <label className="label" htmlFor="type">
                  Тип
                </label>
                <select
                  id="type"
                  className="input"
                  value={newMaterial.type}
                  onChange={(e) =>
                    setNewMaterial((prev) => ({ ...prev, type: e.target.value as MaterialType }))
                  }
                >
                  {materialTypes
                    .filter((item) => item.value)
                    .map((item) => (
                      <option key={item.value} value={item.value}>
                        {item.label}
                      </option>
                    ))}
                </select>
              </div>
            </div>

            <div className="grid gap-3 md:grid-cols-2">
              <div>
                <label className="label" htmlFor="summary">
                  Краткое описание
                </label>
                <input
                  id="summary"
                  className="input"
                  value={newMaterial.summary}
                  onChange={(e) =>
                    setNewMaterial((prev) => ({ ...prev, summary: e.target.value }))
                  }
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
                  {categoriesQuery.data?.map((category) => (
                    <option key={category.id} value={category.id}>
                      {category.name}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            <div>
              <label className="label" htmlFor="content">
                Содержимое
              </label>
              <textarea
                id="content"
                className="input min-h-[120px]"
                value={newMaterial.content}
                onChange={(e) =>
                  setNewMaterial((prev) => ({ ...prev, content: e.target.value }))
                }
                required
              />
            </div>

            <div className="flex justify-end">
              <button type="submit" className="btn-primary" disabled={createMaterial.isPending}>
                {createMaterial.isPending ? 'Сохранение...' : 'Сохранить черновик'}
              </button>
            </div>
          </form>
        </div>
      )}

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

      {materialsQuery.isLoading ? (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {[...Array(6)].map((_, i) => (
            <div key={i} className="card animate-pulse">
              <div className="h-4 w-3/4 rounded bg-gray-200" />
              <div className="mt-2 h-3 w-full rounded bg-gray-200" />
              <div className="mt-2 h-3 w-2/3 rounded bg-gray-200" />
            </div>
          ))}
        </div>
      ) : materialsQuery.data?.items.length === 0 ? (
        <div className="card text-center">
          <p className="text-gray-500">Материалы не найдены</p>
        </div>
      ) : (
        <>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {materialsQuery.data?.items.map((material) => (
              <MaterialCard
                key={material.id}
                material={material}
                onPublish={publishMaterial.mutateAsync}
                isOwner={isOwner}
                isPublishing={publishMaterial.isPending}
              />
            ))}
          </div>

          {materialsQuery.data && materialsQuery.data.pages > 1 && (
            <div className="flex justify-center gap-2">
              <button
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={page === 1}
                className="btn-secondary"
              >
                Назад
              </button>
              <span className="flex items-center px-4 text-sm text-gray-600">
                Страница {page} из {materialsQuery.data.pages}
              </span>
              <button
                onClick={() =>
                  setPage((p) => Math.min(materialsQuery.data?.pages ?? page, p + 1))
                }
                disabled={page === materialsQuery.data.pages}
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
