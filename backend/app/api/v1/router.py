from fastapi import APIRouter

from app.api.v1.endpoints import (
    auth,
    users,
    organizations,
    data_sources,
    dashboards,
    widgets,
    insights,
    analytics,
    exports,
    downloads,
    alerts,
    admin,
    debug
)
from app.api.v1 import chat

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(users.router, prefix="/users", tags=["Users"])
api_router.include_router(organizations.router, prefix="/organizations", tags=["Organizations"])
api_router.include_router(data_sources.router, prefix="/data-sources", tags=["Data Sources"])
api_router.include_router(dashboards.router, prefix="/dashboards", tags=["Dashboards"])
api_router.include_router(widgets.router, prefix="/widgets", tags=["Widgets"])
api_router.include_router(insights.router, prefix="/insights", tags=["Insights"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["Analytics"])
api_router.include_router(exports.router, prefix="/exports", tags=["Exports"])
api_router.include_router(downloads.router, prefix="/downloads", tags=["Downloads"])
api_router.include_router(alerts.router, prefix="/alerts", tags=["Alerts"])
api_router.include_router(admin.router, prefix="/admin", tags=["Admin"])
api_router.include_router(debug.router, prefix="/debug", tags=["Debug"])
api_router.include_router(chat.router, tags=["AI Chat"])  # Chat router already includes /chat prefix