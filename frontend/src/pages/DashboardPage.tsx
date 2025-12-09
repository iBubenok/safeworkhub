/**
 * Главная страница (dashboard).
 */

import { BookOpen, GraduationCap, FileText, TrendingUp } from 'lucide-react';

import { useAuth } from '@/hooks/useAuth';

const stats = [
  {
    name: 'Материалы в базе',
    value: '1,234',
    icon: BookOpen,
    change: '+12%',
    color: 'bg-blue-500',
  },
  {
    name: 'Доступные курсы',
    value: '48',
    icon: GraduationCap,
    change: '+4',
    color: 'bg-green-500',
  },
  {
    name: 'Шаблоны документов',
    value: '256',
    icon: FileText,
    change: '+18',
    color: 'bg-purple-500',
  },
  {
    name: 'Обновлений НПА',
    value: '23',
    icon: TrendingUp,
    change: 'за месяц',
    color: 'bg-orange-500',
  },
];

export function DashboardPage() {
  const { user } = useAuth();

  return (
    <div className="space-y-6">
      {/* Приветствие */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">
          Добро пожаловать, {user?.name}!
        </h1>
        <p className="mt-1 text-gray-600">
          Здесь вы найдёте всё необходимое для работы специалиста по охране труда.
        </p>
      </div>

      {/* Статистика */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {stats.map((stat) => (
          <div key={stat.name} className="card">
            <div className="flex items-center gap-4">
              <div className={`rounded-lg ${stat.color} p-3`}>
                <stat.icon className="h-6 w-6 text-white" />
              </div>
              <div>
                <p className="text-sm text-gray-600">{stat.name}</p>
                <p className="text-2xl font-bold text-gray-900">{stat.value}</p>
              </div>
            </div>
            <p className="mt-2 text-sm text-gray-500">{stat.change}</p>
          </div>
        ))}
      </div>

      {/* Быстрые действия */}
      <div className="grid gap-6 lg:grid-cols-2">
        <div className="card">
          <h2 className="text-lg font-semibold text-gray-900">Быстрые действия</h2>
          <div className="mt-4 space-y-3">
            <a
              href="/materials"
              className="flex items-center gap-3 rounded-lg border p-3 transition-colors hover:bg-gray-50"
            >
              <BookOpen className="h-5 w-5 text-primary-600" />
              <div>
                <p className="font-medium text-gray-900">Поиск по базе знаний</p>
                <p className="text-sm text-gray-500">
                  Найдите ответ на любой вопрос по охране труда
                </p>
              </div>
            </a>
            <a
              href="/courses"
              className="flex items-center gap-3 rounded-lg border p-3 transition-colors hover:bg-gray-50"
            >
              <GraduationCap className="h-5 w-5 text-green-600" />
              <div>
                <p className="font-medium text-gray-900">Начать обучение</p>
                <p className="text-sm text-gray-500">
                  Пройдите курсы повышения квалификации
                </p>
              </div>
            </a>
            <a
              href="/templates"
              className="flex items-center gap-3 rounded-lg border p-3 transition-colors hover:bg-gray-50"
            >
              <FileText className="h-5 w-5 text-purple-600" />
              <div>
                <p className="font-medium text-gray-900">Шаблоны документов</p>
                <p className="text-sm text-gray-500">
                  Скачайте готовые шаблоны приказов и инструкций
                </p>
              </div>
            </a>
          </div>
        </div>

        <div className="card">
          <h2 className="text-lg font-semibold text-gray-900">Последние обновления НПА</h2>
          <div className="mt-4 space-y-3">
            <div className="rounded-lg bg-gray-50 p-3">
              <p className="text-sm font-medium text-gray-900">
                Приказ Минтруда России от 15.12.2024 № 123н
              </p>
              <p className="mt-1 text-sm text-gray-500">
                Об утверждении Правил по охране труда при работе на высоте
              </p>
              <p className="mt-2 text-xs text-gray-400">Добавлено 2 дня назад</p>
            </div>
            <div className="rounded-lg bg-gray-50 p-3">
              <p className="text-sm font-medium text-gray-900">
                Федеральный закон от 10.12.2024 № 456-ФЗ
              </p>
              <p className="mt-1 text-sm text-gray-500">
                О внесении изменений в Трудовой кодекс Российской Федерации
              </p>
              <p className="mt-2 text-xs text-gray-400">Добавлено 5 дней назад</p>
            </div>
          </div>
          <a
            href="/materials?type=npa"
            className="mt-4 block text-center text-sm text-primary-600 hover:underline"
          >
            Смотреть все обновления
          </a>
        </div>
      </div>
    </div>
  );
}
