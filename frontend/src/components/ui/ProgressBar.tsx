import { forwardRef } from 'react';
import * as ProgressPrimitive from '@radix-ui/react-progress';
import { cn } from '@/lib/utils';

interface ProgressBarProps extends React.ComponentPropsWithoutRef<typeof ProgressPrimitive.Root> {
  value?: number;
  variant?: 'default' | 'success' | 'warning' | 'error' | 'accent';
  size?: 'sm' | 'md' | 'lg';
  showLabel?: boolean;
}

const variantStyles = {
  default: 'bg-cif-primary',
  success: 'bg-status-success',
  warning: 'bg-status-warning',
  error: 'bg-status-error',
  accent: 'bg-cif-accent',
};

const sizeStyles = {
  sm: 'h-1',
  md: 'h-2',
  lg: 'h-3',
};

const ProgressBar = forwardRef<
  React.ElementRef<typeof ProgressPrimitive.Root>,
  ProgressBarProps
>(({ className, value = 0, variant = 'default', size = 'md', showLabel = false, ...props }, ref) => (
  <div className="w-full">
    {showLabel && (
      <div className="mb-1 flex justify-between text-sm">
        <span className="text-content-secondary">Progression</span>
        <span className="font-medium text-content-primary">{Math.round(value)}%</span>
      </div>
    )}
    <ProgressPrimitive.Root
      ref={ref}
      className={cn(
        'relative w-full overflow-hidden rounded-full bg-surface-muted',
        sizeStyles[size],
        className
      )}
      {...props}
    >
      <ProgressPrimitive.Indicator
        className={cn(
          'h-full transition-all duration-300 ease-out rounded-full',
          variantStyles[variant]
        )}
        style={{ width: `${value}%` }}
      />
    </ProgressPrimitive.Root>
  </div>
));
ProgressBar.displayName = 'ProgressBar';

export { ProgressBar };
