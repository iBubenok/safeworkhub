import type { ChecklistAnswerType, ChecklistStatus } from '@/types';

export const checklistStatusLabels: Record<ChecklistStatus, string> = {
  draft: 'Черновик',
  published: 'Опубликован',
  archived: 'В архиве',
};

export const checklistAnswerTypeLabels: Record<ChecklistAnswerType, string> = {
  compliance: 'Соответствует / Не соответствует / Не применимо',
  yes_no: 'Да / Нет',
  text: 'Текст (комментарий)',
  number: 'Число',
};

/** Короткие подписи типа ответа (для бейджей). */
export const checklistAnswerTypeShort: Record<ChecklistAnswerType, string> = {
  compliance: 'Соответствие',
  yes_no: 'Да / Нет',
  text: 'Текст',
  number: 'Число',
};
