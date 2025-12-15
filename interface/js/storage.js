/**
 * Storage utilities for localStorage management
 */

const STORAGE_KEYS = {
    AUTH_TOKEN: 'miniapp_auth_token',
    USER_PROFILE: 'miniapp_user',
    PENDING_LOGIN: 'miniapp_pending_login',
    VERIFY_API_KEY: 'miniapp_verify_api_key',
    REPORTS_API_KEY: 'miniapp_reports_api_key',
    DRAFT_TITLE: 'miniapp_draft_title',
    DRAFT_CONTENT: 'miniapp_draft_content'
};

/**
 * Get value from localStorage with optional fallback
 */
function getStoredValue(key, defaultValue = null) {
    try {
        const value = localStorage.getItem(key);
        return value !== null ? value : defaultValue;
    } catch (e) {
        console.warn(`Failed to get localStorage key: ${key}`, e);
        return defaultValue;
    }
}

/**
 * Set value in localStorage
 */
function setStoredValue(key, value) {
    try {
        if (value === null || value === undefined) {
            localStorage.removeItem(key);
        } else {
            localStorage.setItem(key, value);
        }
        return true;
    } catch (e) {
        console.warn(`Failed to set localStorage key: ${key}`, e);
        return false;
    }
}

/**
 * Get parsed JSON from localStorage
 */
function getStoredJSON(key, defaultValue = null) {
    try {
        const value = localStorage.getItem(key);
        return value ? JSON.parse(value) : defaultValue;
    } catch (e) {
        console.warn(`Failed to parse localStorage key: ${key}`, e);
        return defaultValue;
    }
}

/**
 * Set JSON object to localStorage
 */
function setStoredJSON(key, obj) {
    try {
        localStorage.setItem(key, JSON.stringify(obj));
        return true;
    } catch (e) {
        console.warn(`Failed to store JSON for key: ${key}`, e);
        return false;
    }
}

/**
 * Clear a specific localStorage key
 */
function clearStoredValue(key) {
    try {
        localStorage.removeItem(key);
        return true;
    } catch (e) {
        console.warn(`Failed to clear localStorage key: ${key}`, e);
        return false;
    }
}

/**
 * Clear multiple localStorage keys
 */
function clearStoredValues(...keys) {
    keys.forEach(key => clearStoredValue(key));
}

/**
 * Get authentication token from localStorage
 */
function getAuthToken() {
    return getStoredValue(STORAGE_KEYS.AUTH_TOKEN);
}

/**
 * Set authentication token in localStorage
 */
function setAuthToken(token) {
    return setStoredValue(STORAGE_KEYS.AUTH_TOKEN, token);
}

/**
 * Clear authentication token
 */
function clearAuthToken() {
    return clearStoredValue(STORAGE_KEYS.AUTH_TOKEN);
}

/**
 * Get user profile from localStorage
 */
function getUserProfile() {
    return getStoredJSON(STORAGE_KEYS.USER_PROFILE);
}

/**
 * Set user profile in localStorage
 */
function setUserProfile(profile) {
    return setStoredJSON(STORAGE_KEYS.USER_PROFILE, profile);
}

/**
 * Clear user profile
 */
function clearUserProfile() {
    return clearStoredValue(STORAGE_KEYS.USER_PROFILE);
}

/**
 * Get pending login data
 */
function getPendingLogin() {
    return getStoredJSON(STORAGE_KEYS.PENDING_LOGIN);
}

/**
 * Set pending login data
 */
function setPendingLogin(loginData) {
    return setStoredJSON(STORAGE_KEYS.PENDING_LOGIN, loginData);
}

/**
 * Clear pending login
 */
function clearPendingLogin() {
    return clearStoredValue(STORAGE_KEYS.PENDING_LOGIN);
}

/**
 * Get API key from localStorage with fallback candidates
 */
function getApiKey(type = 'reports') {
    const candidates = type === 'verify'
        ? ['miniapp_verify_api_key', 'miniapp_api_key', 'miniapp_key']
        : ['miniapp_reports_api_key', 'miniapp_verify_api_key', 'miniapp_api_key', 'miniapp_key'];

    for (const key of candidates) {
        const value = getStoredValue(key);
        if (value && value.length > 0) return value;
    }
    return null;
}

/**
 * Set API key in localStorage
 */
function setApiKey(key, type = 'reports') {
    const storageKey = type === 'verify'
        ? STORAGE_KEYS.VERIFY_API_KEY
        : STORAGE_KEYS.REPORTS_API_KEY;
    return setStoredValue(storageKey, key);
}

/**
 * Get draft data (title and content)
 */
function getDraftData() {
    return {
        title: getStoredValue(STORAGE_KEYS.DRAFT_TITLE),
        content: getStoredValue(STORAGE_KEYS.DRAFT_CONTENT)
    };
}

/**
 * Set draft data
 */
function setDraftData(title, content) {
    setStoredValue(STORAGE_KEYS.DRAFT_TITLE, title);
    setStoredValue(STORAGE_KEYS.DRAFT_CONTENT, content);
}

/**
 * Clear draft data
 */
function clearDraftData() {
    clearStoredValues(STORAGE_KEYS.DRAFT_TITLE, STORAGE_KEYS.DRAFT_CONTENT);
}

/**
 * Logout user: clear all auth-related storage
 */
async function logout() {
    
    clearStoredValues(
        STORAGE_KEYS.AUTH_TOKEN,
        STORAGE_KEYS.USER_PROFILE,
        STORAGE_KEYS.PENDING_LOGIN
    );
    const res = await fetch(CONFIG.AUTH_LOGOUT, {
        method: 'GET',
        headers: {
            'accept': 'application/json',
            'x-api-key': STORAGE_KEYS.REPORTS_API_KEY
        }
    });

    console.log('Logout response:', res);
    const data = await res.text();

    if (!res.ok || !data || data.ok !== true) {
        console.error(data?.message);
    }
}
