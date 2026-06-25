import { useState } from 'react';
import { Link } from 'react-router-dom';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { Search, FileText, Book, Newspaper, File, Eye, Calendar, Building2 } from 'lucide-react';

import * as materialsApi from '@/api/materials';
import { useAuth } from '@/hooks/useAuth';
import { CreateMaterialDialog } from '@/components/materials/CreateMaterialDialog';
import type { MaterialListItem, MaterialStatus, MaterialType } from '@/types';

const materialTypes: { value: MaterialType | ''; label: string; icon: typeof FileText }[] = [
  { value: '', label: 'Все материалы', icon: File },
  { value: 'article', label: 'Статьи', icon: FileText },
  { value: 'npa', label: 'НПА', icon: Book },
  { value: 'template', label: 'Шаблоны', icon: File },
  { value: 'news', label: 'Новости', icon: Newspaper },
];

const statusFilters: { value: MaterialStatus; label: string }[] = [
  { value: 'published', label: 'Опубликованные' },
  { value: 'draft', label: 'Черновики' },
  { value: 'archived', label: 'Архив' },
];

const statusLabel: Record<string, string> = {
  published: 'Опубликован',
  draft: 'Черновик',
  archived: 'В архиве',
};

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
  onRestore,
  isOwner,
  isBusy,
}: {
  material: MaterialListItem;
  onPublish?: (id: string) => void;
  onRestore?: (id: string) => void;
  isOwner: boolean;
  isBusy: boolean;
}) {
  return (
    <div className="card flex flex-col gap-3 transition-shadow hover:shadow-md">
      <div className="flex items-start gap-3">
        <MaterialTypeIcon type={material.type} />
        <div className="min-w-0 flex-1">
          <Link
            to={`/materials/${material.id}`}
            className="block font-medium text-gray-900 line-clamp-2 hover:text-primary-600"
          >
            {material.title}
          </Link>
          {material.summary && (
            <p className="mt-1 text-sm text-gray-500 line-clamp-2">{material.summary}</p>
          )}

          {/* Мета выровнена по тексту заголовка (правее иконки); flex-wrap не даёт вылезти. */}
          <div className="mt-2 flex flex-wrap items-center gap-x-3 gap-y-1.5 text-xs text-gray-500">
            <span className="rounded-full bg-gray-100 px-2 py-1 uppercase tracking-wide">
              {statusLabel[material.status] ?? material.status}
            </span>
            <span className="inline-flex items-center gap-1">
              <Eye className="h-3.5 w-3.5" />
              {material.views_count}
            </span>
            {material.published_at && (
              <span className="inline-flex items-center gap-1">
                <Calendar className="h-3.5 w-3.5" />
                {new Date(material.published_at).toLocaleDateString('ru-RU')}
              </span>
            )}
          </div>
        </div>
      </div>

      {/* Сноска: какая организация создала материал. mt-auto прижимает её к низу карточки. */}
      {material.organization_name && (
        <div className="mt-auto flex items-center gap-1.5 border-t border-gray-100 pt-2 text-xs text-gray-400">
          <Building2 className="h-3.5 w-3.5 shrink-0" />
          <span className="truncate" title={material.organization_name}>
            {material.organization_name}
          </span>
        </div>
      )}

      {isOwner && material.status === 'draft' && onPublish && (
        <button onClick={() => onPublish(material.id)} className="btn-secondary self-start" disabled={isBusy}>
          Опубликовать
        </button>
      )}
      {isOwner && material.status === 'archived' && onRestore && (
        <button onClick={() => onRestore(material.id)} className="btn-secondary self-start" disabled={isBusy}>
          Восстановить
        </button>
      )}
    </div>
  );
}

export function MaterialsPage() {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedType, setSelectedType] = useState<MaterialType | ''>('');
  const [selectedStatus, setSelectedStatus] = useState<MaterialStatus>('published');
  const [page, setPage] = useState(1);
  const pageSize = 12;

  const queryClient = useQueryClient();
  const { role } = useAuth();
  const isOwner = role === 'org_owner';

  const materialsQuery = useQuery({
    queryKey: ['materials', selectedStatus, searchQuery, selectedType, page],
    queryFn: () =>
      searchQuery
        ? materialsApi.searchMaterials({
            query: searchQuery,
            type: selectedType || undefined,
            status: selectedStatus,
            page,
            page_size: pageSize,
          })
        : materialsApi.getMaterials({
            status: selectedStatus,
            type: selectedType || undefined,
            page,
            page_size: pageSize,
          }),
  });

  const publishMaterial = useMutation({
    mutationFn: materialsApi.publishMaterial,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['materials'] }),
  });

  const restoreMaterial = useMutation({
    mutationFn: materialsApi.restoreMaterial,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['materials'] }),
  });

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    setPage(1);
  };

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Документы и журналы</h1>
          <p className="mt-1 text-gray-600">
            Поиск по материалам, нормативным документам и шаблонам
          </p>
        </div>
        {isOwner && <CreateMaterialDialog />}
      </div>

      {/* Вкладки разделов по типу материала */}
      <div className="border-b border-gray-200">
        <nav className="-mb-px flex gap-1 overflow-x-auto">
          {materialTypes.map((type) => (
            <button
              key={type.value}
              onClick={() => {
                setSelectedType(type.value);
                setPage(1);
              }}
              className={`flex items-center gap-2 whitespace-nowrap border-b-2 px-4 py-2.5 text-sm font-medium transition-colors ${
                selectedType === type.value
                  ? 'border-primary-600 text-primary-700'
                  : 'border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700'
              }`}
            >
              <type.icon className="h-4 w-4" />
              {type.label}
            </button>
          ))}
        </nav>
      </div>

      <div className="card">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
          <form onSubmit={handleSearch} className="flex gap-3 sm:flex-1">
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

          {isOwner && (
            <div className="inline-flex shrink-0 self-start overflow-x-auto rounded-lg border border-gray-200 bg-gray-50 p-0.5 sm:ml-auto sm:self-auto">
              {statusFilters.map((s) => (
                <button
                  key={s.value}
                  onClick={() => {
                    setSelectedStatus(s.value);
                    setPage(1);
                  }}
                  className={`whitespace-nowrap rounded-md px-3 py-1.5 text-sm font-medium transition-colors ${
                    selectedStatus === s.value
                      ? 'bg-white text-primary-700 shadow-sm'
                      : 'text-gray-600 hover:text-gray-900'
                  }`}
                >
                  {s.label}
                </button>
              ))}
            </div>
          )}
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
                onRestore={restoreMaterial.mutateAsync}
                isOwner={isOwner}
                isBusy={publishMaterial.isPending || restoreMaterial.isPending}
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
