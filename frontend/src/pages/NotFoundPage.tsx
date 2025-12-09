/**
 * Страница 404 — не найдено.
 */

import { Link } from 'react-router-dom';
import { Home } from 'lucide-react';

export function NotFoundPage() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-50 px-4">
      <div className="text-center">
        <h1 className="text-9xl font-bold text-gray-200">404</h1>
        <h2 className="mt-4 text-2xl font-semibold text-gray-900">
          Страница не найдена
        </h2>
        <p className="mt-2 text-gray-600">
          Запрашиваемая страница не существует или была удалена.
        </p>
        <Link to="/" className="btn-primary mt-6 inline-flex items-center gap-2">
          <Home className="h-4 w-4" />
          На главную
        </Link>
      </div>
    </div>
  );
}
