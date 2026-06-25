/**
 * Возвращает URL, только если он использует безопасную схему http/https.
 * Иначе — undefined. Защита от XSS через `javascript:`/`data:` в href/src,
 * которые React 18 не нейтрализует во время выполнения.
 */
export function safeHttpUrl(url: string | null | undefined): string | undefined {
  if (!url) return undefined;
  try {
    const parsed = new URL(url, window.location.origin);
    if (parsed.protocol === 'http:' || parsed.protocol === 'https:') {
      return parsed.href;
    }
  } catch {
    return undefined;
  }
  return undefined;
}
