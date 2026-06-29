/** Человекочитаемые подписи ролей пользователя в организации. */

export const roleLabels: Record<string, string> = {
  org_owner: 'Владелец',
  member: 'Сотрудник',
};

/** Метка роли с запасным вариантом для неизвестных значений. */
export function roleLabel(role: string | null | undefined): string {
  if (!role) return '—';
  return roleLabels[role] ?? role;
}
