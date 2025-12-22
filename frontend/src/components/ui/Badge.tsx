import { HTMLAttributes } from 'react';
import { cva, type VariantProps } from 'class-variance-authority';
import { cn } from '@/lib/utils';

const badgeVariants = cva(
  'inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium transition-colors',
  {
    variants: {
      variant: {
        default: 'bg-cif-primary-light text-cif-primary',
        secondary: 'bg-surface-muted text-content-secondary',
        success: 'bg-status-success-bg text-status-success border border-status-success-border',
        warning: 'bg-status-warning-bg text-status-warning border border-status-warning-border',
        error: 'bg-status-error-bg text-status-error border border-status-error-border',
        info: 'bg-status-info-bg text-status-info border border-status-info-border',
        outline: 'border border-edge-default text-content-secondary',
        accent: 'bg-cif-accent/10 text-cif-accent',
      },
    },
    defaultVariants: {
      variant: 'default',
    },
  }
);

export interface BadgeProps
  extends HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof badgeVariants> {}

function Badge({ className, variant, ...props }: BadgeProps) {
  return <div className={cn(badgeVariants({ variant }), className)} {...props} />;
}

export { Badge, badgeVariants };
