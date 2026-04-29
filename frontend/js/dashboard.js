/* ============================================
   VantageTube AI – Dashboard Page Logic (API Integrated)
   dashboard.js
   ============================================ */

// Protect this page - require authentication
if (!requireAuth()) {
  // User will be redirected to login
}

// Global data storage
let dashboardData = {
  user: null,
  channels: [],
  videos: [],
  seoStats: null
};

// Initialize dashboard when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
  loadDashboard();
});

/**
 * Main function to load all dashboard data
 */
async function loadDashboard() {
  try {
    showLoading();
    
    // Load user data
    await loadUserData();
    
    // Load dashboard data in parallel
    await Promise.all([
      loadChannelsAndVideos(),
      loadSEOStats()
    ]);
    
    // Render all sections
    renderWelcomeMessage();
    renderStats();
    renderRecentVideos();
    renderActivityFeed();
    renderTrendingPreview();
    
    showContent();
  } catch (error) {
    console.error('Dashboard load error:', error);
    showError();
  }
}

/**
 * Load current user data
 */
async function loadUserData() {
  try {
    const user = await api.getCurrentUser();
    dashboardData.user = user;
    saveUserData(user);
    
    // Update sidebar user info
    updateSidebarUser(user);
  } catch (error) {
    console.error('Failed to load user:', error);
    throw error;
  }
}

/**
 * Load YouTube channels and videos
 */
async function loadChannelsAndVideos() {
  try {
    // Get connected channels
    const channels = await api.getYouTubeChannels();
    dashboardData.channels = channels;
    
    // If user has channels, get videos from first channel
    if (channels && channels.length > 0) {
      const firstChannel = channels[0];
      const videos = await api.getChannelVideos(firstChannel.id, 10);
      dashboardData.videos = videos;
    }
  } catch (error) {
    console.error('Failed to load channels/videos:', error);
    // Don't throw - dashboard can work without YouTube data
    dashboardData.channels = [];
    dashboardData.videos = [];
  }
}

/**
 * Load SEO statistics
 */
async function loadSEOStats() {
  try {
    const stats = await api.getSEODashboardStats();
    dashboardData.seoStats = stats;
  } catch (error) {
    console.error('Failed to load SEO stats:', error);
    // Don't throw - dashboard can work without SEO stats
    dashboardData.seoStats = null;
  }
}

/**
 * Update sidebar user information
 */
function updateSidebarUser(user) {
  // Update user name
  const userNameEl = document.querySelector('.sidebar-user .user-name');
  if (userNameEl) {
    userNameEl.textContent = user.full_name || user.email;
  }
  
  // Update avatar
  const avatarEl = document.querySelector('.sidebar-user .avatar');
  if (avatarEl) {
    if (user.avatar_url) {
      avatarEl.style.backgroundImage = `url(${user.avatar_url})`;
      avatarEl.style.backgroundSize = 'cover';
      avatarEl.textContent = '';
    } else {
      // Show initials
      const initials = user.full_name 
        ? user.full_name.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2)
        : user.email[0].toUpperCase();
      avatarEl.textContent = initials;
    }
  }
}

/**
 * Render welcome message with user's name
 */
function renderWelcomeMessage() {
  const welcomeEl = document.getElementById('welcomeMessage');
  if (!welcomeEl || !dashboardData.user) return;
  
  const hour = new Date().getHours();
  let greeting = 'Good morning';
  if (hour >= 12 && hour < 18) greeting = 'Good afternoon';
  if (hour >= 18) greeting = 'Good evening';
  
  const firstName = dashboardData.user.full_name 
    ? dashboardData.user.full_name.split(' ')[0]
    : dashboardData.user.email.split('@')[0];
  
  welcomeEl.textContent = `${greeting}, ${firstName}! 👋`;
}

/**
 * Render stats cards
 */
