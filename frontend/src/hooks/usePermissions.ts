import { useAuth } from '@/hooks/useAuth';
import { useAuthStore } from '@/store/authStore';

/**
 * Единая точка ролевых прав. Суперпользователь приравнивается к владельцу
 * (на бэкенде он проходит любые ролевые гейты).
 */
export function usePermissions() {
  const { user, role } = useAuth();
  const organizationId = useAuthStore((state) => state.organizationId);
  const isSuperuser = Boolean(user?.is_superuser);
  const isOwner = role === 'org_owner' || isSuperuser;
  const isMember = Boolean(user) && !isOwner;
  return { user, role, organizationId, isOwner, isSuperuser, isMember };
}
