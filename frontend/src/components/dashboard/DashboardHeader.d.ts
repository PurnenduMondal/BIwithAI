import { type Dashboard } from '@/types';
interface DashboardHeaderProps {
    dashboard: Dashboard;
    onEdit: () => void;
    isEditing: boolean;
}
export declare const DashboardHeader: ({ dashboard, onEdit, isEditing }: DashboardHeaderProps) => import("react/jsx-runtime").JSX.Element;
export {};
