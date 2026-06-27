import { useState } from 'react';
import * as Dialog from '@radix-ui/react-dialog';
import { Plus, X } from 'lucide-react';

import { ChecklistBuilderForm } from '@/components/checklists/ChecklistBuilderForm';

type CheckKind = 'run' | 'checklist';

const kinds: { value: CheckKind; label: string }[] = [
  { value: 'run', label: 'Проверка' },
  { value: 'checklist', label: 'Чек-лист' },
];

/** Кнопка «Создать проверку/чек-лист» + модалка с переключателем типа. */
export function CreateCheckDialog() {
  const [open, setOpen] = useState(false);
  const [kind, setKind] = useState<CheckKind>('checklist');

  return (
    <Dialog.Root
      open={open}
      onOpenChange={(o) => {
        setOpen(o);
        if (o) setKind('checklist');
      }}
    >
      <Dialog.Trigger asChild>
        <button type="button" className="btn-primary flex items-center gap-2">
          <Plus size={18} /> Создать проверку/чек-лист
        </button>
      </Dialog.Trigger>

      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 z-[60] bg-black/40" />
        <Dialog.Content className="fixed left-1/2 top-1/2 z-[70] flex max-h-[85vh] w-[calc(100vw-2rem)] max-w-3xl -translate-x-1/2 -translate-y-1/2 flex-col overflow-hidden rounded-2xl bg-white shadow-2xl focus:outline-none">
          <div className="flex items-center justify-between border-b px-5 py-4">
            <Dialog.Title className="text-lg font-semibold text-gray-900">Создать</Dialog.Title>
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

          {/* Переключатель типа: Проверка | Чек-лист (на всю ширину) */}
          <div className="px-5 pt-4">
            <div className="flex rounded-lg border border-gray-200 bg-gray-50 p-0.5">
              {kinds.map((k) => (
                <button
                  key={k.value}
                  type="button"
                  onClick={() => setKind(k.value)}
                  className={`flex-1 rounded-md px-4 py-1.5 text-sm font-medium transition-colors ${
                    kind === k.value ? 'bg-white text-primary-700 shadow-sm' : 'text-gray-600 hover:text-gray-900'
                  }`}
                >
                  {k.label}
                </button>
              ))}
            </div>
          </div>

          {kind === 'checklist' ? (
            <ChecklistBuilderForm onSaved={() => setOpen(false)} />
          ) : (
            <div className="flex flex-col items-center gap-2 px-5 py-12 text-center">
              <span className="rounded-full bg-amber-100 px-3 py-1 text-sm font-medium text-amber-700">
                В разработке
              </span>
              <p className="text-sm text-gray-500">Создание проверки по чек-листу появится на следующем этапе.</p>
            </div>
          )}
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}
