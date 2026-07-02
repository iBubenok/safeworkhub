import { Link } from 'react-router-dom';
import { CreditCard, Lock } from 'lucide-react';

type AccessDeniedVariant = 'role' | 'subscription';

/** Состояние «нет доступа» для секции/страницы. Роль — скрыто/запрещено; подписка — призыв продлить. */
export function AccessDenied({
  variant = 'role',
  title,
  message,
}: {
  variant?: AccessDeniedVariant;
  title?: string;
  message?: string;
}) {
  const isSubscription = variant === 'subscription';
  return (
    <div className="card flex flex-col items-center gap-3 py-12 text-center">
      {isSubscription ? (
        <CreditCard className="h-10 w-10 text-primary-400" />
      ) : (
        <Lock className="h-10 w-10 text-gray-300" />
      )}
      <h2 className="text-lg font-semibold text-gray-900">
        {title ?? (isSubscription ? 'Требуется активная подписка' : 'Недостаточно прав')}
      </h2>
      <p className="max-w-md text-sm text-gray-500">
        {message ??
          (isSubscription
            ? 'Подписка организации неактивна. Продлите её, чтобы пользоваться этим разделом.'
            : 'У вас нет доступа к этому разделу. Обратитесь к владельцу организации.')}
      </p>
      {isSubscription && (
        <Link to="/settings" className="btn-primary mt-2">
          Продлить подписку
        </Link>
      )}
    </div>
  );
}
