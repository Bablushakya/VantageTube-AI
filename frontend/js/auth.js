/**
 * Authentication Service for VantageTube AI
 * Handles user authentication, registration, and session management
 */

// ==================== Authentication State ====================

/**
 * Check if user is authenticated
 */
function isAuthenticated() {
    const token = localStorage.getItem('auth_token');
    return token !== null && token !== '';
}

/**
 * Get current user data from localStorage
 */
function getCurrentUserData() {
    const userData = localStorage.getItem('user_data');
    return userData ? JSON.parse(userData) : null;
}

/**
 * Save user data to localStorage
 */
function saveUserData(user) {
    localStorage.setItem('user_data', JSON.stringify(user));
}

/**
 * Clear all authentication data
 */
function clearAuthData() {
    localStorage.removeItem('auth_token');
    localStorage.removeItem('user_data');
}

// ==================== Protected Routes ====================

/**
 * Protect page - redirect to login if not authenticated
 * Call this at the top of protected pages
 */
function requireAuth() {
    if (!isAuthenticated()) {
        // Save current page to redirect back after login
        localStorage.setItem('redirect_after_login', window.location.pathname);
        // Use absolute path from root
        window.location.href = '/auth.html';
        return false;
    }
    return true;
}

/**
 * Redirect if already authenticated
 * Call this on login/register pages
 */
function redirectIfAuthenticated() {
    if (isAuthenticated()) {
        const redirectTo = localStorage.getItem('redirect_after_login') || '/pages/dashboard.html';
        localStorage.removeItem('redirect_after_login');
        window.location.href = redirectTo;
        return true;
    }
    return false;
}

// ==================== Authentication Functions ====================

/**
 * Register new user
 */
async function register(email, password, firstName, lastName, displayName) {
    try {
        showLoading('register-btn', 'Creating account...');
        
        const response = await api.register(email, password, firstName, lastName, displayName);
        
        // Save token and user data
        api.setToken(response.access_token);
        saveUserData(response.user);
        
        // Show success message
        showSuccess('Account created successfully! Redirecting...');
        
        // Redirect to dashboard
        // Use absolute path from root (works from any page)
        setTimeout(() => {
            window.location.href = '/pages/dashboard.html';
        }, 1000);
        
        return response;
    } catch (error) {
        hideLoading('register-btn', 'Create Account');
        showError(error.message || 'Registration failed. Please try again.');
        throw error;
    }
}

/**
 * Login user
 */
async function login(email, password) {
    try {
        showLoading('login-btn', 'Logging in...');
        
        const response = await api.login(email, password);
        console.log('Login response:', response);
        // Save token and user data
        api.setToken(response.access_token);
        saveUserData(response.user);
        
        // Show success message
        showSuccess('Login successful! Redirecting...');
        
        // Redirect to dashboard or saved page
        // Use absolute path from root (works from any page)
        setTimeout(() => {
            const redirectTo = localStorage.getItem('redirect_after_login') || '/pages/dashboard.html';
            localStorage.removeItem('redirect_after_login');
            window.location.href = redirectTo;
        }, 1000);
        
        return response;
    } catch (error) {
        hideLoading('login-btn', 'Login');
        showError(error.message || 'Login failed. Please check your credentials.');
        throw error;
    }
}

/**
 * Logout user
 */
async function logout() {
    try {
        // Call logout API
        await api.logout();
    } catch (error) {
        console.error('Logout API error:', error);
    } finally {
        // Clear local data regardless of API response
        clearAuthData();
        
        // Redirect to landing page
        window.location.href = '/auth.html';
    }
}

/**
 * Load current user profile
 */
async function loadCurrentUser() {
    try {
        const user = await api.getCurrentUser();
        saveUserData(user);
        return user;
    } catch (error) {
        console.error('Failed to load user:', error);
        // If token is invalid, clear auth and redirect
        if (error.message.includes('Authentication required')) {
            clearAuthData();
            window.location.href = '/auth.html';
        }
        throw error;
    }
}

// ==================== UI Helper Functions ====================

/**
 * Show loading state on button
 */
function showLoading(buttonId, text = 'Loading...') {
    const button = document.getElementById(buttonId);
    if (button) {
        button.disabled = true;
        button.dataset.originalText = button.textContent;
        button.innerHTML = `<span class="spinner"></span> ${text}`;
    }
}

/**
 * Hide loading state on button
 */
function hideLoading(buttonId, text = null) {
    const button = document.getElementById(buttonId);
    if (button) {
        button.disabled = false;
        button.textContent = text || button.dataset.originalText || 'Submit';
    }
}

