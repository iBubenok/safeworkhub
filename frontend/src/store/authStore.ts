/**
 * Хранилище состояния аутентификации.
 */

import { create } from 'zustand';

import type { User } from '@/types';

interface AuthState {
  user: User | null;
  isInitialized: boolean;
  setUser: (user: User) => void;
  clearAuth: () => void;
  setInitialized: (value: boolean) => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  isInitialized: false,

  setUser: (user) => set({ user }),

  clearAuth: () => set({ user: null }),

  setInitialized: (value) => set({ isInitialized: value }),
}));
