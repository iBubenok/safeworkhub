/**
 * Страница входа в систему.
 */

import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';

import { useAuth } from '@/hooks/useAuth';
import { getErrorMessage } from '@/api/client';

const loginSchema = z.object({
  email: z.string().email('Введите корректный email'),
  password: z.string().min(1, 'Введите пароль'),
});

type LoginFormData = z.infer<typeof loginSchema>;

export function LoginPage() {
  const navigate = useNavigate();
  const { login, isLoggingIn } = useAuth();
  const [error, setError] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginFormData>({
    resolver: zodResolver(loginSchema),
  });

  const onSubmit = async (data: LoginFormData) => {
    setError(null);
    try {
      await login(data);
      navigate('/dashboard');
    } catch (err) {
      setError(getErrorMessage(err));
    }
  };

  return (
    <div className="animate-fade-in">
      {/* Логотип для мобильных */}
      <div className="mb-8 text-center lg:hidden">
        <h1 className="text-3xl font-bold text-primary-600">SafeWorkHub</h1>
        <p className="mt-2 text-gray-600">Платформа по охране труда</p>
      </div>

      <div className="card">
        <div className="card-header">
          <h2 className="card-title text-center">Вход в систему</h2>
        </div>

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          {error && (
            <div className="rounded-md bg-red-50 p-3 text-sm text-red-600">
              {error}
            </div>
          )}

          <div>
            <label htmlFor="email" className="label">
              Email
            </label>
            <input
              {...register('email')}
              type="email"
              id="email"
              className="input"
              placeholder="user@example.com"
              autoComplete="email"
            />
            {errors.email && (
              <p className="error-message">{errors.email.message}</p>
            )}
          </div>

          <div>
            <label htmlFor="password" className="label">
              Пароль
            </label>
            <input
              {...register('password')}
              type="password"
              id="password"
              className="input"
              placeholder="••••••••"
              autoComplete="current-password"
            />
            {errors.password && (
              <p className="error-message">{errors.password.message}</p>
            )}
          </div>

          <button
            type="submit"
            className="btn-primary w-full"
            disabled={isLoggingIn}
          >
            {isLoggingIn ? 'Вход...' : 'Войти'}
          </button>
        </form>

        <p className="mt-6 text-center text-sm text-gray-600">
          Нет аккаунта?{' '}
          <Link to="/register" className="text-primary-600 hover:underline">
            Зарегистрироваться
          </Link>
        </p>
      </div>
    </div>
  );
}
