/**
 * API utilities and fetch wrappers
 */

/**
 * Fetch with automatic 401 session expiry handling
 */
async function fetchWithAuth(url, options = {}) {
    try {
        const headers = options.headers || {};
        
        // Add Bearer token if available
        const token = getAuthToken();
        if (token && !headers['Authorization']) {
            headers['Authorization'] = `Bearer ${token}`;
        }
        
        const response = await fetch(url, { ...options, headers });
        
        // Handle 401 - session expired
        if (response.status === 401) {
            handleSessionExpiry();
            return { ok: false, status: 401, error: 'Session expired' };
        }
        
        return response;
    } catch (error) {
        console.error('Fetch error:', error);
        throw error;
    }
}

/**
 * Handle session expiry
 */
function handleSessionExpiry() {
    clearAuthToken();
    clearUserProfile();
    // Redirect to login
    setTimeout(() => {
        window.location.href = 'login.html';
    }, 800);
}

/**
 * Parse response with safe JSON handling
 */
async function parseResponse(response) {
    try {
        const contentType = response.headers.get('content-type');
        if (contentType && contentType.includes('application/json')) {
            return await response.json();
        }
        return { ok: response.ok, text: await response.text() };
    } catch (error) {
        console.warn('Failed to parse response:', error);
        return { ok: response.ok };
    }
}

/**
 * Extract API keys from server response
 */
function extractApiKeysFromResponse(data) {
    const verifyCandidates = [
        data?.verify_api_key,
        data?.x_api_key,
        data?.api_key,
        data?.['x-api-key']
    ];
    const verifyKey = verifyCandidates.find(k => typeof k === 'string' && k.length > 0);
    if (verifyKey) setApiKey(verifyKey, 'verify');
    
    const reportsCandidates = [
        data?.reports_api_key,
        data?.reports_key
    ];
    const reportsKey = reportsCandidates.find(k => typeof k === 'string' && k.length > 0);
    if (reportsKey) setApiKey(reportsKey, 'reports');
}

/**
 * Check if user is authenticated
 */
function isAuthenticated() {
    return !!getAuthToken();
}

/**
 * Check if user is admin
 */
function isAdmin() {
    
    const user = getUserProfile();
    return user && user.role === 'Administrator';
}

/**
 * Redirect to login if not authenticated
 */
function requireAuth() {
    if (!isAuthenticated()) {
        window.location.href = 'login.html';
    }
}
