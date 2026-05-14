/**
 * API Client for VantageTube AI
 * Handles all communication with the backend API
 */

class APIClient {
    constructor() {
        // Backend API base URL
        this.baseURL = 'http://localhost:8000/api';
        
        // Get token from localStorage
        this.token = localStorage.getItem('auth_token');
    }

    /**
     * Set authentication token
     */
    setToken(token) {
        this.token = token;
        if (token) {
            // Save to cookie instead of localStorage
            if (typeof CookieManager !== 'undefined') {
                CookieManager.setCookie('auth_token', token, {
                    maxAge: 30 * 60 * 60
                });
            }
            localStorage.setItem('auth_token', token); // Backward compatibility
        } else {
            localStorage.removeItem('auth_token');
            if (typeof CookieManager !== 'undefined') {
                CookieManager.deleteCookie('auth_token');
            }
        }
    }

    /**
     * Get authentication token
     */
    getToken() {
        // Try to get from cookie first
        if (typeof CookieManager !== 'undefined') {
            const cookieToken = CookieManager.getCookie('auth_token');
            if (cookieToken) {
                this.token = cookieToken;
                return cookieToken;
            }
        }
        
        // Fallback to localStorage
        return this.token || localStorage.getItem('auth_token');
    }

    /**
     * Clear authentication token
     */
    clearToken() {
        this.token = null;
        localStorage.removeItem('auth_token');
        localStorage.removeItem('user_data');
        if (typeof CookieManager !== 'undefined') {
            CookieManager.deleteCookie('auth_token');
            CookieManager.deleteCookie('user_data');
            CookieManager.deleteCookie('token_expires_at');
        }
    }

    /**
     * Make HTTP request to API
     */
    async request(endpoint, options = {}) {
        const url = `${this.baseURL}${endpoint}`;
        
        // Default headers
        const headers = {
            'Content-Type': 'application/json',
            ...options.headers
        };

        // Add authorization header if token exists
        const token = this.getToken();
        if (token) {
            headers['Authorization'] = `Bearer ${token}`;
        }

        // Merge options
        const config = {
            ...options,
            headers
        };

        try {
            const response = await fetch(url, config);
            
            // Handle 401 Unauthorized (token expired or invalid)
            if (response.status === 401) {
                console.log('Token expired or invalid, clearing auth data');
                // Clear token and redirect to login
                this.clearToken();
                if (typeof clearAuthData !== 'undefined') {
                    clearAuthData();
                }
                if (window.location.pathname !== '/auth.html' && window.location.pathname !== '/index.html') {
                    window.location.href = '/auth.html?reason=session_expired';
                }
                throw new Error('Session expired. Please login again.');
            }

            // Handle 403 Forbidden (permission denied)
            if (response.status === 403) {
                console.log('Access forbidden');
                throw new Error('Access denied. You do not have permission to access this resource.');
            }

            // Handle 429 Too Many Requests (quota exceeded)
            if (response.status === 429) {
                const data = await response.json();
                const retryAfter = parseInt(response.headers.get('Retry-After') || '60', 10);
                const error = new Error(data.detail || 'Quota exceeded. Please try again later.');
                error.status = 429;
                error.quotaExceeded = true;
                error.retryAfterSeconds = retryAfter;
                error.retryAfterMessage = data.message || `Please wait ${retryAfter} seconds before retrying.`;
                throw error;
            }

            // Parse JSON response
            const data = await response.json();

            // Handle non-2xx responses
            if (!response.ok) {
                const error = new Error(data.detail || data.message || 'Request failed');
                error.status = response.status;
                // Detect quota errors that may arrive as 500 due to backend wrapping
                const detail = (data.detail || data.message || '').toLowerCase();
                const isQuotaMsg = detail.includes('quota exceeded') ||
                                   detail.includes('quota') && detail.includes('429') ||
                                   detail.includes('resource_exhausted') ||
                                   detail.includes('free tier') ||
                                   detail.includes('rate limit');
                if (response.status === 500 && isQuotaMsg) {
                    const retryAfter = parseInt(response.headers.get('Retry-After') || '60', 10);
                    error.quotaExceeded = true;
                    error.retryAfterSeconds = retryAfter;
                    error.retryAfterMessage = `AI quota exceeded. Please wait ${retryAfter} seconds before retrying.`;
                }
                throw error;
            }

            return data;
        } catch (error) {
            // Network error or other issues
            if (error.message === 'Failed to fetch') {
                throw new Error('Cannot connect to server. Please ensure the backend is running.');
            }
            throw error;
        }
    }