function renderStats() {
  const grid = document.getElementById('statsGrid');
  if (!grid) return;
  
  const { channels, videos, seoStats } = dashboardData;
  
  // Calculate stats
  const totalSubscribers = channels.reduce((sum, ch) => sum + (ch.subscriber_count || 0), 0);
  const totalViews = channels.reduce((sum, ch) => sum + (ch.view_count || 0), 0);
  const avgSeoScore = seoStats?.average_score || 0;
  const analyzedVideos = seoStats?.analyzed_videos || 0;
  
  const stats = [
    { 
      label: 'Subscribers', 
      value: formatNumber(totalSubscribers), 
      change: channels.length > 0 ? `${channels.length} channel${channels.length !== 1 ? 's' : ''} connected` : 'No channels yet',
      trend: channels.length > 0 ? 'up' : 'neutral',
      icon: '👥', 
      color: 'rgba(108,99,255,0.12)' 
    },
    { 
      label: 'Total Views', 
      value: formatNumber(totalViews), 
      change: videos.length > 0 ? `${videos.length} videos` : 'No videos yet',
      trend: videos.length > 0 ? 'up' : 'neutral',
      icon: '👁️', 
      color: 'rgba(59,130,246,0.12)' 
    },
    { 
      label: 'Avg. SEO Score', 
      value: avgSeoScore > 0 ? Math.round(avgSeoScore) : '--', 
      change: analyzedVideos > 0 ? `${analyzedVideos} analyzed` : 'No analysis yet',
      trend: avgSeoScore >= 70 ? 'up' : avgSeoScore > 0 ? 'neutral' : 'neutral',
      icon: '📊', 
      color: 'rgba(16,185,129,0.12)' 
    },
    { 
      label: 'Videos Analyzed', 
      value: analyzedVideos, 
      change: analyzedVideos > 0 ? 'View reports' : 'Start analyzing',
      trend: analyzedVideos > 0 ? 'up' : 'neutral',
      icon: '🎬', 
      color: 'rgba(245,158,11,0.12)' 
    },
  ];
  
  grid.innerHTML = stats.map(s => `
    <div class="stat-card">
      <div class="stat-icon" style="background:${s.color};">${s.icon}</div>
      <div class="stat-value">${s.value}</div>
      <div class="stat-label">${s.label}</div>
      <div class="stat-change ${s.trend}">
        ${s.trend === 'up' ? '↑' : s.trend === 'down' ? '↓' : '•'} ${s.change}
      </div>
    </div>
  `).join('');
}

/**
 * Render recent videos table
 */
function renderRecentVideos() {
  const tbody = document.getElementById('recentVideosBody');
  if (!tbody) return;
  
  const { videos } = dashboardData;
  
  if (!videos || videos.length === 0) {
    tbody.innerHTML = `
      <tr>
        <td colspan="6" style="text-align: center; padding: 40px; color: var(--text-muted);">
          <div style="font-size: 3rem; margin-bottom: 10px;">📺</div>
          <p>No videos yet</p>
          <p style="font-size: 0.9rem; margin-top: 10px;">
            <a href="channel.html" class="btn btn-primary btn-sm">Connect YouTube Channel</a>
          </p>
        </td>
      </tr>
    `;
    return;
  }
  
  // Show first 5 videos
  const recentVideos = videos.slice(0, 5);
  
  tbody.innerHTML = recentVideos.map(v => {
    const seoScore = v.seo_score || 0;
    const scoreClass = getSeoClass(seoScore);
    const scoreColor = getSeoColor(seoScore);
    const pct = seoScore + '%';
    
    return `
      <tr>
        <td>
          <div class="video-thumb-cell">
            <div class="video-thumb" style="background-image: url('${v.thumbnail_url || ''}'); background-size: cover; background-position: center;">
              ${!v.thumbnail_url ? '🎬' : ''}
            </div>
            <span class="video-title-text" title="${v.title}">${truncate(v.title, 60)}</span>
          </div>
        </td>
        <td>${formatNumber(v.view_count || 0)}</td>
        <td>${formatNumber(v.like_count || 0)}</td>
        <td>
          <div class="seo-score-bar">
            <div class="score-bar-track">
              <div class="score-bar-fill ${scoreClass}" style="width:${pct};"></div>
            </div>
            <span class="score-value" style="color:${scoreColor};">${seoScore || '--'}</span>
          </div>
        </td>
        <td class="text-muted">${formatDate(v.published_at)}</td>
        <td>
          <a href="analyzer.html?video=${v.id}" class="btn btn-ghost btn-sm">Analyze</a>
        </td>
      </tr>
    `;
  }).join('');
}

/**
 * Render activity feed
 */
function renderActivityFeed() {
  const feed = document.getElementById('activityFeed');
  if (!feed) return;
  
  const { videos, seoStats, channels } = dashboardData;
  
  // Generate activity items based on real data
  const activities = [];
  
  // Channel connection activity
  if (channels && channels.length > 0) {
    channels.forEach(ch => {
      activities.push({
        icon: '📺',
        color: 'rgba(108,99,255,0.12)',
        text: `Connected channel: ${ch.title}`,
        time: formatTimeAgo(ch.connected_at || new Date())
      });
    });
  }
  
  // Video analysis activity
  if (seoStats && seoStats.analyzed_videos > 0) {
    activities.push({
      icon: '📊',
      color: 'rgba(16,185,129,0.12)',
      text: `Analyzed ${seoStats.analyzed_videos} video${seoStats.analyzed_videos !== 1 ? 's' : ''}`,
      time: 'Recently'
    });
  }
  
  // Recent videos
  if (videos && videos.length > 0) {
    const latestVideo = videos[0];
    activities.push({
      icon: '🎬',
      color: 'rgba(59,130,246,0.12)',
      text: `New video: ${truncate(latestVideo.title, 40)}`,
      time: formatTimeAgo(latestVideo.published_at)
    });
  }
  
  // Default message if no activity
  if (activities.length === 0) {
    feed.innerHTML = `
      <div style="text-align: center; padding: 40px; color: var(--text-muted);">
        <p>No recent activity</p>
        <p style="font-size: 0.9rem; margin-top: 10px;">Start by connecting your YouTube channel</p>
      </div>
    `;
    return;
  }
  
  feed.innerHTML = activities.slice(0, 5).map(item => `
    <div class="activity-item">
      <div class="activity-icon" style="background:${item.color};">${item.icon}</div>
      <div class="activity-content">
        <div class="activity-text">${item.text}</div>
        <div class="activity-time">${item.time}</div>
      </div>
    </div>
  `).join('');
}

