# Multi-Tenant Subdomain Support

This document explains how to test and use the subdomain-based multi-tenant feature.

## How It Works

### Backend Flow
1. **Middleware**: `TenantResolverMiddleware` extracts subdomain from `X-Organization-Subdomain` header or Host header
2. **Dependencies**: `get_user_organization()` uses the subdomain to resolve the correct organization
3. **Security**: Verifies user is actually a member of the requested organization

### Frontend Flow
1. **Utility**: `getCurrentSubdomain()` extracts subdomain from `window.location.hostname`
2. **API Client**: Automatically adds `X-Organization-Subdomain` header to all API requests
3. **Transparent**: No code changes needed in components - works automatically

## Testing on Localhost

### Method 1: Using *.localhost (Recommended)

Modern browsers support `*.localhost` without configuration:

1. **Create organizations with subdomains:**
```bash
# Create Acme organization
curl -X POST http://localhost:8000/api/v1/organizations \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "Acme Corp", "subdomain": "acme"}'

# Create Globex organization
curl -X POST http://localhost:8000/api/v1/organizations \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "Globex Inc", "subdomain": "globex"}'
```

2. **Add users to organizations** (if not automatic)

3. **Access via subdomain:**
- Frontend: `http://acme.localhost:3000`
- Frontend: `http://globex.localhost:3000`
- API: Backend automatically runs on `http://localhost:8000`

### Method 2: Using hosts file

If `*.localhost` doesn't work, edit your hosts file:

**Location**: `C:\Windows\System32\drivers\etc\hosts`

**Add:**
```
127.0.0.1 acme.localhost
127.0.0.1 globex.localhost
127.0.0.1 localhost
```

Then restart your browser.

## Testing the Feature

### 1. Without Subdomain (Fallback Mode)
Access: `http://localhost:3000`
- Uses user's first organization membership
- Legacy behavior for backward compatibility

### 2. With Subdomain (Multi-Tenant Mode)
Access: `http://acme.localhost:3000`
- Resolves to "acme" organization
- User must be a member, or gets 403 Forbidden
- Different subdomain = different organization context

### 3. Verify Isolation

**As Acme User:**
```bash
# Access via acme subdomain
curl http://localhost:8000/api/v1/dashboards \
  -H "Authorization: Bearer ACME_USER_TOKEN" \
  -H "X-Organization-Subdomain: acme"

# Returns only Acme dashboards
```

**As Globex User:**
```bash
# Access via globex subdomain
curl http://localhost:8000/api/v1/dashboards \
  -H "Authorization: Bearer GLOBEX_USER_TOKEN" \
  -H "X-Organization-Subdomain: globex"

# Returns only Globex dashboards
```

**Cross-Tenant Access Blocked:**
```bash
# Acme user tries to access Globex data
curl http://localhost:8000/api/v1/dashboards \
  -H "Authorization: Bearer ACME_USER_TOKEN" \
  -H "X-Organization-Subdomain: globex"

# Returns 403 Forbidden
```

## Frontend Usage Examples

### Check Current Tenant
```typescript
import { getCurrentSubdomain, isMultiTenantMode } from '@/utils/tenant';

// In a component
const subdomain = getCurrentSubdomain();
console.log('Current organization:', subdomain); // "acme" or null

if (isMultiTenantMode()) {
  console.log('Running in multi-tenant mode');
}
```

### Build Organization URLs
```typescript
import { buildOrgUrl } from '@/utils/tenant';

// Link to different organization
const acmeUrl = buildOrgUrl('acme', '/dashboard');
// Result: http://acme.localhost:3000/dashboard

const globexUrl = buildOrgUrl('globex', '/settings');
// Result: http://globex.localhost:3000/settings
```

### Organization Switcher Component (Example)
```typescript
import { useNavigate } from 'react-router-dom';
import { buildOrgUrl } from '@/utils/tenant';

const OrganizationSwitcher = ({ organizations }) => {
  const handleSwitch = (subdomain: string) => {
    // Navigate to same path but different subdomain
    const newUrl = buildOrgUrl(subdomain, window.location.pathname);
    window.location.href = newUrl;
  };

  return (
    <select onChange={(e) => handleSwitch(e.target.value)}>
      {organizations.map(org => (
        <option key={org.id} value={org.subdomain}>
          {org.name}
        </option>
      ))}
    </select>
  );
};
```

## Security Notes

1. **User Verification**: Backend verifies user is a member of the requested organization
2. **403 Forbidden**: Users get an error if they try to access organizations they don't belong to
3. **Automatic**: No manual org_id selection needed - subdomain determines context
4. **Auditable**: All requests log which organization was accessed

## Troubleshooting

### "Organization not found" error
- User is not a member of any organization
- Solution: Add user to an organization via admin endpoints

### "User is not a member of organization with subdomain 'acme'" error
- User tried to access an organization they don't belong to
- Solution: Add user to that organization or switch to correct subdomain

### Subdomain not detected
- Check browser console: `getCurrentSubdomain()` should return the subdomain
- Verify you're accessing via `subdomain.localhost:3000`, not just `localhost:3000`
- Try clearing browser cache

### CORS errors
- Ensure `CORS_ORIGINS` in backend includes subdomain patterns
- May need to add: `"http://*.localhost:3000"` to allowed origins
