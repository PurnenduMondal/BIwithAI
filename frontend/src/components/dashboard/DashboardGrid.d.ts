import 'react-grid-layout/css/styles.css';
import 'react-resizable/css/styles.css';
import { type Widget } from '@/types';
interface DashboardGridProps {
    dashboardId: string;
    widgets: Widget[];
    isEditing?: boolean;
}
export declare const DashboardGrid: ({ dashboardId, widgets, isEditing }: DashboardGridProps) => import("react/jsx-runtime").JSX.Element;
export {};
