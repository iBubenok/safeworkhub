import { useEffect, useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import * as Dialog from '@radix-ui/react-dialog';
import { X } from 'lucide-react';

import * as runsApi from '@/api/checklistRuns';
import { handleActionError } from '@/api/errors';

/** ISO (UTC) → значение для datetime-local в локальном времени. */
function toLocalInput(iso: string | null): string {
  if (!iso) return '';
  const d = new Date(iso);
  const pad = (n: number) => String(n).padStart(2, '0');
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`;
}

/** Диалог изменения срока проведения: продлить или снять. Управляется извне. */
export function EditDeadlineDialog({
  runId,
  currentDueAt,
  open,
  onOpenChange,
  onSaved,
}: {
  runId: string;
  currentDueAt: string | null;
  open: boolean;
  onOpenChange: (value: boolean) => void;
  onSaved: () => void;
}) {
  const [dueAt, setDueAt] = useState('');

  useEffect(() => {
    if (open) setDueAt(toLocalInput(currentDueAt));
  }, [open, currentDueAt]);

  const save = useMutation({
    mutationFn: (value: string | null) => runsApi.setDeadline(runId, value),
    onSuccess: () => {
      onOpenChange(false);
      onSaved();
    },
    onError: (e) => handleActionError(e),
  });

  return (
    <Dialog.Root open={open} onOpenChange={onOpenChange}>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 z-[60] bg-black/40" />
        <Dialog.Content className="fixed left-1/2 top-1/2 z-[70] flex w-[calc(100vw-2rem)] max-w-md -translate-x-1/2 -translate-y-1/2 flex-col overflow-hidden rounded-2xl bg-white shadow-2xl focus:outline-none">
          <div className="flex items-center justify-between border-b px-5 py-4">
            <Dialog.Title className="text-lg font-semibold text-gray-900">Срок проведения</Dialog.Title>
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

          <div className="space-y-2 px-5 py-4">
            <label className="label" htmlFor="deadline-input">
              Новый срок
            </label>
            <input
              id="deadline-input"
              type="datetime-local"
              className="input"
              value={dueAt}
              onChange={(e) => setDueAt(e.target.value)}
            />
            <p className="text-xs text-gray-500">Снимите срок, чтобы проводить проверку без ограничения по времени.</p>
          </div>

          <div className="flex justify-between gap-2 border-t px-5 py-4">
            <button
              type="button"
              className="btn-secondary"
              disabled={save.isPending}
              onClick={() => save.mutate(null)}
            >
              Без срока
            </button>
            <button
              type="button"
              className="btn-primary"
              disabled={save.isPending || !dueAt}
              onClick={() => save.mutate(new Date(dueAt).toISOString())}
            >
              {save.isPending ? 'Сохранение…' : 'Сохранить'}
            </button>
          </div>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}
