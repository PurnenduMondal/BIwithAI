from pydantic import BaseModel
from typing import Dict, List, Any, Optional
from datetime import datetime
from uuid import UUID

class PeriodInfo(BaseModel):
    start: str
    end: str

class UserStats(BaseModel):
    total: int
    new: int
    active: int

class OrganizationStats(BaseModel):
    total: int

class DashboardStats(BaseModel):
    total: int
    created_in_period: int

class DataSourceStats(BaseModel):
    total: int
    by_type: Dict[str, int]

class TopOrganization(BaseModel):
    org_id: str
    name: str
    dashboard_count: int

class UsageStatsResponse(BaseModel):
    period: PeriodInfo
    users: UserStats
    organizations: OrganizationStats
    dashboards: DashboardStats
    data_sources: DataSourceStats
    top_organizations: List[TopOrganization]

class AuditLogResponse(BaseModel):
    id: UUID
    user_id: UUID
    action: str
    resource_type: str
    resource_id: Optional[UUID]
    audit_metadata: Dict[str, Any]
    ip_address: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True

class ComponentHealth(BaseModel):
    status: str
    latency_ms: Optional[float] = None
    worker_count: Optional[int] = None

class ResourceMetrics(BaseModel):
    cpu_percent: float
    memory_percent: float
    memory_used_gb: float
    memory_total_gb: float
    disk_percent: float
    disk_used_gb: float
    disk_total_gb: float

class SystemHealthResponse(BaseModel):
    status: str  # healthy, degraded, unhealthy
    timestamp: str
    components: Dict[str, ComponentHealth]
    resources: ResourceMetrics