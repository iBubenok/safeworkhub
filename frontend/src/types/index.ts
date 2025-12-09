/**
 * Общие типы приложения.
 */

// Пользователь
export interface User {
  id: string;
  email: string;
  name: string;
  isActive: boolean;
  createdAt: string;
  updatedAt: string;
}

// Организация
export interface Organization {
  id: number;
  name: string;
  inn: string;
  description: string | null;
  logoUrl: string | null;
  createdAt: string;
  updatedAt: string;
}

// Токены аутентификации
export interface TokenResponse {
  accessToken: string;
  refreshToken: string;
  tokenType: string;
  expiresIn: number;
}

// Запрос на вход
export interface LoginRequest {
  email: string;
  password: string;
}

// Запрос на регистрацию
export interface RegisterRequest {
  organizationName: string;
  inn: string;
  adminEmail: string;
  adminPassword: string;
  adminName: string;
}

// Материал базы знаний
export interface Material {
  id: string;
  title: string;
  summary: string | null;
  content: string;
  type: MaterialType;
  viewsCount: number;
  publishedAt: string | null;
  createdAt: string;
  updatedAt: string;
}

export type MaterialType = 'article' | 'npa' | 'template' | 'reference' | 'news';

// Элемент списка материалов
export interface MaterialListItem {
  id: string;
  title: string;
  summary: string | null;
  type: MaterialType;
  viewsCount: number;
  publishedAt: string | null;
}

// Пагинированный ответ
export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  pageSize: number;
  pages: number;
}

// Ответ с ошибкой
export interface ErrorResponse {
  error: {
    code: string;
    message: string;
    details: Record<string, unknown>;
  };
}

// Параметры пагинации
export interface PaginationParams {
  page?: number;
  pageSize?: number;
}

// Параметры поиска материалов
export interface MaterialSearchParams extends PaginationParams {
  query?: string;
  type?: MaterialType;
  categoryId?: number;
}
