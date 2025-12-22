import { forwardRef, InputHTMLAttributes } from 'react';
import { cn } from '@/lib/utils';

export interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  error?: boolean;
}

const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ className, type, error, ...props }, ref) => {
    return (
      <input
        type={type}
        className={cn(
          'flex h-10 w-full rounded-cif border border-edge-default bg-white px-4 py-2.5 text-sm text-content-primary placeholder:text-content-muted',
          'focus:border-transparent focus:outline-none focus:ring-2 focus:ring-cif-primary',
          'disabled:cursor-not-allowed disabled:bg-surface-muted disabled:opacity-50',
          'transition-all duration-200',
          error && 'border-status-error focus:ring-status-error',
          className
        )}
        ref={ref}
        {...props}
      />
    );
  }
);
Input.displayName = 'Input';

export { Input };
