import axios from 'axios';

import { getErrorMessage } from '@/api/client';
import { toast } from '@/store/toastStore';
import type { ErrorResponse } from '@/types';

/** Код ошибки из RFC7807-ответа бэкенда (например SUBSCRIPTION_INACTIVE). */
export function getErrorCode(error: unknown): string | undefined {
  if (axios.isAxiosError(error)) {
    return (error.response?.data as ErrorResponse | undefined)?.error?.code;
  }
  return undefined;
}

export function isSubscriptionError(error: unknown): boolean {
  return getErrorCode(error) === 'SUBSCRIPTION_INACTIVE';
}

export function isForbiddenError(error: unknown): boolean {
  return axios.isAxiosError(error) && error.response?.status === 403;
}

const SUBSCRIPTION_HINT = 'Подписка неактивна. Продлите подписку, чтобы продолжить.';

/** Сообщение для инлайн-показа: отказ по подписке → призыв продлить, иначе текст бэкенда. */
export function getActionErrorMessage(error: unknown): string {
  return isSubscriptionError(error) ? SUBSCRIPTION_HINT : getErrorMessage(error);
}

/**
 * Единая обработка ошибки действия (мутации): отказ по подписке → призыв продлить,
 * прочее → тост с сообщением бэкенда. Заменяет разрозненные alert().
 */
export function handleActionError(error: unknown): void {
  if (isSubscriptionError(error)) {
    toast.error(SUBSCRIPTION_HINT, 'Нужна активная подписка');
    return;
  }
  toast.error(getErrorMessage(error));
}

export { getErrorMessage };
