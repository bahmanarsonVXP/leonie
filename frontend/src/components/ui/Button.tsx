import { forwardRef, ButtonHTMLAttributes } from 'react';
import { Slot } from '@radix-ui/react-slot';
import { cva, type VariantProps } from 'class-variance-authority';
import { cn } from '@/lib/utils';

const buttonVariants = cva(
  'inline-flex items-center justify-center whitespace-nowrap rounded-cif text-sm font-medium transition-all duration-200 ease-out focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-cif-primary focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 active:scale-[0.98]',
  {
    variants: {
      variant: {
        default: 'bg-cif-primary text-white hover:bg-cif-primary-hover shadow-cif-sm hover:shadow-cif',
        destructive: 'bg-status-error text-white hover:bg-error-600',
        outline:
          'border border-edge-default bg-white text-cif-primary hover:bg-cif-primary-light hover:border-cif-primary',
        secondary: 'bg-surface-muted text-content-primary hover:bg-edge-default',
        ghost: 'text-content-secondary hover:bg-surface-muted hover:text-content-primary',
        link: 'text-cif-secondary underline-offset-4 hover:underline hover:text-cif-secondary-hover',
        success: 'bg-status-success text-white hover:bg-success-600',
        accent: 'bg-cif-accent text-white hover:bg-cif-accent-hover shadow-cif-sm hover:shadow-cif',
      },
      size: {
        default: 'h-10 px-4 py-2',
        sm: 'h-8 rounded-cif px-3 text-xs',
        lg: 'h-12 rounded-cif-lg px-8 text-base',
        icon: 'h-10 w-10',
      },
    },
    defaultVariants: {
      variant: 'default',
      size: 'default',
    },
  }
);

export interface ButtonProps
  extends ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  asChild?: boolean;
}

const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, asChild = false, ...props }, ref) => {
    const Comp = asChild ? Slot : 'button';
    return (
      <Comp
        className={cn(buttonVariants({ variant, size, className }))}
        ref={ref}
        {...props}
      />
    );
  }
);
Button.displayName = 'Button';

export { Button, buttonVariants };
