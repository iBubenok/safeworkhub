/**
 * Главная страница (dashboard) — сводка по организации на реальных данных.
 */

import { Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import {
  Activity,
  BookOpen,
  ClipboardCheck,
  ClipboardList,
  FileText,
  GraduationCap,
  ListChecks,
  Scale,
} from 'lucide-react';

import * as materialsApi from '@/api/materials';
import * as checklistsApi from '@/api/checklists';
import * as runsApi from '@/api/checklistRuns';
import { useAuth } from '@/hooks/useAuth';
import { checklistRunResultLabels, checklistRunStatusLabels } from '@/utils/checklistLabels';

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString('ru-RU', { dateStyle: 'medium' });
}

/** Плитка счётчика: показывает total из пагинированного ответа, «—» пока грузится / при ошибке. */
function StatCard({
  name,
  value,
  isLoading,
  icon: Icon,
  color,
}: {
  name: string;
  value: number | undefined;
  isLoading: boolean;
  icon: typeof BookOpen;
  color: string;
}) {
  return (
    <div className="card">
      <div className="flex items-center gap-4">
        <div className={`rounded-lg ${color} p-3`}>
          <Icon className="h-6 w-6 text-white" />
        </div>
        <div>
          <p className="text-sm text-gray-600">{name}</p>
          <p className="text-2xl font-bold text-gray-900">
            {isLoading ? <span className="text-gray-300">—</span> : (value ?? '—')}
          </p>
        </div>
      </div>
    </div>
  );
}

