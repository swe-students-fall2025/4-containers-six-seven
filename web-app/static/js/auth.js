/**
 * Authentication utility functions for the receipt scanner app.
 */

// Store current user info
let currentUser = null;

/**
 * Check if user is authenticated by calling /api/auth/me
 * @returns {Promise<Object|null>} User object if authenticated, null otherwise
 */
async function checkAuthStatus() {
  try {
    const response = await fetch('/api/auth/me', {
      method: 'GET',
      credentials: 'include' // Include cookies for session
    });
    
    if (response.ok) {
      const user = await response.json();
      currentUser = user;
      return user;
    } else if (response.status === 401) {
      // 401 is expected when user is not logged in - not an error
      currentUser = null;
      return null;
    } else {
      // Other errors (500, etc.) - log but don't throw
      console.warn('Auth check returned status:', response.status);
      currentUser = null;
      return null;
    }
  } catch (error) {
    // Network errors only - don't log 401 as error
    if (error.name !== 'TypeError') {
      console.error('Error checking auth status:', error);
    }
    currentUser = null;
    return null;
  }
}

/**
 * Redirect to login page with optional return URL
 * @param {string} returnUrl - URL to return to after login (optional)
 */
function redirectToLogin(returnUrl = null) {
  const url = returnUrl 
    ? `/api/auth/login?next=${encodeURIComponent(returnUrl)}`
    : '/api/auth/login';
  window.location.href = url;
}

/**
 * Handle 401 Unauthorized responses
 * Redirects to login page and stores intended destination
 * @param {string} intendedUrl - URL user was trying to access
 */
function handleUnauthorized(intendedUrl = null) {
  if (intendedUrl) {
    redirectToLogin(intendedUrl);
  } else {
    redirectToLogin(window.location.pathname);
  }
}

/**
 * Check if user is authenticated, redirect to login if not
 * @param {Function} callback - Function to call if authenticated
 * @param {string} redirectUrl - URL to redirect to after login (optional)
 */
async function requireAuth(callback = null, redirectUrl = null) {
  const user = await checkAuthStatus();
  if (user) {
    if (callback) {
      callback(user);
    }
    return user;
  } else {
    handleUnauthorized(redirectUrl || window.location.pathname);
    return null;
  }
}

/**
 * Logout user and redirect to home
 */
async function logout() {
  try {
    const response = await fetch('/api/auth/logout', {
      method: 'POST',
      credentials: 'include'
    });
    
    if (response.ok) {
      currentUser = null;
      window.location.href = '/';
    } else {
      console.error('Logout failed');
    }
  } catch (error) {
    console.error('Logout error:', error);
  }
}

/**
 * Update UI elements based on authentication status
 * @param {Object} user - User object or null
 */
function updateAuthUI(user) {
  // This will be called from pages that need to update their UI
  // Each page can implement its own UI updates
  if (user) {
    // User is logged in
    const authElements = document.querySelectorAll('[data-auth="required"]');
    authElements.forEach(el => {
      el.style.display = '';
    });
    
    const unauthElements = document.querySelectorAll('[data-auth="unauthorized"]');
    unauthElements.forEach(el => {
      el.style.display = 'none';
    });
  } else {
    // User is not logged in
    const authElements = document.querySelectorAll('[data-auth="required"]');
    authElements.forEach(el => {
      el.style.display = 'none';
    });
    
    const unauthElements = document.querySelectorAll('[data-auth="unauthorized"]');
    unauthElements.forEach(el => {
      el.style.display = '';
    });
  }
}

