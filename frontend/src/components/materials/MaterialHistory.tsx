import { useState } from 'react';
import * as Dialog from '@radix-ui/react-dialog';
import { useQuery } from '@tanstack/react-query';
import { History, X } from 'lucide-react';

import * as materialsApi from '@/api/materials';
import { lineDiff, wordDiff, type DiffSegment } from '@/utils/diffText';

function Segments({ segments }: { segments: DiffSegment[] }) {
  return (
    <>
      {segments.map((seg, i) => {
        if (seg.added) {
          return (
            <span key={i} className="rounded bg-green-100 text-green-800">
              {seg.value}
            </span>
          );
        }
        if (seg.removed) {
          return (
            <span key={i} className="rounded bg-red-100 text-red-700 line-through">
              {seg.value}
            </span>
          );
        }
        return <span key={i}>{seg.value}</span>;
      })}
    </>
  );
}

function formatDateTime(iso: string): string {
  return new Date(iso).toLocaleString('ru-RU', { dateStyle: 'short', timeStyle: 'short' });
}

/** Кнопка «История» + модалка с таймлайном версий и diff. */
export function MaterialHistory({ materialId }: { materialId: string }) {
  const [open, setOpen] = useState(false);
  const [selected, setSelected] = useState(0);

  const { data: versions, isLoading } = useQuery({
    queryKey: ['material-versions', materialId],
    queryFn: () => materialsApi.getMaterialVersions(materialId),
    enabled: open,
  });

  const list = versions ?? [];
  const current = list[selected];
  const previous = list[selected + 1]; // список по убыванию version_no — предыдущая идёт ниже

  return (
    <Dialog.Root
      open={open}
      onOpenChange={(o) => {
        setOpen(o);
        if (o) setSelected(0);
      }}
    >
      <Dialog.Trigger asChild>
        <button
          type="button"
          title="История изменений"
          aria-label="История изменений"
          className="rounded p-1.5 text-gray-500 transition hover:bg-gray-100 hover:text-gray-700"
        >
          <History size={16} />
        </button>
      </Dialog.Trigger>

      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 z-[60] bg-black/40" />
        <Dialog.Content className="fixed left-1/2 top-1/2 z-[70] flex h-[85vh] w-[calc(100vw-2rem)] max-w-4xl -translate-x-1/2 -translate-y-1/2 flex-col overflow-hidden rounded-2xl bg-white shadow-2xl focus:outline-none">
          <div className="flex items-center justify-between border-b px-5 py-4">
            <Dialog.Title className="text-lg font-semibold text-gray-900">История изменений</Dialog.Title>
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

          {isLoading ? (
            <div className="flex-1 p-5 text-sm text-gray-500">Загрузка…</div>
          ) : list.length === 0 ? (
            <div className="flex-1 p-5 text-sm text-gray-500">История пуста</div>
          ) : (
            <div className="flex min-h-0 flex-1">
              <nav className="w-56 shrink-0 overflow-y-auto border-r p-3">
                <ol className="space-y-1">
                  {list.map((v, i) => (
                    <li key={v.id}>
                      <button
                        type="button"
                        onClick={() => setSelected(i)}
                        className={`flex w-full gap-2 rounded-md px-2 py-2 text-left text-xs ${
                          i === selected ? 'bg-primary-50' : 'hover:bg-gray-50'
                        }`}
                      >
                        <span className="mt-1 flex flex-col items-center self-stretch">
                          <span
                            className={`h-2.5 w-2.5 shrink-0 rounded-full ${
                              i === selected ? 'bg-primary-600' : 'bg-gray-300'
                            }`}
                          />
                          {i < list.length - 1 && <span className="mt-0.5 w-px flex-1 bg-gray-200" />}
                        </span>
                        <span className="min-w-0">
                          <span className="font-medium text-gray-900">
                            Версия {v.version_no}
                            {i === 0 ? ' (текущая)' : ''}
                          </span>
                          <span className="block text-gray-500">{formatDateTime(v.created_at)}</span>
                          {v.editor_name && <span className="block truncate text-gray-500">{v.editor_name}</span>}
                          {v.change_note && (
                            <span className="block truncate text-gray-400" title={v.change_note}>
                              {v.change_note}
                            </span>
                          )}
                        </span>
                      </button>
                    </li>
                  ))}
                </ol>
              </nav>

              <div className="min-w-0 flex-1 overflow-y-auto p-5 text-sm">
                {current && (
                  <>
                    {!previous && (
                      <p className="mb-3 rounded-md bg-gray-50 p-2 text-xs text-gray-500">
                        Первая версия — содержимое показано как добавленное.
                      </p>
                    )}
                    <div className="mb-4">
                      <h3 className="mb-1 text-xs font-semibold uppercase tracking-wide text-gray-400">Заголовок</h3>
                      <p className="whitespace-pre-wrap break-words">
                        <Segments segments={wordDiff(previous?.snapshot.title, current.snapshot.title)} />
                      </p>
                    </div>
                    <div className="mb-4">
                      <h3 className="mb-1 text-xs font-semibold uppercase tracking-wide text-gray-400">
                        Краткое описание
                      </h3>
                      <p className="whitespace-pre-wrap break-words">
                        <Segments segments={wordDiff(previous?.snapshot.summary, current.snapshot.summary)} />
                      </p>
                    </div>
                    <div>
                      <h3 className="mb-1 text-xs font-semibold uppercase tracking-wide text-gray-400">Текст</h3>
                      <pre className="whitespace-pre-wrap break-words font-sans">
                        <Segments segments={lineDiff(previous?.snapshot.content, current.snapshot.content)} />
                      </pre>
                    </div>
                  </>
                )}
              </div>
            </div>
          )}
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}
