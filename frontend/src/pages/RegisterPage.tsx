/**
 * Страница регистрации организации.
 */

import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';

import { useAuth } from '@/hooks/useAuth';
import { getErrorMessage } from '@/api/client';

const registerSchema = z
  .object({
    organizationName: z.string().min(1, 'Введите название организации'),
    inn: z
      .string()
      .regex(/^\d{10,12}$/, 'ИНН должен содержать 10 или 12 цифр'),
    adminName: z.string().min(1, 'Введите имя'),
    adminEmail: z.string().email('Введите корректный email'),
    adminPassword: z.string().min(8, 'Пароль должен содержать минимум 8 символов'),
    confirmPassword: z.string(),
  })
  .refine((data) => data.adminPassword === data.confirmPassword, {
    message: 'Пароли не совпадают',
    path: ['confirmPassword'],
  });

type RegisterFormData = z.infer<typeof registerSchema>;

export function RegisterPage() {
  const navigate = useNavigate();
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
        organizationName: data.organizationName,
        inn: data.inn,
        adminName: data.adminName,
        adminEmail: data.adminEmail,
        adminPassword: data.adminPassword,
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
                <label htmlFor="organizationName" className="label">
                  Название организации
                </label>
                <input
                  {...register('organizationName')}
                  type="text"
                  id="organizationName"
                  className="input"
                  placeholder="ООО «Название»"
                />
                {errors.organizationName && (
                  <p className="error-message">{errors.organizationName.message}</p>
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
                <label htmlFor="adminName" className="label">
                  Имя
                </label>
                <input
                  {...register('adminName')}
                  type="text"
                  id="adminName"
                  className="input"
                  placeholder="Иван Иванов"
                />
                {errors.adminName && (
                  <p className="error-message">{errors.adminName.message}</p>
                )}
              </div>

              <div>
                <label htmlFor="adminEmail" className="label">
                  Email
                </label>
                <input
                  {...register('adminEmail')}
                  type="email"
                  id="adminEmail"
                  className="input"
                  placeholder="admin@example.com"
                />
                {errors.adminEmail && (
                  <p className="error-message">{errors.adminEmail.message}</p>
                )}
              </div>

              <div>
                <label htmlFor="adminPassword" className="label">
                  Пароль
                </label>
                <input
                  {...register('adminPassword')}
                  type="password"
                  id="adminPassword"
                  className="input"
                  placeholder="Минимум 8 символов"
                />
                {errors.adminPassword && (
                  <p className="error-message">{errors.adminPassword.message}</p>
                )}
              </div>

              <div>
                <label htmlFor="confirmPassword" className="label">
                  Подтверждение пароля
                </label>
                <input
                  {...register('confirmPassword')}
                  type="password"
                  id="confirmPassword"
                  className="input"
                  placeholder="Повторите пароль"
                />
                {errors.confirmPassword && (
                  <p className="error-message">{errors.confirmPassword.message}</p>
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
