import { useState } from 'react';
import * as Dialog from '@radix-ui/react-dialog';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { ScrollText, Search, X } from 'lucide-react';

import * as materialsApi from '@/api/materials';
import { getErrorMessage } from '@/api/client';
import { npaActKindLabels, npaLevelLabels, npaStatusLabels } from '@/utils/npaLabels';
import type { NpaActKind, NpaDetail, NpaLevel, NpaStatus } from '@/types';

/** Кнопка «Редактировать реквизиты» + модалка правки полей НПА и ссылки-замены. */
export function NpaEditDialog({ materialId, npa }: { materialId: string; npa: NpaDetail }) {
  const [open, setOpen] = useState(false);
  const [actKind, setActKind] = useState<NpaActKind>(npa.act_kind);
  const [level, setLevel] = useState<NpaLevel | ''>(npa.level ?? '');
  const [actStatus, setActStatus] = useState<NpaStatus | ''>(npa.act_status ?? '');
  const [documentNumber, setDocumentNumber] = useState(npa.document_number ?? '');
  const [adoptionDate, setAdoptionDate] = useState(npa.adoption_date ?? '');
  const [effectiveDate, setEffectiveDate] = useState(npa.effective_date ?? '');
  const [revisionDate, setRevisionDate] = useState(npa.revision_date ?? '');
  const [issuingAuthority, setIssuingAuthority] = useState(npa.issuing_authority ?? '');
  const [region, setRegion] = useState(npa.region ?? '');
  const [sourceUrl, setSourceUrl] = useState(npa.official_source_url ?? '');
  const [replacedById, setReplacedById] = useState<string | null>(npa.replaced_by_id ?? null);
  const [replacedByTitle, setReplacedByTitle] = useState<string | null>(npa.replaced_by?.title ?? null);
  const [pickerQuery, setPickerQuery] = useState('');
  const [error, setError] = useState<string | null>(null);

  const queryClient = useQueryClient();

  const reset = () => {
    setActKind(npa.act_kind);
    setLevel(npa.level ?? '');
    setActStatus(npa.act_status ?? '');
    setDocumentNumber(npa.document_number ?? '');
    setAdoptionDate(npa.adoption_date ?? '');
    setEffectiveDate(npa.effective_date ?? '');
    setRevisionDate(npa.revision_date ?? '');
    setIssuingAuthority(npa.issuing_authority ?? '');
    setRegion(npa.region ?? '');
    setSourceUrl(npa.official_source_url ?? '');
    setReplacedById(npa.replaced_by_id ?? null);
    setReplacedByTitle(npa.replaced_by?.title ?? null);
    setPickerQuery('');
    setError(null);
  };

  const { data: pickerResults } = useQuery({
    queryKey: ['npa-picker', pickerQuery],
    queryFn: () => materialsApi.searchMaterials({ query: pickerQuery, type: 'npa', page_size: 8 }),
    enabled: open && pickerQuery.trim().length >= 2,
  });

  const save = useMutation({
    mutationFn: () =>
      materialsApi.updateNpa(materialId, {
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
        replaced_by_id: replacedById,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['material', materialId] });
      setOpen(false);
    },
    onError: (e) => setError(getErrorMessage(e)),
  });

  const candidates = (pickerResults?.items ?? []).filter((m) => m.id !== materialId);

  return (
    <Dialog.Root
      open={open}
      onOpenChange={(o) => {
        setOpen(o);
        if (o) reset();
      }}
    >
      <Dialog.Trigger asChild>
        <button
          type="button"
          title="Редактировать реквизиты НПА"
          aria-label="Редактировать реквизиты НПА"
          className="rounded p-1.5 text-gray-500 transition hover:bg-gray-100 hover:text-gray-700"
        >
          <ScrollText size={16} />
        </button>
      </Dialog.Trigger>

      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 z-[60] bg-black/40" />
        <Dialog.Content className="fixed left-1/2 top-1/2 z-[70] flex max-h-[85vh] w-[calc(100vw-2rem)] max-w-2xl -translate-x-1/2 -translate-y-1/2 flex-col overflow-hidden rounded-2xl bg-white shadow-2xl focus:outline-none">
          <div className="flex items-center justify-between border-b px-5 py-4">
            <Dialog.Title className="text-lg font-semibold text-gray-900">Реквизиты НПА</Dialog.Title>
            <Dialog.Close asChild>
              <button
                type="button"
                aria-label="Закрыть"
                className="rounded p-1 text-gray-500 transition hover:bg-gray-100 hover:text-gray-700"
              >
                <X size={18} />
              </button>
            </Dialog.Close>
          </div>

          <form
            className="space-y-3 overflow-y-auto px-5 py-4"
            onSubmit={(e) => {
              e.preventDefault();
              save.mutate();
            }}
          >
            {error && <div className="rounded-md bg-red-50 p-3 text-sm text-red-600">{error}</div>}

            <div className="grid gap-3 md:grid-cols-2">
              <div>
                <label className="label" htmlFor="npae-kind">
                  Вид акта
                </label>
                <select
                  id="npae-kind"
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
                <label className="label" htmlFor="npae-level">
                  Уровень
                </label>
                <select
                  id="npae-level"
                  className="input"
                  value={level}
                  onChange={(e) => setLevel(e.target.value as NpaLevel | '')}
                >
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
                <label className="label" htmlFor="npae-number">
                  Номер документа
                </label>
                <input
                  id="npae-number"
                  className="input"
                  value={documentNumber}
                  onChange={(e) => setDocumentNumber(e.target.value)}
                />
              </div>
              <div>
                <label className="label" htmlFor="npae-status">
                  Статус действия
                </label>
                <select
                  id="npae-status"
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
                <label className="label" htmlFor="npae-adopted">
                  Дата принятия
                </label>
                <input
                  id="npae-adopted"
                  type="date"
                  className="input"
                  value={adoptionDate}
                  onChange={(e) => setAdoptionDate(e.target.value)}
                />
              </div>
              <div>
                <label className="label" htmlFor="npae-effective">
                  Вступление в силу
                </label>
                <input
                  id="npae-effective"
                  type="date"
                  className="input"
                  value={effectiveDate}
                  onChange={(e) => setEffectiveDate(e.target.value)}
                />
              </div>
              <div>
                <label className="label" htmlFor="npae-revision">
                  Последняя редакция
                </label>
                <input
                  id="npae-revision"
                  type="date"
                  className="input"
                  value={revisionDate}
                  onChange={(e) => setRevisionDate(e.target.value)}
                />
              </div>
            </div>

            <div className="grid gap-3 md:grid-cols-2">
              <div>
                <label className="label" htmlFor="npae-authority">
                  Орган, принявший акт
                </label>
                <input
                  id="npae-authority"
                  className="input"
                  value={issuingAuthority}
                  onChange={(e) => setIssuingAuthority(e.target.value)}
                />
              </div>
              <div>
                <label className="label" htmlFor="npae-region">
                  Регион/юрисдикция
                </label>
                <input
                  id="npae-region"
                  className="input"
                  value={region}
                  onChange={(e) => setRegion(e.target.value)}
                />
              </div>
            </div>

            <div>
              <label className="label" htmlFor="npae-source">
                Ссылка на официальную публикацию
              </label>
              <input
                id="npae-source"
                className="input"
                placeholder="https://..."
                value={sourceUrl}
                onChange={(e) => setSourceUrl(e.target.value)}
              />
            </div>

            {/* Документ-замена (когда акт утратил силу). */}
            <div className="rounded-lg border border-gray-200 bg-gray-50 p-3">
              <span className="label">Пришёл на смену (документ-замена)</span>
              {replacedById ? (
                <div className="flex items-center justify-between gap-2 rounded-md border border-gray-200 bg-white px-3 py-2 text-sm">
                  <span className="min-w-0 flex-1 truncate" title={replacedByTitle ?? undefined}>
                    {replacedByTitle ?? 'Выбранный документ'}
                  </span>
                  <button
                    type="button"
                    className="text-gray-400 hover:text-red-600"
                    onClick={() => {
                      setReplacedById(null);
                      setReplacedByTitle(null);
                    }}
                  >
                    <X className="h-4 w-4" />
                  </button>
                </div>
              ) : (
                <>
                  <div className="relative">
                    <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400" />
                    <input
                      className="input pl-9"
                      placeholder="Найти НПА для замены…"
                      value={pickerQuery}
                      onChange={(e) => setPickerQuery(e.target.value)}
                    />
                  </div>
                  {candidates.length > 0 && (
                    <ul className="mt-1 max-h-40 overflow-y-auto rounded-md border border-gray-200 bg-white text-sm">
                      {candidates.map((m) => (
                        <li key={m.id}>
                          <button
                            type="button"
                            className="block w-full truncate px-3 py-2 text-left hover:bg-gray-50"
                            onClick={() => {
                              setReplacedById(m.id);
                              setReplacedByTitle(m.title);
                              setPickerQuery('');
                            }}
                          >
                            {m.title}
                          </button>
                        </li>
                      ))}
                    </ul>
                  )}
                </>
              )}
            </div>

            <div className="flex justify-end gap-2 pt-1">
              <Dialog.Close asChild>
                <button type="button" className="btn-secondary" disabled={save.isPending}>
                  Отмена
                </button>
              </Dialog.Close>
              <button type="submit" className="btn-primary" disabled={save.isPending}>
                {save.isPending ? 'Сохранение...' : 'Сохранить'}
              </button>
            </div>
          </form>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}
