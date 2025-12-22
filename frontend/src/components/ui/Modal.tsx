import { ReactNode } from 'react';
import * as DialogPrimitive from '@radix-ui/react-dialog';
import { X } from 'lucide-react';
import { cn } from '@/lib/utils';

interface ModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  children: ReactNode;
}

export function Modal({ open, onOpenChange, children }: ModalProps) {
  return (
    <DialogPrimitive.Root open={open} onOpenChange={onOpenChange}>
      {children}
    </DialogPrimitive.Root>
  );
}

export function ModalTrigger({ children, className }: { children: ReactNode; className?: string }) {
  return (
    <DialogPrimitive.Trigger className={className}>{children}</DialogPrimitive.Trigger>
  );
}

export function ModalContent({
  children,
  className,
  title,
  description,
}: {
  children: ReactNode;
  className?: string;
  title?: string;
  description?: string;
}) {
  return (
    <DialogPrimitive.Portal>
      <DialogPrimitive.Overlay className="fixed inset-0 z-50 bg-cif-darker/60 backdrop-blur-sm data-[state=open]:animate-fade-in" />
      <DialogPrimitive.Content
        className={cn(
          'fixed left-1/2 top-1/2 z-50 max-h-[85vh] w-full max-w-lg -translate-x-1/2 -translate-y-1/2 overflow-y-auto',
          'rounded-cif-xl bg-surface-card p-6 shadow-cif-lg focus:outline-none data-[state=open]:animate-scale-in',
          'border border-edge-default',
          className
        )}
      >
        {title && (
          <DialogPrimitive.Title className="text-lg font-semibold text-content-primary">
            {title}
          </DialogPrimitive.Title>
        )}
        {description && (
          <DialogPrimitive.Description className="mt-2 text-sm text-content-secondary">
            {description}
          </DialogPrimitive.Description>
        )}
        {children}
        <DialogPrimitive.Close className="absolute right-4 top-4 rounded-cif p-1.5 text-content-muted hover:bg-surface-muted hover:text-content-primary transition-colors">
          <X className="h-5 w-5" />
        </DialogPrimitive.Close>
      </DialogPrimitive.Content>
    </DialogPrimitive.Portal>
  );
}

export function ModalClose({ children, className }: { children: ReactNode; className?: string }) {
  return <DialogPrimitive.Close className={className}>{children}</DialogPrimitive.Close>;
}
