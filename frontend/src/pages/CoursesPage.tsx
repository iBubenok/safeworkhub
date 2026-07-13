import { useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { Rocket, UsersRound, Clock3 } from 'lucide-react';

import * as coursesApi from '@/api/courses';
import * as usersApi from '@/api/users';
import { getErrorMessage } from '@/api/client';
import { ContentEditor } from '@/components/ContentEditor';
import { usePermissions } from '@/hooks/usePermissions';
import type { Course } from '@/types';

export function CoursesPage() {
  const queryClient = useQueryClient();
  const { isOwner } = usePermissions();

  const [newCourse, setNewCourse] = useState({
    title: '',
    description: '',
    content: '',
    duration_minutes: 0,
  });
  const [assignmentTargets, setAssignmentTargets] = useState<Record<number, string>>({});
  const [formError, setFormError] = useState<string | null>(null);

  const coursesQuery = useQuery({
    queryKey: ['courses'],
    queryFn: () => coursesApi.listCourses(),
  });

  const assignmentsQuery = useQuery({
    queryKey: ['my-assignments'],
    queryFn: coursesApi.myAssignments,
    enabled: !isOwner || true,
    staleTime: 30_000,
  });

  const usersQuery = useQuery({
    queryKey: ['users', 'for-assign'],
    queryFn: () => usersApi.searchUsers({ limit: 50 }),
    enabled: isOwner,
    staleTime: 60_000,
  });

  const createCourse = useMutation({
    mutationFn: coursesApi.createCourse,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['courses'] });
      setNewCourse({ title: '', description: '', content: '', duration_minutes: 0 });
    },
    onError: (error) => setFormError(getErrorMessage(error)),
  });

  const publishCourse = useMutation({
    mutationFn: coursesApi.publishCourse,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['courses'] }),
  });

  const assignCourse = useMutation({
    mutationFn: ({ courseId, userId }: { courseId: number; userId: string }) =>
      coursesApi.assignCourse(courseId, [userId]),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['courses'] }),
    onError: (error) => setFormError(getErrorMessage(error)),
  });

  const updateProgress = useMutation({
    mutationFn: ({ courseId, progress }: { courseId: number; progress: number }) =>
      coursesApi.updateProgress(courseId, progress),
    onSuccess: () => assignmentsQuery.refetch(),
  });

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    setFormError(null);
    await createCourse.mutateAsync({
      title: newCourse.title,
      description: newCourse.description || null,
      content: newCourse.content || null,
      duration_minutes: newCourse.duration_minutes,
    });
  };

  const courses = coursesQuery.data ?? [];
  const users = useMemo(() => usersQuery.data ?? [], [usersQuery.data]);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Обучение</h1>
        <p className="mt-1 text-gray-600">
          Курсы, назначения и прогресс сотрудников
        </p>
      </div>

      {isOwner && (
        <div className="card">
          <h3 className="card-title mb-3 text-lg">Создать курс</h3>
          {formError && (
            <div className="mb-3 rounded-md bg-red-50 p-3 text-sm text-red-600">
              {formError}
            </div>
          )}
          <form className="space-y-3" onSubmit={handleCreate}>
            <div className="grid gap-3 md:grid-cols-2">
              <div>
                <label className="label" htmlFor="courseTitle">
                  Название
                </label>
                <input
                  id="courseTitle"
                  className="input"
                  value={newCourse.title}
                  onChange={(e) => setNewCourse((prev) => ({ ...prev, title: e.target.value }))}
                  required
                />
              </div>
              <div>
                <label className="label" htmlFor="courseDuration">
                  Длительность (мин)
                </label>
                <input
                  id="courseDuration"
                  className="input"
                  type="number"
                  min={0}
                  value={newCourse.duration_minutes}
                  onChange={(e) =>
                    setNewCourse((prev) => ({
                      ...prev,
                      duration_minutes: Number(e.target.value),
                    }))
                  }
                />
              </div>
            </div>
            <div>
              <label className="label" htmlFor="courseDescription">
                Краткое описание
              </label>
              <textarea
                id="courseDescription"
                className="input min-h-[60px]"
                value={newCourse.description}
                onChange={(e) =>
                  setNewCourse((prev) => ({ ...prev, description: e.target.value }))
                }
              />
            </div>
            <div>
              <label className="label" htmlFor="courseContent">
                Содержимое курса
              </label>
              <p className="mb-2 text-xs text-gray-500">
                Текст, фото, видео (YouTube/Vimeo/RuTube) — та же разметка, что и в статьях.
              </p>
              <ContentEditor
                id="courseContent"
                value={newCourse.content}
                onChange={(v) => setNewCourse((prev) => ({ ...prev, content: v }))}
              />
            </div>
            <div className="flex justify-end">
              <button className="btn-primary" type="submit" disabled={createCourse.isPending}>
                {createCourse.isPending ? 'Создание...' : 'Создать курс'}
              </button>
            </div>
          </form>
        </div>
      )}

      <div className="grid gap-4 lg:grid-cols-2">
        {courses.map((course: Course) => (
          <div key={course.id} className="card space-y-3">
            <div className="flex items-start justify-between gap-3">
              <div>
                <p className="text-sm uppercase text-gray-500">Курс #{course.id}</p>
                <Link
                  to={`/courses/${course.id}`}
                  className="text-lg font-semibold text-gray-900 hover:text-primary-700 hover:underline"
                >
                  {course.title}
                </Link>
                <p className="text-sm text-gray-600">{course.description || 'Описание не задано'}</p>
              </div>
              <div className="rounded-full bg-gray-100 px-3 py-1 text-xs uppercase text-gray-700">
                {course.is_published ? 'Опубликован' : 'Черновик'}
              </div>
            </div>

            <div className="flex flex-wrap items-center gap-3 text-sm text-gray-600">
              <span className="flex items-center gap-2">
                <Clock3 className="h-4 w-4 text-gray-400" />
                {course.duration_minutes} минут
              </span>
              <Link to={`/courses/${course.id}`} className="text-primary-600 hover:underline">
                Открыть курс →
              </Link>
            </div>

            {isOwner && (
              <div className="space-y-3">
                {!course.is_published && (
                  <button
                    className="btn-secondary"
                    onClick={() => publishCourse.mutateAsync(course.id)}
                    disabled={publishCourse.isPending}
                  >
                    {publishCourse.isPending ? 'Публикация...' : 'Опубликовать'}
                  </button>
                )}

                <div className="rounded-md bg-gray-50 p-3">
                  <p className="text-sm font-medium text-gray-900">Назначить курс</p>
                  <div className="mt-2 flex gap-2">
                    <select
                      className="input"
                      value={assignmentTargets[course.id] ?? ''}
                      onChange={(e) =>
                        setAssignmentTargets((prev) => ({
                          ...prev,
                          [course.id]: e.target.value,
                        }))
                      }
                    >
                      <option value="">Выберите пользователя</option>
                      {users.map((u) => (
                        <option key={u.id} value={u.id}>
                          {u.name} ({u.email})
                        </option>
                      ))}
                    </select>
                    <button
                      className="btn-primary"
                      type="button"
                      disabled={!assignmentTargets[course.id]}
                      onClick={() => {
                        const userId = assignmentTargets[course.id];
                        if (userId) {
                          assignCourse.mutate({ courseId: course.id, userId });
                        }
                      }}
                    >
                      <UsersRound className="mr-1 h-4 w-4" />
                      Назначить
                    </button>
                  </div>
                </div>
              </div>
            )}
          </div>
        ))}
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
                  <p className="text-sm font-medium text-gray-900">
                    Курс #{assignment.course_id}
                  </p>
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
    </div>
  );
}