/**
 * Show error message
 */
function showError(message) {
    // Try to find error container
    const errorContainer = document.getElementById('error-message') || 
                          document.getElementById('auth-error');
    
    if (errorContainer) {
        errorContainer.textContent = message;
        errorContainer.style.display = 'block';
        errorContainer.className = 'error-message';
        
        // Auto-hide after 5 seconds
        setTimeout(() => {
            errorContainer.style.display = 'none';
        }, 5000);
    } else {
        // Fallback to alert
        alert('Error: ' + message);
    }
}

/**
 * Show success message
 */
function showSuccess(message) {
    // Try to find success container
    const successContainer = document.getElementById('success-message') || 
                            document.getElementById('auth-success');
    
    if (successContainer) {
        successContainer.textContent = message;
        successContainer.style.display = 'block';
        successContainer.className = 'success-message';
        
        // Auto-hide after 3 seconds
        setTimeout(() => {
            successContainer.style.display = 'none';
        }, 3000);
    } else {
        // Create temporary success message
        const div = document.createElement('div');
        div.className = 'success-message';
        div.textContent = message;
        div.style.cssText = 'position: fixed; top: 20px; right: 20px; background: #10b981; color: white; padding: 15px 20px; border-radius: 8px; z-index: 10000;';
        document.body.appendChild(div);
        
        setTimeout(() => {
            div.remove();
        }, 3000);
    }
}

/**
 * Clear error message
 */
function clearError() {
    const errorContainer = document.getElementById('error-message') || 
                          document.getElementById('auth-error');
    if (errorContainer) {
        errorContainer.style.display = 'none';
    }
}

// ==================== Form Validation ====================

/**
 * Validate email format
 */
function isValidEmail(email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
}

/**
 * Validate password strength
 */
function isValidPassword(password) {
    // At least 8 characters
    return password.length >= 8;
}

/**
 * Validate registration form
 */
function validateRegistrationForm(email, password, confirmPassword, fullName) {
    if (!fullName || fullName.trim().length < 2) {
        throw new Error('Please enter your full name (at least 2 characters)');
    }
    
    if (!isValidEmail(email)) {
        throw new Error('Please enter a valid email address');
    }
    
    if (!isValidPassword(password)) {
        throw new Error('Password must be at least 8 characters long');
    }
    
    if (password !== confirmPassword) {
        throw new Error('Passwords do not match');
    }
    
    return true;
}

/**
 * Validate login form
 */
function validateLoginForm(email, password) {
    if (!isValidEmail(email)) {
        throw new Error('Please enter a valid email address');
    }
    
    if (!password || password.length < 1) {
        throw new Error('Please enter your password');
    }
    
    return true;
}

// ==================== User Display Functions ====================

/**
 * Display user info in navigation
 */
function displayUserInfo() {
    const user = getCurrentUserData();
    if (!user) return;
    
    // Update user name displays
    const userNameElements = document.querySelectorAll('.user-name');
    userNameElements.forEach(el => {
        el.textContent = user.full_name || user.email;
    });
    
    // Update user email displays
    const userEmailElements = document.querySelectorAll('.user-email');
    userEmailElements.forEach(el => {
        el.textContent = user.email;
    });
    
    // Update avatar displays
    const avatarElements = document.querySelectorAll('.user-avatar');
    avatarElements.forEach(el => {
        if (user.avatar_url) {
            el.src = user.avatar_url;
        } else {
            // Show initials
            const initials = user.full_name 
                ? user.full_name.split(' ').map(n => n[0]).join('').toUpperCase()
                : user.email[0].toUpperCase();
            el.alt = initials;
            el.textContent = initials;
        }
    });
}

/**
 * Initialize authentication on page load
 */
function initAuth() {
    // Display user info if authenticated
    if (isAuthenticated()) {
        displayUserInfo();
    }
    
    // Add logout button handlers
    const logoutButtons = document.querySelectorAll('.logout-btn, [data-action="logout"]');
    logoutButtons.forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.preventDefault();
            logout();
        });
    });
}

// Initialize auth when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initAuth);
} else {
    initAuth();
}

// Export functions for use in other files
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        isAuthenticated,
        getCurrentUserData,
        saveUserData,
        clearAuthData,
        requireAuth,
        redirectIfAuthenticated,
        register,
        login,
        logout,
        loadCurrentUser,
        showError,
        showSuccess,
        clearError,
        displayUserInfo
    };
}
