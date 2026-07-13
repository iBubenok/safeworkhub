import { useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import * as Dialog from '@radix-ui/react-dialog';
import { X } from 'lucide-react';

import * as usersApi from '@/api/users';
import { handleActionError } from '@/api/errors';
import { toast } from '@/store/toastStore';

/**
 * Диалог установки нового пароля другому пользователю (админ).
 * Открыт, когда target != null.
 */
export function SetUserPasswordDialog({
  target,
  onClose,
}: {
  target: { id: string; name: string } | null;
  onClose: () => void;
}) {
  const [next, setNext] = useState('');
  const [confirm, setConfirm] = useState('');
  const [error, setError] = useState<string | null>(null);

  const save = useMutation({
    mutationFn: (id: string) => usersApi.setUserPassword(id, next),
    onSuccess: () => {
      toast.success('Пароль обновлён');
      onClose();
    },
    onError: (e) => handleActionError(e),
  });

  const submit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!target) return;
    setError(null);
    if (next.length < 8) {
      setError('Пароль должен быть не короче 8 символов');
      return;
    }
    if (next !== confirm) {
      setError('Пароль и подтверждение не совпадают');
      return;
    }
    save.mutate(target.id);
  };

  return (
    <Dialog.Root
      open={target !== null}
      onOpenChange={(v) => {
        if (!v) {
          setNext('');
          setConfirm('');
          setError(null);
          onClose();
        }
      }}
    >
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 z-[60] bg-black/40" />
        <Dialog.Content className="fixed left-1/2 top-1/2 z-[70] flex w-[calc(100vw-2rem)] max-w-md -translate-x-1/2 -translate-y-1/2 flex-col overflow-hidden rounded-2xl bg-white shadow-2xl focus:outline-none">
          <div className="flex items-center justify-between border-b px-5 py-4">
            <Dialog.Title className="text-lg font-semibold text-gray-900">
              Смена пароля{target ? `: ${target.name}` : ''}
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

          <form className="space-y-3 px-5 py-4" onSubmit={submit}>
            {error && <div className="rounded-md bg-red-50 p-3 text-sm text-red-600">{error}</div>}
            <p className="text-xs text-gray-500">
              После смены пароля пользователю потребуется войти заново.
            </p>
            <div>
              <label className="label" htmlFor="set-new-pass">
                Новый пароль
              </label>
              <input
                id="set-new-pass"
                type="password"
                className="input"
                value={next}
                onChange={(e) => setNext(e.target.value)}
                minLength={8}
                autoComplete="new-password"
                required
              />
            </div>
            <div>
              <label className="label" htmlFor="set-confirm-pass">
                Повторите пароль
              </label>
              <input
                id="set-confirm-pass"
                type="password"
                className="input"
                value={confirm}
                onChange={(e) => setConfirm(e.target.value)}
                minLength={8}
                autoComplete="new-password"
                required
              />
            </div>
            <div className="flex justify-end gap-2 pt-1">
              <Dialog.Close asChild>
                <button type="button" className="btn-secondary">
                  Отмена
                </button>
              </Dialog.Close>
              <button type="submit" className="btn-primary" disabled={save.isPending}>
                {save.isPending ? 'Сохранение…' : 'Сменить пароль'}
              </button>
            </div>
          </form>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}
