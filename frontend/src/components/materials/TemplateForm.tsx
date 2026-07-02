import { useRef, useState } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { Paperclip, X } from 'lucide-react';

import * as materialsApi from '@/api/materials';
import { getActionErrorMessage } from '@/api/errors';
import { ContentEditor } from '@/components/ContentEditor';
import { formatFileSize } from '@/utils/formatFileSize';
import type { Category, MaterialStatus } from '@/types';

const ALLOWED_EXTENSIONS = ['doc', 'docx', 'xls', 'xlsx', 'pdf', 'odt', 'ods', 'rtf', 'txt', 'csv'];
const MAX_SIZE_MB = 25;

/** Форма создания шаблона: базовые поля + прикреплённые файлы (1..N). */
export function TemplateForm({ categories }: { categories: Category[] }) {
  const [title, setTitle] = useState('');
  const [summary, setSummary] = useState('');
  const [content, setContent] = useState('');
  const [categoryId, setCategoryId] = useState<number | undefined>(undefined);
  const [files, setFiles] = useState<File[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const fileInputRef = useRef<HTMLInputElement>(null);
  const queryClient = useQueryClient();
  const navigate = useNavigate();

  const validateFile = (file: File): string | null => {
    const ext = file.name.split('.').pop()?.toLowerCase() ?? '';
    if (!ALLOWED_EXTENSIONS.includes(ext)) {
      return `Недопустимый тип файла .${ext}`;
    }
    if (file.size > MAX_SIZE_MB * 1024 * 1024) {
      return `Файл «${file.name}» превышает ${MAX_SIZE_MB} МБ`;
    }
    return null;
  };

  const handleFilesSelected = (selected: FileList | null) => {
    if (!selected) return;
    setError(null);
    const next: File[] = [];
    for (const file of Array.from(selected)) {
      const problem = validateFile(file);
      if (problem) {
        setError(problem);
        continue;
      }
      next.push(file);
    }
    setFiles((prev) => [...prev, ...next]);
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  const removeFile = (index: number) => setFiles((prev) => prev.filter((_, i) => i !== index));

  const submit = async (status: MaterialStatus) => {
    setError(null);
    if (!title.trim()) {
      setError('Укажите заголовок шаблона');
      return;
    }
    setSubmitting(true);
    try {
      const material = await materialsApi.createTemplate({
        title,
        summary: summary || null,
        content,
        category_id: categoryId,
        status,
      });
      for (const file of files) {
        await materialsApi.uploadAttachment(material.id, file);
      }
      queryClient.invalidateQueries({ queryKey: ['materials'] });
      navigate(`/materials/${material.id}`);
    } catch (e) {
      setError(getActionErrorMessage(e));
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <form
      className="space-y-3"
      onSubmit={(e) => {
        e.preventDefault();
        void submit('draft');
      }}
    >
      {error && <div className="rounded-md bg-red-50 p-3 text-sm text-red-600">{error}</div>}

      <div className="grid gap-3 md:grid-cols-2">
        <div>
          <label className="label" htmlFor="tpl-title">
            Заголовок
          </label>
          <input id="tpl-title" className="input" value={title} onChange={(e) => setTitle(e.target.value)} required />
        </div>
        <div>
          <label className="label" htmlFor="tpl-category">
            Категория
          </label>
          <select
            id="tpl-category"
            className="input"
            value={categoryId ?? ''}
            onChange={(e) => setCategoryId(e.target.value ? Number(e.target.value) : undefined)}
          >
            <option value="">Без категории</option>
            {categories.map((category) => (
              <option key={category.id} value={category.id}>
                {category.name}
              </option>
            ))}
          </select>
        </div>
      </div>

      <div>
        <label className="label" htmlFor="tpl-summary">
          Краткое описание
        </label>
        <input id="tpl-summary" className="input" value={summary} onChange={(e) => setSummary(e.target.value)} />
      </div>

      <div>
        <label className="label" htmlFor="tpl-content">
          Инструкция по заполнению (необязательно)
        </label>
        <ContentEditor id="tpl-content" value={content} onChange={setContent} />
      </div>

      <div>
        <span className="label">Файлы шаблона</span>
        <button
          type="button"
          className="btn-secondary flex items-center gap-2"
          onClick={() => fileInputRef.current?.click()}
        >
          <Paperclip className="h-4 w-4" /> Выбрать файлы
        </button>
        <input
          ref={fileInputRef}
          type="file"
          multiple
          className="hidden"
          accept={ALLOWED_EXTENSIONS.map((e) => `.${e}`).join(',')}
          onChange={(e) => handleFilesSelected(e.target.files)}
        />
        <p className="mt-1 text-xs text-gray-400">
          Разрешены: {ALLOWED_EXTENSIONS.join(', ')}. До {MAX_SIZE_MB} МБ на файл.
        </p>

        {files.length > 0 && (
          <ul className="mt-2 space-y-1">
            {files.map((file, index) => (
              <li
                key={`${file.name}-${index}`}
                className="flex items-center justify-between rounded-md border border-gray-200 px-3 py-2 text-sm"
              >
                <span className="min-w-0 flex-1 truncate" title={file.name}>
                  {file.name} <span className="text-gray-400">({formatFileSize(file.size)})</span>
                </span>
                <button
                  type="button"
                  aria-label="Убрать файл"
                  className="ml-2 rounded p-1 text-gray-400 hover:bg-gray-100 hover:text-gray-600"
                  onClick={() => removeFile(index)}
                >
                  <X className="h-4 w-4" />
                </button>
              </li>
            ))}
          </ul>
        )}
      </div>

      <div className="flex justify-end gap-2">
        <button type="submit" className="btn-secondary" disabled={submitting}>
          {submitting ? 'Сохранение...' : 'Сохранить черновик'}
        </button>
        <button type="button" className="btn-primary" disabled={submitting} onClick={() => void submit('published')}>
          Опубликовать
        </button>
      </div>
    </form>
  );
}