/**
 * Render trending preview
 */
function renderTrendingPreview() {
  const container = document.getElementById('trendingPreview');
  if (!container) return;
  
  // Show placeholder for now (will be populated when trending data is available)
  container.innerHTML = `
    <div style="text-align: center; padding: 40px; color: var(--text-muted);">
      <div style="font-size: 3rem; margin-bottom: 10px;">🔥</div>
      <p>Trending topics coming soon</p>
      <p style="font-size: 0.9rem; margin-top: 10px;">
        <a href="trending.html" class="btn btn-primary btn-sm">Explore Trending</a>
      </p>
    </div>
  `;
}

// ==================== Helper Functions ====================

/**
 * Format large numbers (1000 -> 1K, 1000000 -> 1M)
 */
function formatNumber(num) {
  if (num >= 1000000) {
    return (num / 1000000).toFixed(1) + 'M';
  }
  if (num >= 1000) {
    return (num / 1000).toFixed(1) + 'K';
  }
  return num.toString();
}

/**
 * Format date to relative time or short date
 */
function formatDate(dateString) {
  if (!dateString) return '--';
  
  const date = new Date(dateString);
  const now = new Date();
  const diffDays = Math.floor((now - date) / (1000 * 60 * 60 * 24));
  
  if (diffDays === 0) return 'Today';
  if (diffDays === 1) return 'Yesterday';
  if (diffDays < 7) return `${diffDays} days ago`;
  if (diffDays < 30) return `${Math.floor(diffDays / 7)} weeks ago`;
  if (diffDays < 365) return `${Math.floor(diffDays / 30)} months ago`;
  
  return date.toLocaleDateString();
}

/**
 * Format time ago (e.g., "2 hours ago")
 */
function formatTimeAgo(dateString) {
  if (!dateString) return 'Recently';
  
  const date = new Date(dateString);
  const now = new Date();
  const diffMs = now - date;
  const diffMins = Math.floor(diffMs / (1000 * 60));
  const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));
  
  if (diffMins < 1) return 'Just now';
  if (diffMins < 60) return `${diffMins} min${diffMins !== 1 ? 's' : ''} ago`;
  if (diffHours < 24) return `${diffHours} hour${diffHours !== 1 ? 's' : ''} ago`;
  if (diffDays < 7) return `${diffDays} day${diffDays !== 1 ? 's' : ''} ago`;
  
  return formatDate(dateString);
}

/**
 * Truncate text to specified length
 */
function truncate(text, maxLength) {
  if (!text) return '';
  if (text.length <= maxLength) return text;
  return text.substring(0, maxLength) + '...';
}

/**
 * Get SEO score class (for color coding)
 */
function getSeoClass(score) {
  if (score >= 80) return 'excellent';
  if (score >= 60) return 'good';
  if (score >= 40) return 'fair';
  return 'poor';
}

/**
 * Get SEO score color
 */
function getSeoColor(score) {
  if (score >= 80) return 'var(--success)';
  if (score >= 60) return 'var(--primary)';
  if (score >= 40) return 'var(--warning)';
  return 'var(--danger)';
}

// ==================== UI State Functions ====================

/**
 * Show loading state
 */
function showLoading() {
  document.getElementById('loadingState').style.display = 'block';
  document.getElementById('errorState').style.display = 'none';
  document.getElementById('dashboardContent').style.display = 'none';
}

/**
 * Show error state
 */
function showError() {
  document.getElementById('loadingState').style.display = 'none';
  document.getElementById('errorState').style.display = 'block';
  document.getElementById('dashboardContent').style.display = 'none';
}

/**
 * Show content (hide loading/error)
 */
function showContent() {
  document.getElementById('loadingState').style.display = 'none';
  document.getElementById('errorState').style.display = 'none';
  document.getElementById('dashboardContent').style.display = 'block';
}
