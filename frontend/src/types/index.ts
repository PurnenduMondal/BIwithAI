export interface User {
  id: string;
  email: string;
  full_name: string | null;
  role: 'admin' | 'analyst' | 'viewer';
  is_active: boolean;
  created_at: string;
  last_login: string | null;
}

export interface Organization {
  id: string;
  name: string;
  subdomain: string | null;
  settings: Record<string, any>;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface DataSource {
  id: string;
  name: string;
  type: 'csv' | 'postgresql' | 'mysql' | 'api' | 'google_sheets';
  status: 'pending' | 'active' | 'error' | 'syncing';
  schema_metadata: Record<string, any>;
  last_sync: string | null;
  created_at: string;
  updated_at: string;
  org_id?: string;
  // For DataSourceWithStats
  total_rows?: number;
  total_columns?: number;
  last_dataset_version?: number;
}

export interface Dashboard {
  id: string;
  name: string;
  description: string | null;
  layout_config: Record<string, any>;
  filters: any[];
  theme: Record<string, any>;
  is_template: boolean;
  is_public: boolean;
  created_at: string;
  updated_at: string;
  widgets?: Widget[];
}

export interface Widget {
  id: string;
  dashboard_id: string;
  widget_type: 'chart' | 'metric' | 'table' | 'text' | 'ai_insight';
  title: string;
  position: {
    x: number;
    y: number;
    w: number;
    h: number;
  };
  config: Record<string, any>;
  data_source_id: string | null;
  created_at: string;
}

export interface Insight {
  id: string;
  dashboard_id: string;
  insight_type: string;
  content: string;
  confidence_score: number;
  insight_metadata: Record<string, any>;
  created_at: string;
}

export interface Alert {
  id: string;
  dashboard_id: string;
  widget_id: string | null;
  condition: Record<string, any>;
  notification_channels: any[];
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

// Component Props
export * from './dashboard';