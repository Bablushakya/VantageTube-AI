/**
 * Cookie Manager for VantageTube AI
 * Handles secure cookie storage for authentication and user data
 */

class CookieManager {
    /**
     * Set a cookie
     */
    static setCookie(name, value, options = {}) {
        const {
            maxAge = 30 * 60 * 60, // 30 hours default
            path = '/',
            secure = window.location.protocol === 'https:',
            sameSite = 'Lax'
        } = options;

        let cookieString = `${encodeURIComponent(name)}=${encodeURIComponent(JSON.stringify(value))}`;
        
        if (maxAge) {
            cookieString += `; Max-Age=${maxAge}`;
        }
        
        cookieString += `; Path=${path}`;
        
        if (secure) {
            cookieString += '; Secure';
        }
        
        cookieString += `; SameSite=${sameSite}`;

        document.cookie = cookieString;
    }

    /**
     * Get a cookie
     */
    static getCookie(name) {
        const nameEQ = encodeURIComponent(name) + '=';
        const cookies = document.cookie.split(';');
        
        for (let cookie of cookies) {
            cookie = cookie.trim();
            if (cookie.startsWith(nameEQ)) {
                try {
                    const value = cookie.substring(nameEQ.length);
                    return JSON.parse(decodeURIComponent(value));
                } catch (e) {
                    return decodeURIComponent(value);
                }
            }
        }
        
        return null;
    }

    /**
     * Delete a cookie
     */
    static deleteCookie(name) {
        this.setCookie(name, '', { maxAge: -1 });
    }

    /**
     * Check if cookie exists
     */
    static hasCookie(name) {
        return this.getCookie(name) !== null;
    }

    /**
     * Get all cookies
     */
    static getAllCookies() {
        const cookies = {};
        document.cookie.split(';').forEach(cookie => {
            const [name, value] = cookie.trim().split('=');
            if (name) {
                try {
                    cookies[decodeURIComponent(name)] = JSON.parse(decodeURIComponent(value));
                } catch (e) {
                    cookies[decodeURIComponent(name)] = decodeURIComponent(value);
                }
            }
        });
        return cookies;
    }

    /**
     * Clear all cookies
     */
    static clearAllCookies() {
        document.cookie.split(';').forEach(cookie => {
            const name = cookie.split('=')[0].trim();
            if (name) {
                this.deleteCookie(name);
            }
        });
    }
}

// Export for use in other files
if (typeof module !== 'undefined' && module.exports) {
    module.exports = CookieManager;
}
