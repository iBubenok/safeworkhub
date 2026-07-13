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

  /**
   * Может ли текущий пользователь сменить пароль указанному сотруднику.
   * Себе — всегда; суперпользователь — любому; владелец — только сотрудникам (role member).
   */
  const canChangePasswordOf = (target: { id: string; role: string; is_superuser: boolean }): boolean => {
    if (!user) return false;
    if (target.id === user.id) return true;
    if (target.is_superuser && !isSuperuser) return false;
    if (isSuperuser) return true;
    if (role === 'org_owner') return target.role === 'member';
    return false;
  };

  return { user, role, organizationId, isOwner, isSuperuser, isMember, canChangePasswordOf };
}
