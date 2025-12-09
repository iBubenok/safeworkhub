/**
 * Утилита для объединения классов CSS.
 */

import { type ClassValue, clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

/**
 * Объединяет классы с поддержкой условий и разрешением конфликтов Tailwind.
 */
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}
