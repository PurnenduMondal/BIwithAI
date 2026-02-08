-- Users and Authentication
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255),
    full_name VARCHAR(255),
    role VARCHAR(50) DEFAULT 'viewer', -- admin, analyst, viewer
    created_at TIMESTAMP DEFAULT NOW(),
    last_login TIMESTAMP
);

-- Organizations (Multi-tenancy)
CREATE TABLE organizations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    subdomain VARCHAR(100) UNIQUE,
    settings JSONB, -- branding, limits, features
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE organization_members (
    org_id UUID REFERENCES organizations(id),
    user_id UUID REFERENCES users(id),
    role VARCHAR(50),
    PRIMARY KEY (org_id, user_id)
);

-- Data Sources
CREATE TABLE data_sources (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID REFERENCES organizations(id),
    name VARCHAR(255) NOT NULL,
    type VARCHAR(50), -- csv, postgresql, mysql, api, google_sheets
    connection_config JSONB, -- encrypted credentials, endpoints
    schema_metadata JSONB, -- detected columns, types, relationships
    last_sync TIMESTAMP,
    sync_frequency VARCHAR(50), -- hourly, daily, weekly, manual
    status VARCHAR(50), -- active, error, pending
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Datasets (processed data snapshots)
CREATE TABLE datasets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    data_source_id UUID REFERENCES data_sources(id),
    version INTEGER,
    row_count INTEGER,
    column_count INTEGER,
    data_profile JSONB, -- statistics, distributions
    storage_path VARCHAR(500), -- S3/file system path
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(data_source_id, version)
);

-- Dashboards
CREATE TABLE dashboards (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID REFERENCES organizations(id),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    layout_config JSONB, -- grid layout, widget positions
    filters JSONB, -- global filters
    theme JSONB, -- colors, fonts
    is_template BOOLEAN DEFAULT false,
    is_public BOOLEAN DEFAULT false,
    public_share_token VARCHAR(100) UNIQUE,
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Dashboard Widgets
CREATE TABLE widgets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    dashboard_id UUID REFERENCES dashboards(id) ON DELETE CASCADE,
    widget_type VARCHAR(50), -- chart, metric, table, text, ai_insight
    title VARCHAR(255),
    position JSONB, -- {x, y, width, height}
    config JSONB, -- chart config, data queries
    data_source_id UUID REFERENCES data_sources(id),
    created_at TIMESTAMP DEFAULT NOW()
);

-- AI-Generated Insights
CREATE TABLE insights (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    dashboard_id UUID REFERENCES dashboards(id),
    widget_id UUID REFERENCES widgets(id),
    insight_type VARCHAR(50), -- trend, anomaly, recommendation, summary
    content TEXT, -- AI-generated text
    confidence_score DECIMAL(3,2),
    metadata JSONB, -- supporting data, calculations
    created_at TIMESTAMP DEFAULT NOW()
);

-- Query Cache
CREATE TABLE query_cache (
    cache_key VARCHAR(255) PRIMARY KEY,
    result JSONB,
    expires_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Audit Log
CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    action VARCHAR(100), -- view_dashboard, create_widget, etc.
    resource_type VARCHAR(50),
    resource_id UUID,
    metadata JSONB,
    ip_address INET,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Alerts & Notifications
CREATE TABLE alerts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    dashboard_id UUID REFERENCES dashboards(id),
    widget_id UUID REFERENCES widgets(id),
    condition JSONB, -- threshold rules
    notification_channels JSONB, -- email, slack, webhook
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE alert_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    alert_id UUID REFERENCES alerts(id),
    triggered_at TIMESTAMP,
    value JSONB,
    notification_sent BOOLEAN
);
```

---

## 2. Backend Architecture & Implementation

### **Project Structure**
```
backend/
├── src/
│   ├── api/
│   │   ├── routes/
│   │   │   ├── auth.py
│   │   │   ├── datasources.py
│   │   │   ├── dashboards.py
│   │   │   ├── widgets.py
│   │   │   └── insights.py
│   │   └── middlewares/
│   │       ├── auth.py
│   │       ├── rate_limit.py
│   │       └── error_handler.py
│   ├── services/
│   │   ├── data_ingestion/
│   │   │   ├── connectors/
│   │   │   │   ├── csv_connector.py
│   │   │   │   ├── postgres_connector.py
│   │   │   │   ├── api_connector.py
│   │   │   │   └── base_connector.py
│   │   │   ├── schema_detector.py
│   │   │   └── data_cleaner.py
│   │   ├── analytics/
│   │   │   ├── profiler.py
│   │   │   ├── pattern_detector.py
│   │   │   ├── forecasting.py
│   │   │   └── anomaly_detection.py
│   │   ├── ai/
│   │   │   ├── insight_generator.py
│   │   │   ├── nlp_query.py
│   │   │   └── chart_recommender.py
│   │   ├── dashboard/
│   │   │   ├── generator.py
│   │   │   ├── layout_engine.py
│   │   │   └── export_service.py
│   │   └── cache/
│   │       └── redis_cache.py
│   ├── models/
│   │   ├── user.py
│   │   ├── datasource.py
│   │   └── dashboard.py
│   ├── workers/
│   │   ├── data_sync.py
│   │   ├── insight_generation.py
│   │   └── alert_checker.py
│   └── utils/
│       ├── encryption.py
│       ├── validators.py
│       └── helpers.py
├── tests/
├── requirements.txt
└── config.py