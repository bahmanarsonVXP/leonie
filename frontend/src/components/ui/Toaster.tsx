import { useEffect, useState } from 'react';
import * as ToastPrimitive from '@radix-ui/react-toast';
import { X, CheckCircle, AlertCircle, Info, AlertTriangle } from 'lucide-react';
import { cn } from '@/lib/utils';

export interface Toast {
  id: string;
  type: 'success' | 'error' | 'info' | 'warning';
  title: string;
  description?: string;
  duration?: number;
}

interface ToasterState {
  toasts: Toast[];
  addToast: (toast: Omit<Toast, 'id'>) => void;
  removeToast: (id: string) => void;
}

const toasterState: ToasterState = {
  toasts: [],
  addToast: () => {},
  removeToast: () => {},
};

const listeners = new Set<() => void>();

function subscribe(listener: () => void) {
  listeners.add(listener);
  return () => {
    listeners.delete(listener);
  };
}

function notify() {
  listeners.forEach((listener) => listener());
}

export function toast(options: Omit<Toast, 'id'>) {
  const id = crypto.randomUUID();
  toasterState.toasts = [...toasterState.toasts, { ...options, id }];
  notify();

  const duration = options.duration ?? 5000;
  setTimeout(() => {
    toasterState.toasts = toasterState.toasts.filter((t) => t.id !== id);
    notify();
  }, duration);
}

export function Toaster() {
  const [toasts, setToasts] = useState<Toast[]>([]);

  useEffect(() => {
    return subscribe(() => {
      setToasts([...toasterState.toasts]);
    });
  }, []);

  const icons = {
    success: <CheckCircle className="h-5 w-5 text-success-600" />,
    error: <AlertCircle className="h-5 w-5 text-error-600" />,
    info: <Info className="h-5 w-5 text-primary-600" />,
    warning: <AlertTriangle className="h-5 w-5 text-warning-600" />,
  };

  const backgrounds = {
    success: 'border-success-200 bg-success-50',
    error: 'border-error-200 bg-error-50',
    info: 'border-primary-200 bg-primary-50',
    warning: 'border-warning-200 bg-warning-50',
  };

  return (
    <ToastPrimitive.Provider swipeDirection="right">
      {toasts.map((t) => (
        <ToastPrimitive.Root
          key={t.id}
          className={cn(
            'group pointer-events-auto relative flex w-full items-start gap-3 overflow-hidden rounded-lg border p-4 shadow-lg transition-all',
            'data-[swipe=cancel]:translate-x-0 data-[swipe=end]:translate-x-[var(--radix-toast-swipe-end-x)] data-[swipe=move]:translate-x-[var(--radix-toast-swipe-move-x)] data-[swipe=move]:transition-none',
            'data-[state=open]:animate-slide-up data-[state=closed]:animate-fade-out',
            backgrounds[t.type]
          )}
        >
          {icons[t.type]}
          <div className="flex-1">
            <ToastPrimitive.Title className="text-sm font-semibold text-neutral-900">
              {t.title}
            </ToastPrimitive.Title>
            {t.description && (
              <ToastPrimitive.Description className="mt-1 text-sm text-neutral-600">
                {t.description}
              </ToastPrimitive.Description>
            )}
          </div>
          <ToastPrimitive.Close className="rounded-md p-1 text-neutral-400 hover:bg-neutral-100 hover:text-neutral-600">
            <X className="h-4 w-4" />
          </ToastPrimitive.Close>
        </ToastPrimitive.Root>
      ))}
      <ToastPrimitive.Viewport className="fixed bottom-0 right-0 z-[100] flex max-h-screen w-full flex-col-reverse gap-2 p-4 sm:max-w-[420px]" />
    </ToastPrimitive.Provider>
  );
}
