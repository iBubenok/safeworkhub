import { useEffect, useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import * as Dialog from '@radix-ui/react-dialog';
import { X } from 'lucide-react';

import * as runsApi from '@/api/checklistRuns';
import { handleActionError } from '@/api/errors';
import { AssigneePicker } from '@/components/checklists/AssigneePicker';
import { usePermissions } from '@/hooks/usePermissions';
import type { RunAssignee } from '@/types';

/**
 * Диалог изменения состава назначенных на уже начатую проверку.
 * Доступен создателю проверки или владельцу организации.
 */
export function EditAssigneesDialog({
  runId,
  creatorId,
  current,
  open,
  onOpenChange,
  onSaved,
}: {
  runId: string;
  creatorId: string;
  current: RunAssignee[];
  open: boolean;
  onOpenChange: (value: boolean) => void;
  onSaved: () => void;
}) {
  const { user } = usePermissions();
  const [assigneeIds, setAssigneeIds] = useState<string[]>([]);

  useEffect(() => {
    if (open) {
      setAssigneeIds(current.map((a) => a.id));
    }
  }, [open, current]);

  const save = useMutation({
    mutationFn: () => runsApi.setAssignees(runId, assigneeIds),
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
        <Dialog.Content className="fixed left-1/2 top-1/2 z-[70] flex max-h-[85vh] w-[calc(100vw-2rem)] max-w-md -translate-x-1/2 -translate-y-1/2 flex-col overflow-hidden rounded-2xl bg-white shadow-2xl focus:outline-none">
          <div className="flex items-center justify-between border-b px-5 py-4">
            <Dialog.Title className="text-lg font-semibold text-gray-900">Состав проверяющих</Dialog.Title>
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

          <div className="space-y-2 overflow-y-auto px-5 py-4">
            <p className="text-xs text-gray-500">
              Назначенные смогут заполнять и завершать проверку. Создатель остаётся проверяющим всегда.
            </p>
            <AssigneePicker
              selected={assigneeIds}
              onChange={setAssigneeIds}
              excludeIds={user ? [creatorId, user.id] : [creatorId]}
            />
          </div>

          <div className="flex justify-end gap-2 border-t px-5 py-4">
            <Dialog.Close asChild>
              <button type="button" className="btn-secondary">
                Отмена
              </button>
            </Dialog.Close>
            <button type="button" className="btn-primary" disabled={save.isPending} onClick={() => save.mutate()}>
              {save.isPending ? 'Сохранение…' : 'Сохранить'}
            </button>
          </div>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}
