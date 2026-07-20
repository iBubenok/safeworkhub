import { useState } from 'react';
import { Link } from 'react-router-dom';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { Rocket, Clock3, Search } from 'lucide-react';

import * as coursesApi from '@/api/courses';
import { CreateCourseDialog } from '@/components/courses/CreateCourseDialog';
import { usePermissions } from '@/hooks/usePermissions';
import type { Course } from '@/types';

export function CoursesPage() {
  const queryClient = useQueryClient();
  const { isOwner } = usePermissions();

  const [searchQuery, setSearchQuery] = useState('');

  const coursesQuery = useQuery({
    queryKey: ['courses', searchQuery],
    queryFn: () => coursesApi.listCourses({ search: searchQuery }),
  });

  const assignmentsQuery = useQuery({
    queryKey: ['my-assignments'],
    queryFn: coursesApi.myAssignments,
    staleTime: 30_000,
  });

  const publishCourse = useMutation({
    mutationFn: coursesApi.publishCourse,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['courses'] }),
  });

  const updateProgress = useMutation({
    mutationFn: ({ courseId, progress }: { courseId: number; progress: number }) =>
      coursesApi.updateProgress(courseId, progress),
    onSuccess: () => assignmentsQuery.refetch(),
  });

  const courses = coursesQuery.data ?? [];

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Обучение</h1>
          <p className="mt-1 text-gray-600">
            Курсы, назначения и прогресс сотрудников
          </p>
        </div>
        {isOwner && <CreateCourseDialog />}
      </div>

      <div className="card">
        <form onSubmit={(e) => e.preventDefault()} className="flex gap-3">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 h-5 w-5 -translate-y-1/2 text-gray-400" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Поиск по названию и описанию курса..."
              className="input pl-10"
            />
          </div>
        </form>
      </div>

      <div className="card">
        <div className="flex items-center justify-between">
          <h3 className="card-title text-lg">Мои назначения</h3>
          <Rocket className="h-5 w-5 text-primary-600" />
        </div>
        {assignmentsQuery.isLoading ? (
          <p className="mt-2 text-sm text-gray-600">Загрузка назначений...</p>
        ) : (assignmentsQuery.data?.length ?? 0) === 0 ? (
          <p className="mt-2 text-sm text-gray-600">Назначения не найдены</p>
        ) : (
          <div className="mt-3 space-y-2">
            {assignmentsQuery.data?.map((assignment) => (
              <div
                key={assignment.id}
                className="flex items-center justify-between rounded-md bg-gray-50 px-3 py-2"
              >
                <div>
                  <Link
                    to={`/courses/${assignment.course_id}`}
                    className="text-sm font-medium text-gray-900 hover:text-primary-700 hover:underline"
                  >
                    {assignment.course_title ?? `Курс #${assignment.course_id}`}
                  </Link>
                  <p className="text-xs text-gray-500">
                    Статус: {assignment.status}, прогресс: {assignment.progress_percent}%
                  </p>
                </div>
                {assignment.status !== 'completed' && (
                  <button
                    className="btn-secondary"
                    onClick={() =>
                      updateProgress.mutate({ courseId: assignment.course_id, progress: 100 })
                    }
                    disabled={updateProgress.isPending}
                  >
                    Завершить
                  </button>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      {coursesQuery.isLoading ? (
        <div className="grid gap-4 lg:grid-cols-2">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="card h-32 animate-pulse" />
          ))}
        </div>
      ) : courses.length === 0 ? (
        <div className="card text-center">
          <p className="text-gray-500">Курсы не найдены</p>
        </div>
      ) : (
      <div className="grid gap-4 lg:grid-cols-2">
        {courses.map((course: Course) => (
          <Link
            key={course.id}
            to={`/courses/${course.id}`}
            className="card flex flex-col gap-3 transition-shadow hover:shadow-md"
          >
            <div className="flex items-start justify-between gap-3">
              <p className="font-semibold text-gray-900 line-clamp-2">{course.title}</p>
              {isOwner && (
                <span className="shrink-0 rounded-full bg-gray-100 px-2.5 py-1 text-xs uppercase tracking-wide text-gray-700">
                  {course.is_published ? 'Опубликован' : 'Черновик'}
                </span>
              )}
            </div>

            {course.description && (
              <p className="text-sm text-gray-500 line-clamp-2">{course.description}</p>
            )}

            <div className="mt-auto flex items-center gap-2 text-xs text-gray-500">
              <Clock3 className="h-3.5 w-3.5" />
              <span>≈ {course.duration_minutes} мин</span>
            </div>

            {isOwner && !course.is_published && (
              <button
                type="button"
                className="btn-secondary self-start"
                onClick={(e) => {
                  e.preventDefault();
                  e.stopPropagation();
                  publishCourse.mutate(course.id);
                }}
                disabled={publishCourse.isPending}
              >
                {publishCourse.isPending ? 'Публикация...' : 'Опубликовать'}
              </button>
            )}
          </Link>
        ))}
      </div>
      )}
    </div>
  );
}
