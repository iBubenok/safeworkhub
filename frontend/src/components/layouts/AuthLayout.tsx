/**
 * Layout для страниц аутентификации.
 */

import { ReactNode } from 'react';

interface AuthLayoutProps {
  children: ReactNode;
}

export function AuthLayout({ children }: AuthLayoutProps) {
  return (
    <div className="flex min-h-screen">
      {/* Левая панель с брендингом */}
      <div className="hidden w-1/2 bg-primary-600 lg:flex lg:flex-col lg:justify-center lg:px-12">
        <div className="max-w-md">
          <h1 className="text-4xl font-bold text-white">SafeWorkHub</h1>
          <p className="mt-4 text-lg text-primary-100">
            Корпоративная платформа по охране труда. Все инструменты для
            специалиста ОТ в одном месте.
          </p>
          <ul className="mt-8 space-y-4 text-primary-100">
            <li className="flex items-center gap-3">
              <span className="flex h-8 w-8 items-center justify-center rounded-full bg-primary-500 text-white">
                ✓
              </span>
              База знаний и нормативные документы
            </li>
            <li className="flex items-center gap-3">
              <span className="flex h-8 w-8 items-center justify-center rounded-full bg-primary-500 text-white">
                ✓
              </span>
              Онлайн-обучение и аттестация
            </li>
            <li className="flex items-center gap-3">
              <span className="flex h-8 w-8 items-center justify-center rounded-full bg-primary-500 text-white">
                ✓
              </span>
              Шаблоны документов и сервисы
            </li>
          </ul>
        </div>
      </div>

      {/* Правая панель с формой */}
      <div className="flex w-full items-center justify-center px-4 py-12 lg:w-1/2">
        <div className="w-full max-w-md">{children}</div>
      </div>
    </div>
  );
}
