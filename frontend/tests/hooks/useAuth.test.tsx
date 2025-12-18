import { beforeEach, describe, expect, it } from 'vitest';

import { useAuthStore } from '@/store/authStore';
import type { TokenResponse } from '@/types';

const tokens: TokenResponse = {
  access_token: 'test-access',
  token_type: 'bearer',
  expires_in: 1800,
  refresh_expires_in: 3600,
  organization_id: 1,
  role: 'org_owner',
  user: {
    id: 'user-1',
    email: 'user@example.com',
    name: 'Пользователь',
    is_active: true,
    is_superuser: false,
    primary_organization_id: 1,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  },
};

describe('auth store', () => {
  beforeEach(() => {
    useAuthStore.setState({
      user: null,
      accessToken: null,
      organizationId: null,
      role: null,
      isInitialized: false,
      setSession: useAuthStore.getState().setSession,
      setUser: useAuthStore.getState().setUser,
      clearAuth: useAuthStore.getState().clearAuth,
      setInitialized: useAuthStore.getState().setInitialized,
    });
  });

  it('setSession сохраняет токен и пользователя', () => {
    useAuthStore.getState().setSession(tokens);

    const state = useAuthStore.getState();
    expect(state.user?.email).toBe(tokens.user.email);
    expect(state.accessToken).toBe(tokens.access_token);
    expect(state.organizationId).toBe(tokens.organization_id);
    expect(state.role).toBe(tokens.role);
  });

  it('clearAuth очищает состояние', () => {
    useAuthStore.getState().setSession(tokens);
    useAuthStore.getState().clearAuth();

    const state = useAuthStore.getState();
    expect(state.user).toBeNull();
    expect(state.accessToken).toBeNull();
    expect(state.organizationId).toBeNull();
    expect(state.role).toBeNull();
  });
});
