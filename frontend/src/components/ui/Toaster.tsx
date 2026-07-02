import * as Toast from '@radix-ui/react-toast';
import { CheckCircle2, Info, X, XCircle } from 'lucide-react';

import { useToastStore, type ToastVariant } from '@/store/toastStore';

const variantConfig: Record<ToastVariant, { icon: typeof Info; accent: string }> = {
  error: { icon: XCircle, accent: 'text-red-500' },
  success: { icon: CheckCircle2, accent: 'text-green-500' },
  info: { icon: Info, accent: 'text-primary-500' },
};

/** Глобальный контейнер тостов. Монтируется один раз в App. */
export function Toaster() {
  const toasts = useToastStore((state) => state.toasts);
  const dismiss = useToastStore((state) => state.dismiss);

  return (
    <Toast.Provider swipeDirection="right" duration={5000}>
      {toasts.map((item) => {
        const { icon: Icon, accent } = variantConfig[item.variant];
        return (
          <Toast.Root
            key={item.id}
            open
            onOpenChange={(open) => {
              if (!open) dismiss(item.id);
            }}
            className="flex items-start gap-3 rounded-lg border border-gray-200 bg-white p-3 shadow-lg data-[state=closed]:animate-out data-[state=closed]:fade-out data-[swipe=end]:animate-out"
          >
            <Icon className={`mt-0.5 h-5 w-5 shrink-0 ${accent}`} />
            <div className="min-w-0 flex-1">
              {item.title && <Toast.Title className="text-sm font-semibold text-gray-900">{item.title}</Toast.Title>}
              <Toast.Description className="text-sm text-gray-600">{item.message}</Toast.Description>
            </div>
            <Toast.Close
              aria-label="Закрыть"
              className="rounded p-0.5 text-gray-400 transition hover:bg-gray-100 hover:text-gray-600"
            >
              <X className="h-4 w-4" />
            </Toast.Close>
          </Toast.Root>
        );
      })}
      <Toast.Viewport className="fixed bottom-0 right-0 z-[100] m-4 flex w-96 max-w-[calc(100vw-2rem)] flex-col gap-2 outline-none" />
    </Toast.Provider>
  );
}
