import { useState } from 'react';
import * as Dialog from '@radix-ui/react-dialog';
import { Plus, X } from 'lucide-react';

import { ChecklistBuilderForm } from '@/components/checklists/ChecklistBuilderForm';
import type { Checklist } from '@/types';

/**
 * Диалог конструктора чек-листа. Без `checklist` — создание, с ним — правка.
 * `trigger` переопределяет кнопку-открыватель (для страницы деталей).
 */
export function ChecklistBuilderDialog({
  checklist,
  trigger,
}: {
  checklist?: Checklist;
  trigger?: React.ReactNode;
}) {
  const [open, setOpen] = useState(false);

  return (
    <Dialog.Root open={open} onOpenChange={setOpen}>
      <Dialog.Trigger asChild>
        {trigger ?? (
          <button type="button" className="btn-primary flex items-center gap-2">
            <Plus size={18} /> Создать чек-лист
          </button>
        )}
      </Dialog.Trigger>

      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 z-[60] bg-black/40" />
        <Dialog.Content className="fixed left-1/2 top-1/2 z-[70] flex max-h-[85vh] w-[calc(100vw-2rem)] max-w-3xl -translate-x-1/2 -translate-y-1/2 flex-col overflow-hidden rounded-2xl bg-white shadow-2xl focus:outline-none">
          <div className="flex items-center justify-between border-b px-5 py-4">
            <Dialog.Title className="text-lg font-semibold text-gray-900">
              {checklist ? 'Редактировать чек-лист' : 'Новый чек-лист'}
            </Dialog.Title>
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

          {open && <ChecklistBuilderForm checklist={checklist} onSaved={() => setOpen(false)} />}
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}
