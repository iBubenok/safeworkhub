import type {
  ChecklistAnswerType,
  ChecklistComplianceValue,
  ChecklistRunResult,
  ChecklistRunStatus,
  ChecklistStatus,
} from '@/types';

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

export const checklistRunStatusLabels: Record<ChecklistRunStatus, string> = {
  in_progress: 'В процессе',
  completed: 'Завершена',
};

export const checklistRunResultLabels: Record<ChecklistRunResult, string> = {
  passed: 'Пройдено',
  has_issues: 'Есть нарушения',
};

/** Подписи вариантов ответа «Соответствие». */
export const complianceValueLabels: Record<ChecklistComplianceValue, string> = {
  compliant: 'Соответствует',
  non_compliant: 'Не соответствует',
  not_applicable: 'Не применимо',
};
