import { diffLines, diffWords, type Change } from 'diff';

export interface DiffSegment {
  value: string;
  added: boolean;
  removed: boolean;
}

function normalize(changes: Change[]): DiffSegment[] {
  return changes.map((c) => ({ value: c.value, added: !!c.added, removed: !!c.removed }));
}

/** Пословный diff — для коротких строк (заголовок, описание). */
export function wordDiff(oldStr: string | null | undefined, newStr: string | null | undefined): DiffSegment[] {
  return normalize(diffWords(oldStr ?? '', newStr ?? ''));
}

/** Построчный diff — для тела материала. */
export function lineDiff(oldStr: string | null | undefined, newStr: string | null | undefined): DiffSegment[] {
  return normalize(diffLines(oldStr ?? '', newStr ?? ''));
}
