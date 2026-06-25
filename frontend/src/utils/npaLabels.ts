import type { NpaActKind, NpaLevel, NpaStatus } from '@/types';

/** Русские подписи для enum НПА (для форм и карточки). */
export const npaActKindLabels: Record<NpaActKind, string> = {
  federal_law: 'Федеральный закон (ФЗ)',
  constitutional_law: 'Федеральный конституционный закон (ФКЗ)',
  code: 'Кодекс',
  presidential_decree: 'Указ Президента',
  government_decree: 'Постановление Правительства',
  ministry_order: 'Приказ министерства/ведомства',
  gost: 'ГОСТ',
  sanpin: 'СанПиН',
  sp: 'Свод правил (СП)',
  regional_law: 'Региональный закон/акт',
  municipal_act: 'Муниципальный акт',
  local_act: 'Локальный нормативный акт',
  other: 'Иное',
};

export const npaLevelLabels: Record<NpaLevel, string> = {
  federal: 'Федеральный',
  regional: 'Региональный',
  municipal: 'Муниципальный',
  local: 'Локальный',
};

export const npaStatusLabels: Record<NpaStatus, string> = {
  in_force: 'Действует',
  not_in_force: 'Не вступил в силу',
  repealed: 'Утратил силу',
  amended: 'Изменён',
  suspended: 'Приостановлен',
};
