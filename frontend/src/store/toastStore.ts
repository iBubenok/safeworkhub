import { create } from 'zustand';

export type ToastVariant = 'error' | 'success' | 'info';

export interface ToastItem {
  id: string;
  title?: string;
  message: string;
  variant: ToastVariant;
}

interface ToastState {
  toasts: ToastItem[];
  push: (toast: Omit<ToastItem, 'id'>) => void;
  dismiss: (id: string) => void;
}

let counter = 0;

export const useToastStore = create<ToastState>((set) => ({
  toasts: [],
  push: (toast) =>
    set((state) => ({ toasts: [...state.toasts, { ...toast, id: `toast-${++counter}` }] })),
  dismiss: (id) => set((state) => ({ toasts: state.toasts.filter((t) => t.id !== id) })),
}));

/** Императивный хелпер для показа тостов вне React-дерева (в мутациях, интерсепторах). */
export const toast = {
  error: (message: string, title?: string) =>
    useToastStore.getState().push({ message, title, variant: 'error' }),
  success: (message: string, title?: string) =>
    useToastStore.getState().push({ message, title, variant: 'success' }),
  info: (message: string, title?: string) =>
    useToastStore.getState().push({ message, title, variant: 'info' }),
};
