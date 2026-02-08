import { type ReactNode } from 'react';
interface ModalProps {
    isOpen: boolean;
    onClose: () => void;
    title: string;
    children: ReactNode;
    footer?: ReactNode;
    size?: 'sm' | 'md' | 'lg' | 'xl';
}
export declare const Modal: ({ isOpen, onClose, title, children, footer, size, }: ModalProps) => import("react").ReactPortal;
export {};
