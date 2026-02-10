/**
 * Utility functions for multi-tenant organization/subdomain management
 */

/**
 * Extract subdomain from current hostname
 * 
 * Examples:
 * - acme.localhost:3000 -> "acme"
 * - globex.localhost -> "globex"
 * - localhost:3000 -> null
 * - 127.0.0.1 -> null
 * - acme.myapp.com -> "acme"
 * 
 * @returns The subdomain string or null if no subdomain exists
 */
export const getCurrentSubdomain = (): string | null => {
  const hostname = window.location.hostname;
  
  // Split hostname by dots
  const parts = hostname.split('.');
  
  // If there are at least 2 parts (subdomain.domain)
  if (parts.length >= 2) {
    const subdomain = parts[0];
    
    // Ignore common non-subdomain cases
    const ignoredSubdomains = ['localhost', 'www', '127'];
    
    // Check if it's a valid subdomain (not localhost, www, or IP)
    if (!ignoredSubdomains.includes(subdomain) && !subdomain.match(/^\d+$/)) {
      return subdomain;
    }
  }
  
  return null;
};

/**
 * Check if the application is running in multi-tenant mode
 * (i.e., accessed via a subdomain)
 */
export const isMultiTenantMode = (): boolean => {
  return getCurrentSubdomain() !== null;
};

/**
 * Get the base domain without subdomain
 * 
 * Examples:
 * - acme.localhost:3000 -> "localhost:3000"
 * - globex.myapp.com -> "myapp.com"
 * - localhost -> "localhost"
 */
export const getBaseDomain = (): string => {
  const hostname = window.location.hostname;
  const port = window.location.port;
  const parts = hostname.split('.');
  
  // If subdomain exists, remove it
  if (parts.length >= 2 && getCurrentSubdomain()) {
    const baseParts = parts.slice(1);
    const baseDomain = baseParts.join('.');
    return port ? `${baseDomain}:${port}` : baseDomain;
  }
  
  return port ? `${hostname}:${port}` : hostname;
};

/**
 * Build a URL for a specific organization subdomain
 * 
 * @param subdomain - The organization subdomain
 * @param path - Optional path to append
 */
export const buildOrgUrl = (subdomain: string, path: string = '/'): string => {
  const protocol = window.location.protocol;
  const baseDomain = getBaseDomain();
  return `${protocol}//${subdomain}.${baseDomain}${path}`;
};
