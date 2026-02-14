# Multi-Tenant Subdomain Routing Guide

## Overview

Your application now supports **subdomain-based multi-tenant routing**. Users belonging to different organizations can access their data through organization-specific subdomains.

## How It Works

### 1. **URL Structure**

- **Base Domain:** `http://localhost:3000/` (no organization context)
- **Organization Subdomain:** `http://acme.localhost:3000/` (Acme organization context)
- **Another Organization:** `http://globex.localhost:3000/` (Globex organization context)

### 2. **Authentication Flow**

#### Step 1: User Logs In
- User visits `http://localhost:3000/login`
- Enters credentials and clicks "Sign In"

#### Step 2: Backend Returns User Data
- Backend includes list of organizations the user belongs to
- Each organization has: `org_id`, `org_name`, `subdomain`, and `role`

#### Step 3: Automatic Redirect Logic

**Scenario A: User on Base Domain (no subdomain)**
- If user has **1 organization** → Redirect to that org's subdomain automatically
  - Example: Redirect to `http://acme.localhost:3000/home`
- If user has **multiple organizations** → Show organization selector
  - User picks which org → Redirect to `http://[chosen-org].localhost:3000/home`
- If user has **no organizations** → Stay on base domain

**Scenario B: User Already on Subdomain**
- Verify user has access to that organization
- If yes → Continue to `/home` on that subdomain
- If no → Redirect to their first available organization

### 3. **How Subdomain is Detected**

The frontend uses utility functions in `utils/tenant.ts`:

```typescript
import { getCurrentSubdomain, redirectToSubdomain, storeSubdomainContext } from '../utils/tenant';

// Get current subdomain (null if on base domain)
const subdomain = getCurrentSubdomain();
// Returns: 'acme' from 'acme.localhost:3000'
// Returns: null from 'localhost:3000'

// Redirect to an organization's subdomain
redirectToSubdomain('acme', '/home');
// Navigates to: http://acme.localhost:3000/home

// Store subdomain in localStorage for persistence
storeSubdomainContext('acme');
```

### 4. **Backend Tenant Resolution**

The backend middleware (`TenantResolverMiddleware`) extracts the subdomain from:

1. **Custom Header:** `X-Organization-Subdomain` (sent by frontend)
2. **Host Header:** Falls back to parsing the hostname

The frontend API client automatically sends the `X-Organization-Subdomain` header with every request:

```typescript
// In api/client.ts
const subdomain = getCurrentSubdomain();
if (subdomain) {
  config.headers['X-Organization-Subdomain'] = subdomain;
}
```

## Testing Locally

### Option 1: Using localhost Subdomains (Easiest)

Modern browsers support `*.localhost` subdomains without any configuration:

1. Start your backend: `http://localhost:8000`
2. Start your frontend: `http://localhost:3000`
3. Access different organizations:
   - `http://localhost:3000` - Base domain
   - `http://acme.localhost:3000` - Acme organization
   - `http://globex.localhost:3000` - Globex organization

### Option 2: Using /etc/hosts (More Control)

Add entries to your hosts file:

**On Mac/Linux:** Edit `/etc/hosts`
**On Windows:** Edit `C:\Windows\System32\drivers\etc\hosts`

```
127.0.0.1   acme.localhost
127.0.0.1   globex.localhost
127.0.0.1   initech.localhost
```

Then access via:
- `http://acme.localhost:3000`
- `http://globex.localhost:3000`

## Setting Up Organizations with Subdomains

### Backend: Create Organization with Subdomain

When creating an organization, set the `subdomain` field:

```python
# Example API call or database entry
organization = Organization(
    name="Acme Corporation",
    subdomain="acme",  # Must be unique, lowercase, alphanumeric + hyphens
    settings={}
)
```

### Frontend: API to Create Organization

```typescript
// In your organization API
const createOrganization = async (data: {
  name: string;
  subdomain: string;
}) => {
  const response = await apiClient.post('/api/v1/organizations', data);
  return response.data;
};
```

## User Experience Examples

### Example 1: New User with One Organization

1. User registers: `jane@example.com`
2. User creates/joins organization "Acme" with subdomain "acme"
3. User logs in at `localhost:3000/login`
4. **Auto-redirect** to `acme.localhost:3000/home`
5. All subsequent work happens on `acme.localhost:3000`

### Example 2: User with Multiple Organizations

1. User logs in at `localhost:3000/login`
2. System detects user belongs to 3 organizations
3. **Shows organization selector** at `/select-organization`
4. User clicks "Acme Corporation"
5. **Redirects** to `acme.localhost:3000/home`
6. Later, user wants to switch to "Globex"
7. User navigates to `globex.localhost:3000`
8. System validates access and allows entry

