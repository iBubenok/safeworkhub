import { MarkdownEditor } from '@/components/MarkdownEditor';

interface ContentEditorProps {
  value: string;
  onChange: (value: string) => void;
  id?: string;
}

/**
 * Редактор тела материала на Markdown с панелью инструментов.
 * Inline-HTML поддерживается и безопасно рендерится тем же конвейером
 * (Markdown-компонент с санитизацией) — это вариант «для продвинутых»,
 * отдельный переключатель формата не нужен.
 */
export function ContentEditor({ value, onChange, id }: ContentEditorProps) {
  return <MarkdownEditor id={id} value={value} onChange={onChange} />;
}
