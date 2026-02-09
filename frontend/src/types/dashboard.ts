import { type Dashboard } from './index';

export interface DashboardHeaderProps {
  dashboard: Dashboard;
  onEdit: () => void;
  isEditing: boolean;
  onAddWidget?: () => void;
}