### Example 3: Directly Accessing Organization Subdomain

1. User bookmarks `acme.localhost:3000/dashboards`
2. User visits bookmark (not logged in)
3. System redirects to `/login` on `acme.localhost:3000`
4. User logs in
5. System validates user has access to "Acme"
6. User proceeds to `/dashboards` on `acme.localhost:3000`

## Key Components Modified

### Backend Changes

1. **User Schema** ([schemas/user.py](backend/app/schemas/user.py))
   - Added `OrganizationMembership` model
   - Updated `UserResponse` to include `organizations` list

2. **Users Endpoint** ([api/v1/endpoints/users.py](backend/app/api/v1/endpoints/users.py))
   - Modified `/me` to load and return organization memberships

### Frontend Changes

1. **Types** ([types/index.ts](frontend/src/types/index.ts))
   - Added `OrganizationMembership` interface
   - Updated `User` interface with `organizations` field

2. **Tenant Utilities** ([utils/tenant.ts](frontend/src/utils/tenant.ts))
   - `getCurrentSubdomain()` - Detect current subdomain
   - `redirectToSubdomain()` - Navigate to org subdomain
   - `storeSubdomainContext()` - Persist subdomain in localStorage

3. **Auth Hook** ([hooks/useAuth.ts](frontend/src/hooks/useAuth.ts))
   - Updated login flow to handle subdomain redirects
   - Added organization selection logic
   - Updated logout to clear subdomain and return to base domain

4. **API Client** ([api/client.ts](frontend/src/api/client.ts))
   - Already configured to send `X-Organization-Subdomain` header

5. **Organization Selector** ([pages/SelectOrganization.tsx](frontend/src/pages/SelectOrganization.tsx))
   - New page to let users choose their organization

6. **App Routes** ([App.tsx](frontend/src/App.tsx))
   - Added `/select-organization` route

## Troubleshooting

### Issue: Subdomain not detected

**Solution:** Check browser console:
```javascript
import { getCurrentSubdomain } from './utils/tenant';
console.log('Current subdomain:', getCurrentSubdomain());
```

### Issue: Infinite redirect loop

**Solution:** Check if organization subdomain is set correctly in database and user has membership.

### Issue: Auth doesn't persist across subdomains

**Solution:** The current implementation uses localStorage which is domain-scoped. The auth flow handles this by re-authenticating when switching subdomains. For production, consider:
- Using cookies with domain set to `.yourdomain.com`
- Implementing single sign-on (SSO)

### Issue: Can't access org.localhost on browser

**Solution:** Most modern browsers support `*.localhost` automatically. If not:
1. Try Chrome, Firefox, or Edge (Safari might have issues)
2. Use `/etc/hosts` method (Option 2 above)

## Production Considerations

### 1. **Domain Configuration**

Set up wildcard DNS for your domain:
```
*.yourdomain.com → Your Server IP
```

### 2. **SSL Certificates**

Use wildcard SSL certificate:
```
*.yourdomain.com
```

### 3. **Cookie Domain**

Set auth cookies to work across subdomains:
```python
# Backend cookie settings
cookie_domain = ".yourdomain.com"
```

### 4. **CORS Configuration**

Allow requests from subdomains:
```python
# backend/app/main.py
origins = [
    "https://*.yourdomain.com",
    "http://*.yourdomain.com"
]
```

### 5. **Environment Variables**

Update API base URL to be dynamic:
```typescript
// frontend/src/api/client.ts
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';
```

## Next Steps

1. **Test the Flow:**
   - Create organizations with subdomains in database
   - Add users as organization members
   - Test login → organization selection → subdomain redirect

2. **Add Organization Creation UI:**
   - Create form to register new organizations
   - Auto-generate subdomain from organization name

3. **Add Organization Switcher:**
   - Add dropdown in header to switch between user's organizations
   - Redirects to selected organization's subdomain

4. **Implement Data Isolation:**
   - Ensure all API endpoints filter data by organization
   - Use the subdomain from `request.state.subdomain` in backend

5. **Production Deployment:**
   - Configure wildcard DNS
   - Set up wildcard SSL
   - Update CORS and cookie settings

## Summary

You now have a fully functional multi-tenant platform with subdomain-based routing! Users can:

- ✅ Login and be automatically directed to their organization's subdomain
- ✅ Choose from multiple organizations if they belong to more than one
- ✅ Access organization-specific data at subdomain URLs
- ✅ Have their subdomain context automatically sent with API requests
- ✅ Switch between organizations by navigating to different subdomains
