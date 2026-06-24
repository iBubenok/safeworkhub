import { Fragment, useLayoutEffect, useRef, useState } from 'react';
import {
  Bold,
  Code,
  Code2,
  Heading1,
  Heading2,
  Heading3,
  Image as ImageIcon,
  Italic,
  Link2,
  List,
  ListOrdered,
  Minus,
  Quote,
  SquareCode,
  Strikethrough,
  Table,
  type LucideIcon,
} from 'lucide-react';

import { Markdown } from '@/components/Markdown';

interface MarkdownEditorProps {
  value: string;
  onChange: (value: string) => void;
  id?: string;
  placeholder?: string;
  /** Tailwind-класс высоты области (по умолчанию min-h-[200px]). */
  heightClass?: string;
}

interface ToolbarAction {
  icon: LucideIcon;
  label: string;
  run: () => void;
}

/**
 * Редактор Markdown с панелью форматирования и переключателем «код ⟷ превью».
 *
 * Контролируемый компонент (value/onChange) — переиспользуется и при создании,
 * и при редактировании материала. Кнопки панели либо оборачивают выделенный
 * текст разметкой, либо вставляют готовую конструкцию для начала ввода.
 */
export function MarkdownEditor({
  value,
  onChange,
  id,
  placeholder,
  heightClass = 'min-h-[200px]',
}: MarkdownEditorProps) {
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  // Желаемое выделение после программной правки value — применяется после ре-рендера.
  const pendingSelection = useRef<[number, number] | null>(null);
  const [preview, setPreview] = useState(false);

  useLayoutEffect(() => {
    if (pendingSelection.current && textareaRef.current) {
      const [start, end] = pendingSelection.current;
      textareaRef.current.focus();
      textareaRef.current.setSelectionRange(start, end);
      pendingSelection.current = null;
    }
  });

  // Обернуть выделение парой маркеров (жирный/курсив/код и т.п.).
  const wrap = (before: string, after: string, fallback = 'текст') => {
    const ta = textareaRef.current;
    if (!ta) return;
    const { selectionStart: start, selectionEnd: end } = ta;
    const selected = value.slice(start, end) || fallback;
    onChange(value.slice(0, start) + before + selected + after + value.slice(end));
    const innerStart = start + before.length;
    pendingSelection.current = [innerStart, innerStart + selected.length];
  };

  // Добавить префикс к каждой строке выделения (заголовок/список/цитата).
  const prefixLines = (makePrefix: (index: number) => string) => {
    const ta = textareaRef.current;
    if (!ta) return;
    const { selectionStart: start, selectionEnd: end } = ta;
    const lineStart = value.lastIndexOf('\n', start - 1) + 1;
    const block = value.slice(lineStart, end);
    const transformed = block
      .split('\n')
      .map((line, index) => makePrefix(index) + line)
      .join('\n');
    onChange(value.slice(0, lineStart) + transformed + value.slice(end));
    pendingSelection.current = [lineStart, lineStart + transformed.length];
  };

  // Вставить блочную конструкцию на отдельной строке (например, разделитель ---).
  const insertBlock = (text: string) => {
    const ta = textareaRef.current;
    if (!ta) return;
    const { selectionStart: start } = ta;
    const leadingBreak = start > 0 && value[start - 1] !== '\n' ? '\n' : '';
    const inserted = `${leadingBreak}${text}\n`;
    onChange(value.slice(0, start) + inserted + value.slice(start));
    const caret = start + inserted.length;
    pendingSelection.current = [caret, caret];
  };

  // Вставить ссылку/изображение и поставить курсор в адрес.
  const insertLink = (markerPrefix: string) => {
    const ta = textareaRef.current;
    if (!ta) return;
    const { selectionStart: start, selectionEnd: end } = ta;
    const text = value.slice(start, end) || 'текст';
    const url = 'https://';
    const inserted = `${markerPrefix}[${text}](${url})`;
    onChange(value.slice(0, start) + inserted + value.slice(end));
    const urlStart = start + markerPrefix.length + 1 + text.length + 2;
    pendingSelection.current = [urlStart, urlStart + url.length];
  };

  const groups: ToolbarAction[][] = [
    [
      { icon: Heading1, label: 'Заголовок 1', run: () => prefixLines(() => '# ') },
      { icon: Heading2, label: 'Заголовок 2', run: () => prefixLines(() => '## ') },
      { icon: Heading3, label: 'Заголовок 3', run: () => prefixLines(() => '### ') },
    ],
    [
      { icon: Bold, label: 'Жирный', run: () => wrap('**', '**') },
      { icon: Italic, label: 'Курсив', run: () => wrap('*', '*') },
      { icon: Strikethrough, label: 'Зачёркнутый', run: () => wrap('~~', '~~') },
      { icon: SquareCode, label: 'Код (строкой)', run: () => wrap('`', '`', 'код') },
    ],
    [
      { icon: List, label: 'Маркированный список', run: () => prefixLines(() => '- ') },
      { icon: ListOrdered, label: 'Нумерованный список', run: () => prefixLines((i) => `${i + 1}. `) },
      { icon: Quote, label: 'Цитата', run: () => prefixLines(() => '> ') },
      { icon: Minus, label: 'Разделитель (---)', run: () => insertBlock('---') },
    ],
    [
      { icon: Link2, label: 'Ссылка', run: () => insertLink('') },
      { icon: ImageIcon, label: 'Изображение', run: () => insertLink('!') },
      { icon: Code2, label: 'Блок кода', run: () => wrap('\n```\n', '\n```\n', 'код') },
      {
        icon: Table,
        label: 'Таблица',
        run: () => insertBlock('| Заголовок | Заголовок |\n| --- | --- |\n| Ячейка | Ячейка |'),
      },
    ],
  ];

  return (
    <div className="overflow-hidden rounded-md border border-gray-300 focus-within:border-primary-500 focus-within:ring-1 focus-within:ring-primary-500">
      <div className="flex flex-wrap items-center gap-1 border-b border-gray-200 bg-gray-50 px-2 py-1.5">
        {groups.map((group, groupIndex) => (
          <Fragment key={groupIndex}>
            {groupIndex > 0 && <span className="mx-1 h-5 w-px bg-gray-300" />}
            {group.map((action) => (
              <button
                key={action.label}
                type="button"
                title={action.label}
                aria-label={action.label}
                disabled={preview}
                onClick={action.run}
                className="rounded p-1.5 text-gray-600 transition hover:bg-gray-200 disabled:cursor-not-allowed disabled:opacity-40"
              >
                <action.icon size={16} />
              </button>
            ))}
          </Fragment>
        ))}

        <button
          type="button"
          title={preview ? 'Редактор' : 'Превью'}
          aria-label={preview ? 'Редактор' : 'Превью'}
          aria-pressed={preview}
          onClick={() => setPreview((v) => !v)}
          className={`ml-auto rounded p-1.5 transition ${
            preview ? 'bg-primary-100 text-primary-700' : 'text-gray-600 hover:bg-gray-200'
          }`}
        >
          <Code size={16} />
        </button>
      </div>

      {preview ? (
        <div className={`${heightClass} overflow-y-auto bg-white p-3`}>
          {value ? <Markdown>{value}</Markdown> : <p className="text-sm text-gray-400">Нечего показать</p>}
        </div>
      ) : (
        <textarea
          id={id}
          ref={textareaRef}
          className={`block w-full resize-y ${heightClass} px-3 py-2 font-mono text-sm focus:outline-none`}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder={placeholder}
        />
      )}
    </div>
  );
}