    /**
     * GET request
     */
    async get(endpoint) {
        return this.request(endpoint, {
            method: 'GET'
        });
    }

    /**
     * POST request
     */
    async post(endpoint, data) {
        return this.request(endpoint, {
            method: 'POST',
            body: JSON.stringify(data)
        });
    }

    /**
     * PUT request
     */
    async put(endpoint, data) {
        return this.request(endpoint, {
            method: 'PUT',
            body: JSON.stringify(data)
        });
    }

    /**
     * DELETE request
     */
    async delete(endpoint) {
        return this.request(endpoint, {
            method: 'DELETE'
        });
    }

    /**
     * Upload file (multipart/form-data)
     */
    async upload(endpoint, formData) {
        const url = `${this.baseURL}${endpoint}`;
        
        const headers = {};
        const token = this.getToken();
        if (token) {
            headers['Authorization'] = `Bearer ${token}`;
        }

        try {
            const response = await fetch(url, {
                method: 'POST',
                headers,
                body: formData
            });

            if (response.status === 401) {
                this.clearToken();
                window.location.href = '/auth.html';
                throw new Error('Authentication required');
            }

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.detail || data.message || 'Upload failed');
            }

            return data;
        } catch (error) {
            if (error.message === 'Failed to fetch') {
                throw new Error('Cannot connect to server');
            }
            throw error;
        }
    }

    // ==================== Authentication Endpoints ====================

    /**
     * Register new user
     */
    async register(email, password, firstName, lastName, displayName) {
        return this.post('/auth/register', {
            email,
            password,
            confirm_password: password,  // Same as password
            first_name: firstName,
            last_name: lastName,
            display_name: displayName || `${firstName} ${lastName}`
        });
    }

    /**
     * Login user
     */
    async login(email, password) {
        return this.post('/auth/login', {
            email,
            password
        });
    }

    /**
     * Get current user
     */
    async getCurrentUser() {
        return this.get('/auth/me');
    }

    /**
     * Logout user
     */
    async logout() {
        try {
            await this.post('/auth/logout', {});
        } finally {
            this.clearToken();
        }
    }

    /**
     * Check authentication status
     */
    async checkAuth() {
        return this.get('/auth/check');
    }

    /**
     * Refresh access token
     */
    async refreshToken() {
        return this.post('/auth/refresh', {});
    }

    // ==================== User Profile Endpoints ====================

    /**
     * Get user profile
     */
    async getUserProfile() {
        return this.get('/users/me');
    }

    /**
     * Update user profile
     */
    async updateUserProfile(data) {
        return this.put('/users/me', data);
    }

    /**
     * Change password
     */
    async changePassword(currentPassword, newPassword, confirmPassword) {
        return this.post('/users/change-password', {
            current_password: currentPassword,
            new_password: newPassword,
            confirm_password: confirmPassword
        });
    }

    /**
     * Upload avatar
     */
    async uploadAvatar(file) {
        const formData = new FormData();
        formData.append('file', file);
        return this.upload('/users/avatar', formData);
    }

    /**
     * Delete avatar
     */
    async deleteAvatar() {
        return this.delete('/users/avatar');
    }

    /**
     * Get user settings
     */
    async getUserSettings() {
        return this.get('/users/settings');
    }

    /**
     * Update user settings
     */
    async updateUserSettings(settings) {
        return this.put('/users/settings', settings);
    }

    // ==================== YouTube Endpoints ====================

    /**
     * Get YouTube OAuth URL
     */
    async getYouTubeAuthURL() {
        return this.get('/youtube/oauth/authorize');
    }

    /**
     * Get connected YouTube channels
     */
    async getYouTubeChannels() {
        return this.get('/youtube/channels');
    }

    /**
     * Sync channel videos
     */
    async syncChannelVideos(channelId) {
        return this.post(`/youtube/channels/${channelId}/sync`, {});
    }

    /**
     * Get channel videos
     */
    async getChannelVideos(channelId, limit = 50) {
        return this.get(`/youtube/channels/${channelId}/videos?limit=${limit}`);
    }

    /**
     * Disconnect YouTube channel
     */
    async disconnectYouTubeChannel(channelId) {
        return this.delete(`/youtube/channels/${channelId}`);
    }

    // ==================== SEO Analysis Endpoints ====================

    /**
     * Analyze video SEO
     */
    async analyzeVideoSEO(videoId, forceReanalysis = false) {
        return this.post('/seo/analyze', {
            video_id: videoId,
            force_reanalysis: forceReanalysis
        });
    }

    /**
     * Get video SEO reports
     */
    async getVideoSEOReports(videoId) {
        return this.get(`/seo/videos/${videoId}/reports`);
    }

    /**
     * Get SEO dashboard stats
     */
    async getSEODashboardStats() {
        return this.get('/seo/dashboard/stats');
    }

    // ==================== AI Content Generation Endpoints ====================

    /**
     * Get quota information
     */
    async getQuotaInfo() {
        return this.get('/content/quota/info');
    }

    /**
     * Generate video analysis (titles + description + tags) in a single batch call.
     * Used by the Video Analyzer page.
     *
     * @param {Object} params
     * @param {string} params.topic       - Video topic / title (required)
     * @param {string[]} [params.keywords] - Target SEO keywords
     * @param {string} [params.tone]       - Content tone (default: "engaging")
     * @param {number} [params.count]      - Number of title options 1-10 (default: 5)
     * @param {string} [params.video_id]   - Database video ID for history tracking
     *
     * @returns {Promise<{titles, description, tags, cache_hit, gemini_calls_made, generated_at}>}
     */
    async generateVideoAnalysis(params) {
        return this.post('/content/generate/video-analysis', params);
    }

    /**
     * Generate video titles
     */
    async generateTitles(data) {
        return this.post('/content/generate/titles', data);
    }

    /**
     * Generate video description
     */
    async generateDescription(data) {
        return this.post('/content/generate/description', data);
    }

    /**
     * Generate video tags
     */
    async generateTags(data) {
        return this.post('/content/generate/tags', data);
    }

    /**
     * Generate thumbnail text
     */
    async generateThumbnailText(data) {
        return this.post('/content/generate/thumbnail-text', data);
    }

    /**
     * Get content generation history
     */
    async getContentHistory(contentType = null, limit = 50) {
        let endpoint = `/content/history?limit=${limit}`;
        if (contentType) {
            endpoint += `&content_type=${contentType}`;
        }
        return this.get(endpoint);
    }

    /**
     * Get content generation stats
     */
    async getContentStats() {
        return this.get('/content/stats');
    }

    /**
     * Delete generated content
     */
    async deleteGeneratedContent(contentId) {
        return this.delete(`/content/history/${contentId}`);
    }

    // ==================== Video Analytics Endpoints ====================

    /**
     * Get comprehensive video analytics data.
     * Fetches performance metrics, traffic sources, audience insights, etc.
     *
     * @param {string} videoId - Database video ID (not YouTube video ID)
     * @param {boolean} [forceRefresh=false] - Bypass cache if true
     * @returns {Promise<Object>} Analytics data
     */
    async getVideoAnalytics(videoId, forceRefresh = false) {
        let endpoint = `/videos/${videoId}/analytics`;
        if (forceRefresh) {
            endpoint += '?force_refresh=true';
        }
        return this.get(endpoint);
    }

    // ==================== Trending Topics Endpoints ====================

    /**
     * Fetch trending videos
     */
    async fetchTrendingVideos(region = 'US', categoryId = null, maxResults = 50) {
        return this.post('/trending/fetch', {
            region,
            category_id: categoryId,
            max_results: maxResults
        });
    }

    /**
     * Filter trending videos
     */
    async filterTrendingVideos(filters) {
        return this.post('/trending/filter', filters);
    }

    /**
     * Analyze trending video
     */
    async analyzeTrendingVideo(videoId, niche = null) {
        let endpoint = `/trending/videos/${videoId}/analyze`;
        if (niche) {
            endpoint += `?niche=${encodeURIComponent(niche)}`;
        }
        return this.get(endpoint);
    }

    /**
     * Get trending stats
     */
    async getTrendingStats(region = 'US') {
        return this.get(`/trending/stats?region=${region}`);
    }

    /**
     * Get trending dashboard
     */
    async getTrendingDashboard(region = 'US') {
        return this.get(`/trending/dashboard?region=${region}`);
    }

    /**
     * Get content opportunities
     */
    async getContentOpportunities(niche, region = 'US', limit = 5) {
        return this.get(`/trending/opportunities?niche=${encodeURIComponent(niche)}&region=${region}&limit=${limit}`);
    }

    /**
     * Get YouTube categories
     */
    async getYouTubeCategories() {
        return this.get('/trending/categories');
    }

    /**
     * Get supported regions
     */
    async getSupportedRegions() {
        return this.get('/trending/regions');
    }
}

// Create global API client instance
const api = new APIClient();

// Export for use in other files
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { api, APIClient };
}
