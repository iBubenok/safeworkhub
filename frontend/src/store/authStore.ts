import { create } from 'zustand';

import type { TokenResponse, User } from '@/types';

interface AuthState {
  user: User | null;
  accessToken: string | null;
  organizationId: number | null;
  role: string | null;
  isInitialized: boolean;
  setSession: (tokens: TokenResponse) => void;
  setUser: (user: User) => void;
  clearAuth: () => void;
  setInitialized: (value: boolean) => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  accessToken: null,
  organizationId: null,
  role: null,
  isInitialized: false,

  setSession: (tokens) =>
    set({
      user: tokens.user,
      accessToken: tokens.access_token,
      organizationId: tokens.organization_id,
      role: tokens.role,
    }),

  setUser: (user) => set({ user }),

  clearAuth: () =>
    set({
      user: null,
      accessToken: null,
      organizationId: null,
      role: null,
    }),

  setInitialized: (value) => set({ isInitialized: value }),
}));