export function DashboardPage() {
  const { user } = useAuth();

  // Счётчики: берём только total, поэтому запрашиваем минимальную страницу.
  const materialsCount = useQuery({
    queryKey: ['dashboard', 'materials-count'],
    queryFn: () => materialsApi.getMaterials({ status: 'published', page_size: 1 }),
  });
  const checklistsCount = useQuery({
    queryKey: ['dashboard', 'checklists-count'],
    queryFn: () => checklistsApi.getChecklists({ page_size: 1 }),
  });
  const completedRunsCount = useQuery({
    queryKey: ['dashboard', 'runs-count', 'completed'],
    queryFn: () => runsApi.getRuns({ status: 'completed', page_size: 1 }),
  });
  const activeRunsCount = useQuery({
    queryKey: ['dashboard', 'runs-count', 'in_progress'],
    queryFn: () => runsApi.getRuns({ status: 'in_progress', page_size: 1 }),
  });

  // Списки для нижнего блока.
  const recentNpa = useQuery({
    queryKey: ['dashboard', 'recent-npa'],
    queryFn: () => materialsApi.getMaterials({ type: 'npa', status: 'published', page_size: 5 }),
  });
  const recentRuns = useQuery({
    queryKey: ['dashboard', 'recent-runs'],
    queryFn: () => runsApi.getRuns({ page_size: 5 }),
  });

  const stats = [
    {
      name: 'Материалы в базе',
      value: materialsCount.data?.total,
      isLoading: materialsCount.isLoading,
      icon: BookOpen,
      color: 'bg-blue-500',
    },
    {
      name: 'Чек-листы',
      value: checklistsCount.data?.total,
      isLoading: checklistsCount.isLoading,
      icon: ListChecks,
      color: 'bg-purple-500',
    },
    {
      name: 'Проверок проведено',
      value: completedRunsCount.data?.total,
      isLoading: completedRunsCount.isLoading,
      icon: ClipboardCheck,
      color: 'bg-green-500',
    },
    {
      name: 'Активные проверки',
      value: activeRunsCount.data?.total,
      isLoading: activeRunsCount.isLoading,
      icon: Activity,
      color: 'bg-orange-500',
    },
  ];

  const npaItems = recentNpa.data?.items ?? [];
  const runItems = recentRuns.data?.items ?? [];

  return (
    <div className="space-y-6">
      {/* Приветствие */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Добро пожаловать, {user?.name}!</h1>
        <p className="mt-1 text-gray-600">
          Здесь вы найдёте всё необходимое для работы специалиста по охране труда.
        </p>
      </div>

      {/* Статистика */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {stats.map((stat) => (
          <StatCard key={stat.name} {...stat} />
        ))}
      </div>

      {/* Быстрые действия */}
      <div className="grid gap-6 lg:grid-cols-2">
        <div className="card">
          <h2 className="text-lg font-semibold text-gray-900">Быстрые действия</h2>
          <div className="mt-4 space-y-3">
            <Link
              to="/materials"
              className="flex items-center gap-3 rounded-lg border p-3 transition-colors hover:bg-gray-50"
            >
              <BookOpen className="h-5 w-5 text-primary-600" />
              <div>
                <p className="font-medium text-gray-900">Поиск по базе знаний</p>
                <p className="text-sm text-gray-500">Найдите ответ на любой вопрос по охране труда</p>
              </div>
            </Link>
            <Link
              to="/courses"
              className="flex items-center gap-3 rounded-lg border p-3 transition-colors hover:bg-gray-50"
            >
              <GraduationCap className="h-5 w-5 text-green-600" />
              <div>
                <p className="font-medium text-gray-900">Начать обучение</p>
                <p className="text-sm text-gray-500">Пройдите курсы повышения квалификации</p>
              </div>
            </Link>
            <Link
              to="/checks"
              className="flex items-center gap-3 rounded-lg border p-3 transition-colors hover:bg-gray-50"
            >
              <ClipboardCheck className="h-5 w-5 text-purple-600" />
              <div>
                <p className="font-medium text-gray-900">Проверки и чек-листы</p>
                <p className="text-sm text-gray-500">Проведите проверку по чек-листу</p>
              </div>
            </Link>
          </div>
        </div>

        {/* Последние проверки */}
        <div className="card">
          <h2 className="text-lg font-semibold text-gray-900">Последние проверки</h2>
          <div className="mt-4 space-y-3">
            {recentRuns.isLoading ? (
              [...Array(2)].map((_, i) => <div key={i} className="h-16 animate-pulse rounded-lg bg-gray-100" />)
            ) : runItems.length === 0 ? (
              <div className="flex flex-col items-center gap-2 py-6 text-center">
                <ClipboardList className="h-8 w-8 text-gray-300" />
                <p className="text-sm text-gray-500">Проверки ещё не проводились</p>
              </div>
            ) : (
              runItems.map((run) => (
                <Link
                  key={run.id}
                  to={`/checks/runs/${run.id}`}
                  className="block rounded-lg bg-gray-50 p-3 transition-colors hover:bg-gray-100"
                >
                  <p className="text-sm font-medium text-gray-900 line-clamp-1">
                    {run.title || run.checklist_title}
                  </p>
                  <div className="mt-1.5 flex flex-wrap items-center gap-x-2 gap-y-1 text-xs">
                    <span className="rounded-full bg-gray-200 px-2 py-0.5 uppercase tracking-wide text-gray-600">
                      {checklistRunStatusLabels[run.status]}
                    </span>
                    {run.result && (
                      <span
                        className={`rounded-full px-2 py-0.5 font-medium ${
                          run.result === 'passed' ? 'bg-green-50 text-green-700' : 'bg-red-50 text-red-700'
                        }`}
                      >
                        {checklistRunResultLabels[run.result]}
                        {run.score !== null && ` · ${run.score}%`}
                      </span>
                    )}
                    <span className="text-gray-400">{formatDate(run.created_at)}</span>
                  </div>
                </Link>
              ))
            )}
          </div>
          <Link to="/checks" className="mt-4 block text-center text-sm text-primary-600 hover:underline">
            Смотреть все проверки
          </Link>
        </div>
      </div>

      {/* Последние обновления НПА */}
      <div className="card">
        <div className="flex items-center gap-2">
          <Scale className="h-5 w-5 text-primary-600" />
          <h2 className="text-lg font-semibold text-gray-900">Последние обновления НПА</h2>
        </div>
        <div className="mt-4 grid gap-3 sm:grid-cols-2">
          {recentNpa.isLoading ? (
            [...Array(2)].map((_, i) => <div key={i} className="h-20 animate-pulse rounded-lg bg-gray-100" />)
          ) : npaItems.length === 0 ? (
            <div className="col-span-full flex flex-col items-center gap-2 py-6 text-center">
              <FileText className="h-8 w-8 text-gray-300" />
              <p className="text-sm text-gray-500">Нормативные документы пока не добавлены</p>
            </div>
          ) : (
            npaItems.map((npa) => (
              <Link
                key={npa.id}
                to={`/materials/${npa.id}`}
                className="block rounded-lg bg-gray-50 p-3 transition-colors hover:bg-gray-100"
              >
                <p className="text-sm font-medium text-gray-900 line-clamp-2">{npa.title}</p>
                {npa.summary && <p className="mt-1 text-sm text-gray-500 line-clamp-2">{npa.summary}</p>}
                {npa.published_at && (
                  <p className="mt-2 text-xs text-gray-400">Опубликовано {formatDate(npa.published_at)}</p>
                )}
              </Link>
            ))
          )}
        </div>
        <Link to="/materials" className="mt-4 block text-center text-sm text-primary-600 hover:underline">
          Смотреть все материалы
        </Link>
      </div>
    </div>
  );
}
