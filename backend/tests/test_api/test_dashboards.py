import pytest
from httpx import AsyncClient
from uuid import uuid4

@pytest.mark.asyncio
async def test_create_dashboard(authenticated_client: AsyncClient, test_user, db_session):
    """Test dashboard creation"""
    # Create organization first
    from app.models.organization import Organization, OrganizationMember
    
    org = Organization(name="Test Org")
    db_session.add(org)
    await db_session.flush()
    
    member = OrganizationMember(
        org_id=org.id,
        user_id=test_user.id,
        role="admin"
    )
    db_session.add(member)
    await db_session.commit()
    
    # Create dashboard
    response = await authenticated_client.post(
        "/api/v1/dashboards/",
        json={
            "name": "Test Dashboard",
            "description": "A test dashboard",
            "layout_config": {},
            "filters": [],
            "theme": {}
        }
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test Dashboard"
    assert "id" in data

@pytest.mark.asyncio
async def test_list_dashboards(authenticated_client: AsyncClient, test_user, db_session):
    """Test listing dashboards"""
    # Setup organization
    from app.models.organization import Organization, OrganizationMember
    from app.models.dashboard import Dashboard
    
    org = Organization(name="Test Org")
    db_session.add(org)
    await db_session.flush()
    
    member = OrganizationMember(
        org_id=org.id,
        user_id=test_user.id,
        role="admin"
    )
    db_session.add(member)
    
    # Create test dashboards
    for i in range(3):
        dashboard = Dashboard(
            org_id=org.id,
            created_by=test_user.id,
            name=f"Dashboard {i}",
            description=f"Test dashboard {i}"
        )
        db_session.add(dashboard)
    
    await db_session.commit()
    
    # List dashboards
    response = await authenticated_client.get("/api/v1/dashboards/")
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3

@pytest.mark.asyncio
async def test_get_dashboard(authenticated_client: AsyncClient, test_user, db_session):
    """Test getting specific dashboard"""
    from app.models.organization import Organization, OrganizationMember
    from app.models.dashboard import Dashboard
    
    # Setup
    org = Organization(name="Test Org")
    db_session.add(org)
    await db_session.flush()
    
    member = OrganizationMember(
        org_id=org.id,
        user_id=test_user.id,
        role="admin"
    )
    db_session.add(member)
    
    dashboard = Dashboard(
        org_id=org.id,
        created_by=test_user.id,
        name="Specific Dashboard",
        description="Test"
    )
    db_session.add(dashboard)
    await db_session.commit()
    await db_session.refresh(dashboard)
    
    # Get dashboard
    response = await authenticated_client.get(f"/api/v1/dashboards/{dashboard.id}")
    
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Specific Dashboard"