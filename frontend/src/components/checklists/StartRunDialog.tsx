import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useMutation } from '@tanstack/react-query';
import * as Dialog from '@radix-ui/react-dialog';
import { X } from 'lucide-react';

import * as runsApi from '@/api/checklistRuns';
import { handleActionError } from '@/api/errors';
import { AssigneePicker } from '@/components/checklists/AssigneePicker';
import { usePermissions } from '@/hooks/usePermissions';

/**
 * Диалог старта проверки по чек-листу: необязательное название + назначение сотрудников.
 * Управляется извне (open/onOpenChange), чтобы кнопку-триггер можно было разместить внутри
 * карточки-ссылки без конфликта обработчиков.
 */
export function StartRunDialog({
  checklistId,
  open,
  onOpenChange,
}: {
  checklistId: string;
  open: boolean;
  onOpenChange: (value: boolean) => void;
}) {
  const navigate = useNavigate();
  const { user } = usePermissions();
  const [title, setTitle] = useState('');
  const [assigneeIds, setAssigneeIds] = useState<string[]>([]);
  const [dueAt, setDueAt] = useState('');

  useEffect(() => {
    if (open) {
      setTitle('');
      setAssigneeIds([]);
      setDueAt('');
    }
  }, [open]);

  const startRun = useMutation({
    mutationFn: () =>
      runsApi.startRun({
        checklist_id: checklistId,
        title: title.trim() || null,
        due_at: dueAt ? new Date(dueAt).toISOString() : null,
        assignee_ids: assigneeIds,
      }),
    onSuccess: (run) => {
      onOpenChange(false);
      navigate(`/checks/runs/${run.id}`);
    },
    onError: (e) => handleActionError(e),
  });

  return (
    <Dialog.Root open={open} onOpenChange={onOpenChange}>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 z-[60] bg-black/40" />
        <Dialog.Content
          onClick={(e) => e.stopPropagation()}
          className="fixed left-1/2 top-1/2 z-[70] flex max-h-[85vh] w-[calc(100vw-2rem)] max-w-md -translate-x-1/2 -translate-y-1/2 flex-col overflow-hidden rounded-2xl bg-white shadow-2xl focus:outline-none"
        >
          <div className="flex items-center justify-between border-b px-5 py-4">
            <Dialog.Title className="text-lg font-semibold text-gray-900">Провести проверку</Dialog.Title>
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

          <div className="space-y-4 overflow-y-auto px-5 py-4">
            <div>
              <label className="label" htmlFor="run-title">
                Название проверки <span className="font-normal text-gray-400">(необязательно)</span>
              </label>
              <input
                id="run-title"
                className="input"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="Например: Цех №2, июль"
              />
            </div>
            <div>
              <p className="label">
                Назначить сотрудников <span className="font-normal text-gray-400">(необязательно)</span>
              </p>
              <p className="mb-2 text-xs text-gray-500">
                Назначенные смогут заполнять и завершать проверку наравне с вами.
              </p>
              <AssigneePicker
                selected={assigneeIds}
                onChange={setAssigneeIds}
                excludeIds={user ? [user.id] : []}
              />
            </div>
            <div>
              <label className="label" htmlFor="run-due">
                Срок проведения <span className="font-normal text-gray-400">(необязательно)</span>
              </label>
              <input
                id="run-due"
                type="datetime-local"
                className="input"
                value={dueAt}
                onChange={(e) => setDueAt(e.target.value)}
              />
              <p className="mt-1 text-xs text-gray-500">Оставьте пустым — проверка без срока.</p>
            </div>
          </div>

          <div className="flex justify-end gap-2 border-t px-5 py-4">
            <Dialog.Close asChild>
              <button type="button" className="btn-secondary">
                Отмена
              </button>
            </Dialog.Close>
            <button type="button" className="btn-primary" disabled={startRun.isPending} onClick={() => startRun.mutate()}>
              {startRun.isPending ? 'Запуск…' : 'Начать проверку'}
            </button>
          </div>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}
