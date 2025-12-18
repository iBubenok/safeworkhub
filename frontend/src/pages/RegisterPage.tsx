/**
 * Страница регистрации организации.
 */

import { useState } from 'react';
import { Link } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';

import { useAuth } from '@/hooks/useAuth';
import { getErrorMessage } from '@/api/client';

const registerSchema = z
  .object({
    organization_name: z.string().min(1, 'Введите название организации'),
    inn: z
      .string()
      .regex(/^\d{10,12}$/, 'ИНН должен содержать 10 или 12 цифр'),
    admin_name: z.string().min(1, 'Введите имя'),
    admin_email: z.string().email('Введите корректный email'),
    admin_password: z.string().min(8, 'Пароль должен содержать минимум 8 символов'),
    confirm_password: z.string(),
  })
  .refine((data) => data.admin_password === data.confirm_password, {
    message: 'Пароли не совпадают',
    path: ['confirm_password'],
  });

type RegisterFormData = z.infer<typeof registerSchema>;

export function RegisterPage() {
  const { register: registerOrg, isRegistering } = useAuth();
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<RegisterFormData>({
    resolver: zodResolver(registerSchema),
  });

  const onSubmit = async (data: RegisterFormData) => {
    setError(null);
    try {
      await registerOrg({
        organization_name: data.organization_name,
        inn: data.inn,
        admin_name: data.admin_name,
        admin_email: data.admin_email,
        admin_password: data.admin_password,
      });
      setSuccess(true);
    } catch (err) {
      setError(getErrorMessage(err));
    }
  };

  if (success) {
    return (
      <div className="animate-fade-in">
        <div className="card text-center">
          <div className="mb-4 text-6xl">✓</div>
          <h2 className="text-xl font-semibold text-gray-900">
            Регистрация завершена!
          </h2>
          <p className="mt-2 text-gray-600">
            На указанный email отправлено письмо для подтверждения.
          </p>
          <Link to="/login" className="btn-primary mt-6 inline-block">
            Перейти к входу
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="animate-fade-in">
      {/* Логотип для мобильных */}
      <div className="mb-8 text-center lg:hidden">
        <h1 className="text-3xl font-bold text-primary-600">SafeWorkHub</h1>
        <p className="mt-2 text-gray-600">Платформа по охране труда</p>
      </div>

      <div className="card">
        <div className="card-header">
          <h2 className="card-title text-center">Регистрация организации</h2>
        </div>

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          {error && (
            <div className="rounded-md bg-red-50 p-3 text-sm text-red-600">
              {error}
            </div>
          )}

          <div className="border-b pb-4">
            <h3 className="mb-3 font-medium text-gray-900">Данные организации</h3>

            <div className="space-y-3">
              <div>
                <label htmlFor="organization_name" className="label">
                  Название организации
                </label>
                <input
                  {...register('organization_name')}
                  type="text"
                  id="organization_name"
                  className="input"
                  placeholder="ООО «Название»"
                />
                {errors.organization_name && (
                  <p className="error-message">{errors.organization_name.message}</p>
                )}
              </div>

              <div>
                <label htmlFor="inn" className="label">
                  ИНН
                </label>
                <input
                  {...register('inn')}
                  type="text"
                  id="inn"
                  className="input"
                  placeholder="1234567890"
                  maxLength={12}
                />
                {errors.inn && (
                  <p className="error-message">{errors.inn.message}</p>
                )}
              </div>
            </div>
          </div>

          <div>
            <h3 className="mb-3 font-medium text-gray-900">Данные администратора</h3>

            <div className="space-y-3">
              <div>
                <label htmlFor="admin_name" className="label">
                  Имя
                </label>
                <input
                  {...register('admin_name')}
                  type="text"
                  id="admin_name"
                  className="input"
                  placeholder="Иван Иванов"
                />
                {errors.admin_name && (
                  <p className="error-message">{errors.admin_name.message}</p>
                )}
              </div>

              <div>
                <label htmlFor="adminEmail" className="label">
                  Email
                </label>
                <input
                  {...register('admin_email')}
                  type="email"
                  id="adminEmail"
                  className="input"
                  placeholder="admin@example.com"
                />
                {errors.admin_email && (
                  <p className="error-message">{errors.admin_email.message}</p>
                )}
              </div>

              <div>
                <label htmlFor="adminPassword" className="label">
                  Пароль
                </label>
                <input
                  {...register('admin_password')}
                  type="password"
                  id="adminPassword"
                  className="input"
                  placeholder="Минимум 8 символов"
                />
                {errors.admin_password && (
                  <p className="error-message">{errors.admin_password.message}</p>
                )}
              </div>

              <div>
                <label htmlFor="confirm_password" className="label">
                  Подтверждение пароля
                </label>
                <input
                  {...register('confirm_password')}
                  type="password"
                  id="confirm_password"
                  className="input"
                  placeholder="Повторите пароль"
                />
                {errors.confirm_password && (
                  <p className="error-message">{errors.confirm_password.message}</p>
                )}
              </div>
            </div>
          </div>

          <button
            type="submit"
            className="btn-primary w-full"
            disabled={isRegistering}
          >
            {isRegistering ? 'Регистрация...' : 'Зарегистрироваться'}
          </button>
        </form>

        <p className="mt-6 text-center text-sm text-gray-600">
          Уже есть аккаунт?{' '}
          <Link to="/login" className="text-primary-600 hover:underline">
            Войти
          </Link>
        </p>
      </div>
    </div>
  );
}
