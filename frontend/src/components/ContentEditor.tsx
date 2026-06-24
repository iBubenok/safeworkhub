import { useState } from 'react';
import { Code } from 'lucide-react';

import { Markdown } from '@/components/Markdown';
import { MarkdownEditor } from '@/components/MarkdownEditor';
import type { MaterialContentFormat } from '@/types';

interface ContentEditorProps {
  value: string;
  onChange: (value: string) => void;
  format: MaterialContentFormat;
  onFormatChange: (format: MaterialContentFormat) => void;
  id?: string;
}

const FORMATS: { value: MaterialContentFormat; label: string }[] = [
  { value: 'markdown', label: 'Markdown' },
  { value: 'html', label: 'HTML' },
];

/**
 * Редактор тела материала с выбором формата (Markdown / HTML).
 * Markdown — с панелью инструментов; HTML — простое поле с предпросмотром.
 * Оба формата рендерятся одним безопасным конвейером (Markdown-компонент
 * с санитизацией HTML), поэтому скрипты в превью не исполняются.
 */
export function ContentEditor({ value, onChange, format, onFormatChange, id }: ContentEditorProps) {
  return (
    <div className="space-y-2">
      <div className="flex items-center gap-2">
        <span className="text-xs text-gray-500">Формат:</span>
        {FORMATS.map((f) => (
          <button
            key={f.value}
            type="button"
            onClick={() => onFormatChange(f.value)}
            className={`rounded-full px-3 py-1 text-xs font-medium transition-colors ${
              format === f.value
                ? 'bg-primary-600 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            {f.label}
          </button>
        ))}
      </div>

      {format === 'markdown' ? (
        <MarkdownEditor id={id} value={value} onChange={onChange} />
      ) : (
        <HtmlEditor id={id} value={value} onChange={onChange} />
      )}
    </div>
  );
}

function HtmlEditor({
  value,
  onChange,
  id,
}: {
  value: string;
  onChange: (value: string) => void;
  id?: string;
}) {
  const [preview, setPreview] = useState(false);

  return (
    <div className="overflow-hidden rounded-md border border-gray-300 focus-within:border-primary-500 focus-within:ring-1 focus-within:ring-primary-500">
      <div className="flex items-center justify-between gap-2 border-b border-gray-200 bg-gray-50 px-2 py-1.5">
        <span className="flex items-center gap-2 text-xs text-gray-500">
          <span className="rounded bg-gray-200 px-1.5 py-0.5 font-medium text-gray-700">HTML</span>
          опасные теги (скрипты) удаляются автоматически
        </span>
        <button
          type="button"
          title={preview ? 'Редактор' : 'Превью'}
          aria-label={preview ? 'Редактор' : 'Превью'}
          aria-pressed={preview}
          onClick={() => setPreview((v) => !v)}
          className={`rounded p-1.5 transition ${
            preview ? 'bg-primary-100 text-primary-700' : 'text-gray-600 hover:bg-gray-200'
          }`}
        >
          <Code size={16} />
        </button>
      </div>

      {preview ? (
        <div className="min-h-[200px] overflow-y-auto bg-white p-3">
          {value ? <Markdown>{value}</Markdown> : <p className="text-sm text-gray-400">Нечего показать</p>}
        </div>
      ) : (
        <textarea
          id={id}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          className="block min-h-[200px] w-full resize-y px-3 py-2 font-mono text-sm focus:outline-none"
          placeholder={'<h2>Заголовок</h2>\n<p>Текст с <b>разметкой</b></p>'}
        />
      )}
    </div>
  );
}
