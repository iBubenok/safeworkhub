import { useRef, useState } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { Paperclip, X } from 'lucide-react';

import * as materialsApi from '@/api/materials';
import { getActionErrorMessage } from '@/api/errors';
import { ContentEditor } from '@/components/ContentEditor';
import { formatFileSize } from '@/utils/formatFileSize';
import { npaActKindLabels, npaLevelLabels, npaStatusLabels } from '@/utils/npaLabels';
import type { Category, MaterialStatus, NpaActKind, NpaLevel, NpaStatus } from '@/types';

const ALLOWED_EXTENSIONS = ['doc', 'docx', 'xls', 'xlsx', 'pdf', 'odt', 'ods', 'rtf', 'txt', 'csv'];
const MAX_SIZE_MB = 25;

/** Форма создания НПА: метаданные акта + файл с текстом акта. */
export function NpaForm({ categories }: { categories: Category[] }) {
  const [title, setTitle] = useState('');
  const [summary, setSummary] = useState('');
  const [content, setContent] = useState('');
  const [categoryId, setCategoryId] = useState<number | undefined>(undefined);

  const [actKind, setActKind] = useState<NpaActKind>('federal_law');
  const [level, setLevel] = useState<NpaLevel | ''>('');
  const [actStatus, setActStatus] = useState<NpaStatus | ''>('');
  const [documentNumber, setDocumentNumber] = useState('');
  const [adoptionDate, setAdoptionDate] = useState('');
  const [effectiveDate, setEffectiveDate] = useState('');
  const [revisionDate, setRevisionDate] = useState('');
  const [issuingAuthority, setIssuingAuthority] = useState('');
  const [region, setRegion] = useState('');
  const [sourceUrl, setSourceUrl] = useState('');

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
      setError('Укажите название акта');
      return;
    }
    setSubmitting(true);
    try {
      const material = await materialsApi.createNpa({
        title,
        summary: summary || null,
        content,
        category_id: categoryId,
        status,
        act_kind: actKind,
        level: level || null,
        act_status: actStatus || null,
        document_number: documentNumber.trim() || null,
        adoption_date: adoptionDate || null,
        effective_date: effectiveDate || null,
        revision_date: revisionDate || null,
        issuing_authority: issuingAuthority.trim() || null,
        region: region.trim() || null,
        official_source_url: sourceUrl.trim() || null,
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

      <p className="rounded-md bg-blue-50 p-2 text-xs text-blue-700">
        НПА рассчитан на неопределённый круг лиц и многократное применение. Индивидуальные документы
        (приказ о приёме конкретного сотрудника, постановление о штрафе) сюда не относятся.
      </p>

      <div className="grid gap-3 md:grid-cols-2">
        <div>
          <label className="label" htmlFor="npa-title">
            Название акта
          </label>
          <input id="npa-title" className="input" value={title} onChange={(e) => setTitle(e.target.value)} required />
        </div>
        <div>
          <label className="label" htmlFor="npa-category">
            Категория
          </label>
          <select
            id="npa-category"
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
        <label className="label" htmlFor="npa-summary">
          Краткая суть
        </label>
        <input id="npa-summary" className="input" value={summary} onChange={(e) => setSummary(e.target.value)} />
      </div>

      <div className="grid gap-3 md:grid-cols-2">
        <div>
          <label className="label" htmlFor="npa-kind">
            Вид акта
          </label>
          <select
            id="npa-kind"
            className="input"
            value={actKind}
            onChange={(e) => setActKind(e.target.value as NpaActKind)}
          >
            {(Object.keys(npaActKindLabels) as NpaActKind[]).map((k) => (
              <option key={k} value={k}>
                {npaActKindLabels[k]}
              </option>
            ))}
          </select>
        </div>
        <div>
          <label className="label" htmlFor="npa-level">
            Уровень
          </label>
          <select id="npa-level" className="input" value={level} onChange={(e) => setLevel(e.target.value as NpaLevel | '')}>
            <option value="">Не указан</option>
            {(Object.keys(npaLevelLabels) as NpaLevel[]).map((l) => (
              <option key={l} value={l}>
                {npaLevelLabels[l]}
              </option>
            ))}
          </select>
        </div>
      </div>

      <div className="grid gap-3 md:grid-cols-2">
        <div>
          <label className="label" htmlFor="npa-number">
            Номер документа
          </label>
          <input
            id="npa-number"
            className="input"
            placeholder="426-ФЗ, 2464, 772н"
            value={documentNumber}
            onChange={(e) => setDocumentNumber(e.target.value)}
          />
        </div>
        <div>
          <label className="label" htmlFor="npa-status">
            Статус действия
          </label>
          <select
            id="npa-status"
            className="input"
            value={actStatus}
            onChange={(e) => setActStatus(e.target.value as NpaStatus | '')}
          >
            <option value="">Не указан</option>
            {(Object.keys(npaStatusLabels) as NpaStatus[]).map((s) => (
              <option key={s} value={s}>
                {npaStatusLabels[s]}
              </option>
            ))}
          </select>
        </div>
      </div>

      <div className="grid gap-3 md:grid-cols-3">
        <div>
          <label className="label" htmlFor="npa-adopted">
            Дата принятия
          </label>
          <input
            id="npa-adopted"
            type="date"
            className="input"
            value={adoptionDate}
            onChange={(e) => setAdoptionDate(e.target.value)}
          />
        </div>
        <div>
          <label className="label" htmlFor="npa-effective">
            Вступление в силу
          </label>
          <input
            id="npa-effective"
            type="date"
            className="input"
            value={effectiveDate}
            onChange={(e) => setEffectiveDate(e.target.value)}
          />
        </div>
        <div>
          <label className="label" htmlFor="npa-revision">
            Последняя редакция
          </label>
          <input
            id="npa-revision"
            type="date"
            className="input"
            value={revisionDate}
            onChange={(e) => setRevisionDate(e.target.value)}
          />
        </div>
      </div>

      <div className="grid gap-3 md:grid-cols-2">
        <div>
          <label className="label" htmlFor="npa-authority">
            Орган, принявший акт
          </label>
          <input
            id="npa-authority"
            className="input"
            placeholder="Минтруд России, Правительство РФ"
            value={issuingAuthority}
            onChange={(e) => setIssuingAuthority(e.target.value)}
          />
        </div>
        <div>
          <label className="label" htmlFor="npa-region">
            Регион/юрисдикция
          </label>
          <input
            id="npa-region"
            className="input"
            placeholder="для региональных/муниципальных"
            value={region}
            onChange={(e) => setRegion(e.target.value)}
          />
        </div>
      </div>

      <div>
        <label className="label" htmlFor="npa-source">
          Ссылка на официальную публикацию
        </label>
        <input
          id="npa-source"
          className="input"
          placeholder="https://..."
          value={sourceUrl}
          onChange={(e) => setSourceUrl(e.target.value)}
        />
      </div>

      <div>
        <label className="label" htmlFor="npa-content">
          Комментарий/применение в ОТ (необязательно)
        </label>
        <ContentEditor id="npa-content" value={content} onChange={setContent} />
      </div>

      <div>
        <span className="label">Файл акта</span>
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
