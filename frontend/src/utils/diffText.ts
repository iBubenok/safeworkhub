import { diffWords, type Change } from 'diff';

export interface DiffSegment {
  value: string;
  added: boolean;
  removed: boolean;
}

function normalize(changes: Change[]): DiffSegment[] {
  return changes.map((c) => ({ value: c.value, added: !!c.added, removed: !!c.removed }));
}

/** Пословный diff — подсвечивает изменённые слова (для заголовка, описания, текста). */
export function wordDiff(oldStr: string | null | undefined, newStr: string | null | undefined): DiffSegment[] {
  return normalize(diffWords(oldStr ?? '', newStr ?? ''));
}
