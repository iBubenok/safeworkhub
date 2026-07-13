import { apiClient } from './client';
import type { Course, CourseAssignment } from '@/types';

export async function listCourses(
  limit: number = 20,
  offset: number = 0,
): Promise<Course[]> {
  const response = await apiClient.get<Course[]>('/courses', {
    params: { limit, offset },
  });
  return response.data;
}

export async function getCourse(courseId: number): Promise<Course> {
  const response = await apiClient.get<Course>(`/courses/${courseId}`);
  return response.data;
}

export interface CourseInput {
  title: string;
  description?: string | null;
  content?: string | null;
  duration_minutes?: number;
}

export async function createCourse(data: CourseInput): Promise<Course> {
  const response = await apiClient.post<Course>('/courses', {
    title: data.title,
    description: data.description ?? null,
    content: data.content ?? null,
    duration_minutes: data.duration_minutes ?? 0,
  });
  return response.data;
}

export async function updateCourse(courseId: number, data: Partial<CourseInput>): Promise<Course> {
  const response = await apiClient.patch<Course>(`/courses/${courseId}`, data);
  return response.data;
}

export async function publishCourse(courseId: number): Promise<Course> {
  const response = await apiClient.post<Course>(`/courses/${courseId}/publish`);
  return response.data;
}

export async function assignCourse(courseId: number, userIds: string[]): Promise<CourseAssignment[]> {
  const response = await apiClient.post<CourseAssignment[]>(`/courses/${courseId}/assign`, {
    user_ids: userIds,
  });
  return response.data;
}

export async function updateProgress(courseId: number, progress_percent: number): Promise<CourseAssignment> {
  const response = await apiClient.post<CourseAssignment>(`/courses/${courseId}/progress`, null, {
    params: { progress_percent },
  });
  return response.data;
}

export async function myAssignments(): Promise<CourseAssignment[]> {
  const response = await apiClient.get<CourseAssignment[]>('/courses/assignments/me');
  return response.data;
}
