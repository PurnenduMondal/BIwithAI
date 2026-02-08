import { type ButtonHTMLAttributes, type ReactNode } from 'react';
interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
    variant?: 'primary' | 'secondary' | 'outline' | 'danger';
    size?: 'sm' | 'md' | 'lg';
    isLoading?: boolean;
    children: ReactNode;
}
export declare const Button: ({ variant, size, isLoading, children, className, disabled, ...props }: ButtonProps) => import("react/jsx-runtime").JSX.Element;
export {};
