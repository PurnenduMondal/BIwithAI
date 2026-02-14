export interface OrganizationMembership {
  org_id: string;
  org_name: string;
  subdomain: string | null;
  role: 'admin' | 'member' | 'viewer';
}

export interface User {
  id: string;
  email: string;
  full_name: string | null;
  role: 'admin' | 'analyst' | 'viewer';
  is_active: boolean;
  created_at: string;
  last_login: string | null;
  organizations: OrganizationMembership[];
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
  generated_by_ai?: boolean;
  generation_context?: Record<string, any>;
  created_at: string;
  updated_at: string;
  widgets?: Widget[];
}

export interface Widget {
  id: string;
  dashboard_id: string;
  widget_type: 'line' | 'bar' | 'pie' | 'area' | 'scatter' | 'heatmap' | 'metric' | 'table' | 'gauge';
  title: string;
  description?: string | null;
  position: {
    x: number;
    y: number;
    w: number;
    h: number;
  };
  query_config: Record<string, any>; // Data query configuration
  chart_config: Record<string, any>; // Visual chart configuration
  data_mapping?: Record<string, any>; // Column mappings
  data_source_id: string | null;
  generated_by_ai?: boolean;
  generation_prompt?: string | null;
  ai_reasoning?: string | null;
  created_at: string;
  updated_at?: string;
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