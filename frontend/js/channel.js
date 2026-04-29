/**
 * Channel Overview Page Logic with API Integration
 * Handles channel data display, video list, and sync functionality
 */

// Protect this page - require authentication
if (!requireAuth()) {
  // User will be redirected to login
}

// Global state
let currentChannel = null;
let channelVideos = [];
let currentSort = 'latest';

// Initialize channel page
document.addEventListener('DOMContentLoaded', () => {
  loadChannelData();
});

/**
 * Load channel data from API
 */
async function loadChannelData() {
  try {
    showLoadingState();
    
    // Get connected channels
    const channels = await api.getYouTubeChannels();
    
    if (!channels || channels.length === 0) {
      showNoChannelState();
      return;
    }
    
    // Use first channel
    currentChannel = channels[0];
    
    // Render channel header
    renderChannelHeader(currentChannel);
    
    // Load channel videos
    await loadChannelVideos(currentChannel.id);
    
    // Load user for sidebar
    const user = await api.getCurrentUser();
    updateSidebar(user);
    
    hideLoadingState();
  } catch (error) {
    console.error('Failed to load channel data:', error);
    showError('Failed to load channel data. Please try again.');
    hideLoadingState();
  }
}

/**
 * Render channel header
 */
function renderChannelHeader(channel) {
  // Update avatar
  const avatarEl = document.querySelector('.channel-avatar');
  if (channel.thumbnail_url) {
    avatarEl.style.backgroundImage = `url(${channel.thumbnail_url})`;
    avatarEl.style.backgroundSize = 'cover';
    avatarEl.style.backgroundPosition = 'center';
    avatarEl.textContent = '';
  } else {
    const initials = channel.title.split(' ').map(w => w[0]).join('').toUpperCase().slice(0, 2);
    avatarEl.textContent = initials;
  }
  
  // Update channel info
  document.querySelector('.channel-info h2').textContent = channel.title;
  document.querySelector('.channel-handle').textContent = `@${channel.custom_url || channel.title.replace(/\s+/g, '').toLowerCase()}`;
  
  // Update meta items
  const metaContainer = document.querySelector('.channel-meta');
  metaContainer.innerHTML = `
    <div class="channel-meta-item">👥 <strong>${formatNumber(channel.subscriber_count || 0)}</strong> subscribers</div>
    <div class="channel-meta-item">🎬 <strong>${formatNumber(channel.video_count || 0)}</strong> videos</div>
    <div class="channel-meta-item">👁️ <strong>${formatNumber(channel.view_count || 0)}</strong> total views</div>
    <div class="channel-meta-item">📅 Joined <strong>${formatDate(channel.published_at)}</strong></div>
    <div class="channel-meta-item">🌍 <strong>${channel.country || 'Unknown'}</strong></div>
  `;
  
  // Update stats cards
  updateStatsCards(channel);
}

/**
 * Update stats cards
 */
function updateStatsCards(channel) {
  const statsGrid = document.querySelector('.stats-grid');
  if (!statsGrid) return;
  
  // Calculate average SEO score from videos
  const avgSeoScore = channelVideos.length > 0
    ? Math.round(channelVideos.reduce((sum, v) => sum + (v.seo_score || 0), 0) / channelVideos.length)
    : 0;
  
  // Calculate engagement rate (likes / views * 100)
  const totalLikes = channelVideos.reduce((sum, v) => sum + (v.like_count || 0), 0);
  const totalViews = channelVideos.reduce((sum, v) => sum + (v.view_count || 0), 0);
  const engagementRate = totalViews > 0 ? ((totalLikes / totalViews) * 100).toFixed(1) : 0;
  
  statsGrid.innerHTML = `
    <div class="stat-card">
      <div class="stat-icon" style="background:rgba(108,99,255,0.12);">👥</div>
      <div class="stat-value">${formatNumber(channel.subscriber_count || 0)}</div>
      <div class="stat-label">Subscribers</div>
      <div class="stat-change">Total subscribers</div>
    </div>
    <div class="stat-card">
      <div class="stat-icon" style="background:rgba(59,130,246,0.12);">👁️</div>
      <div class="stat-value">${formatNumber(channel.view_count || 0)}</div>
      <div class="stat-label">Total Views</div>
      <div class="stat-change">All-time views</div>
    </div>
    <div class="stat-card">
      <div class="stat-icon" style="background:rgba(16,185,129,0.12);">📊</div>
      <div class="stat-value">${avgSeoScore}/100</div>
      <div class="stat-label">Avg. SEO Score</div>
      <div class="stat-change">${channelVideos.length} videos analyzed</div>
    </div>
    <div class="stat-card">
      <div class="stat-icon" style="background:rgba(245,158,11,0.12);">💬</div>
      <div class="stat-value">${engagementRate}%</div>
      <div class="stat-label">Avg. Engagement</div>
      <div class="stat-change">Likes to views ratio</div>
    </div>
  `;
}

/**
 * Load channel videos
 */
async function loadChannelVideos(channelId) {
  try {
    channelVideos = await api.getChannelVideos(channelId, 100);
    
    // Update video count in header
    const cardTitle = document.querySelector('.card-title');
    if (cardTitle) {
      cardTitle.textContent = `All Videos (${channelVideos.length})`;
    }
    
    // Render videos
    renderVideos(channelVideos);
    
    // Update stats with video data
    updateStatsCards(currentChannel);
  } catch (error) {
    console.error('Failed to load videos:', error);
    showToast('Failed to load videos', 'error');
  }
}

/**
 * Render videos grid
 */
function renderVideos(videos) {
  const grid = document.getElementById('videosGrid');
  if (!grid) return;
  
  if (videos.length === 0) {
    grid.innerHTML = `
      <div style="grid-column: 1/-1; text-align: center; padding: 60px 20px; color: var(--text-muted);">
        <div style="font-size: 3rem; margin-bottom: 16px;">🎬</div>
        <h3 style="margin-bottom: 8px;">No videos found</h3>
        <p>Sync your channel to see your videos here.</p>
        <button class="btn btn-primary" onclick="syncChannel()" style="margin-top: 16px;">
          🔄 Sync Channel
        </button>
      </div>
    `;
    return;
  }
  
  grid.innerHTML = videos.map(video => {
    const seoScore = video.seo_score || 0;
    const scoreColor = getSeoColor(seoScore);
    const thumbnail = video.thumbnail_url || 'https://via.placeholder.com/320x180?text=No+Thumbnail';
    
    return `
      <div class="video-card" onclick="viewVideo('${video.id}')">
        <div class="video-thumbnail" style="background-image: url('${thumbnail}'); background-size: cover; background-position: center;">
          <div class="play-overlay">
            <div class="play-btn">▶</div>
          </div>
          <span class="video-duration">${formatDuration(video.duration)}</span>
        </div>
        <div class="video-card-body">
          <div class="video-card-title">${escapeHtml(video.title)}</div>
          <div class="video-card-meta">
            <span>👁️ ${formatNumber(video.view_count || 0)}</span>
            <span>👍 ${formatNumber(video.like_count || 0)}</span>
            <span style="font-weight:700;color:${scoreColor};">SEO: ${seoScore}</span>
          </div>
          <div style="font-size:0.72rem;color:var(--text-muted);margin-top:4px;">
            ${formatTimeAgo(video.published_at)}
          </div>
        </div>
      </div>
    `;
  }).join('');
}

/**
 * View video details (navigate to analyzer)
 */
function viewVideo(videoId) {
  window.location.href = `analyzer.html?video=${videoId}`;
}

/**
 * Sync channel data
 */
async function syncChannel() {
  if (!currentChannel) {
    showToast('No channel connected', 'error');
    return;
  }
  
  try {
    showToast('Syncing channel data...', 'info');
    
    // Sync videos from YouTube
    await api.syncChannelVideos(currentChannel.id);
    
    // Reload channel data
    await loadChannelData();
    
    showToast('✅ Channel synced successfully!', 'success');
  } catch (error) {
    console.error('Failed to sync channel:', error);
    showToast('Failed to sync channel. Please try again.', 'error');
  }
}

/**
 * Refresh channel data
 */
async function refreshChannel() {
  await loadChannelData();
  showToast('✅ Channel data refreshed!', 'success');
}

/**
 * Sort videos
 */
function sortVideos(sortBy) {
  currentSort = sortBy;
  
  let sorted = [...channelVideos];
  
  switch (sortBy) {
    case 'latest':
      sorted.sort((a, b) => new Date(b.published_at) - new Date(a.published_at));
      break;
    case 'views':
      sorted.sort((a, b) => (b.view_count || 0) - (a.view_count || 0));
      break;
    case 'seo':
      sorted.sort((a, b) => (b.seo_score || 0) - (a.seo_score || 0));
      break;
    case 'engagement':
      sorted.sort((a, b) => {
        const engA = (a.view_count || 0) > 0 ? (a.like_count || 0) / (a.view_count || 0) : 0;
        const engB = (b.view_count || 0) > 0 ? (b.like_count || 0) / (b.view_count || 0) : 0;
        return engB - engA;
      });
      break;
  }
  
  renderVideos(sorted);
}

/**
 * Show no channel state
 */
function showNoChannelState() {
  const mainContent = document.querySelector('.page-content');
  mainContent.innerHTML = `
    <div style="text-align: center; padding: 80px 20px;">
      <div style="font-size: 5rem; margin-bottom: 24px;">📺</div>
      <h2 style="margin-bottom: 12px;">No YouTube Channel Connected</h2>
      <p style="color: var(--text-muted); margin-bottom: 32px; max-width: 500px; margin-left: auto; margin-right: auto;">
        Connect your YouTube channel to view analytics, manage videos, and optimize your content with AI-powered insights.
      </p>
      <button class="btn btn-primary" onclick="connectChannel()">
        🔗 Connect YouTube Channel
      </button>
    </div>
  `;
}

/**
 * Connect YouTube channel
 */
async function connectChannel() {
  try {
    showToast('Redirecting to YouTube...', 'info');
    
    // Get OAuth URL
    const response = await api.getYouTubeAuthURL();
    
    // Redirect to OAuth URL
    window.location.href = response.authorization_url;
  } catch (error) {
    console.error('Failed to get OAuth URL:', error);
    showToast('Failed to connect channel. Please try again.', 'error');
  }
}

/**
 * Update sidebar with user data
 */
function updateSidebar(user) {
  const sidebarName = document.querySelector('.sidebar-user .user-name');
  const sidebarAvatar = document.querySelector('.sidebar-user .avatar');
  
  if (sidebarName) {
    sidebarName.textContent = user.full_name || user.email;
  }
  
  if (sidebarAvatar) {
    if (user.avatar_url) {
      sidebarAvatar.style.backgroundImage = `url(${user.avatar_url})`;
      sidebarAvatar.style.backgroundSize = 'cover';
      sidebarAvatar.textContent = '';
    } else {
      const initials = user.full_name 
        ? user.full_name.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2)
        : user.email[0].toUpperCase();
      sidebarAvatar.textContent = initials;
    }
  }
}

// ==================== Helper Functions ====================

/**
 * Format number with K/M suffix
 */
function formatNumber(num) {
  if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M';
  if (num >= 1000) return (num / 1000).toFixed(1) + 'K';
  return num.toString();
}

/**
 * Format date
 */
function formatDate(dateString) {
  if (!dateString) return 'Unknown';
  const date = new Date(dateString);
  return date.toLocaleDateString('en-US', { month: 'long', year: 'numeric' });
}

/**
 * Format time ago
 */
function formatTimeAgo(dateString) {
  if (!dateString) return 'Unknown';
  
  const date = new Date(dateString);
  const now = new Date();
  const seconds = Math.floor((now - date) / 1000);
  
  const intervals = {
    year: 31536000,
    month: 2592000,
    week: 604800,
    day: 86400,
    hour: 3600,
    minute: 60
  };
  
  for (const [unit, secondsInUnit] of Object.entries(intervals)) {
    const interval = Math.floor(seconds / secondsInUnit);
    if (interval >= 1) {
      return `${interval} ${unit}${interval > 1 ? 's' : ''} ago`;
    }
  }
  
  return 'Just now';
}

/**
 * Format duration (ISO 8601 to MM:SS)
 */
function formatDuration(duration) {
  if (!duration) return '0:00';
  
  // Parse ISO 8601 duration (PT1H2M3S)
  const match = duration.match(/PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?/);
  if (!match) return '0:00';
  
  const hours = parseInt(match[1] || 0);
  const minutes = parseInt(match[2] || 0);
  const seconds = parseInt(match[3] || 0);
  
  if (hours > 0) {
    return `${hours}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
  }
  return `${minutes}:${seconds.toString().padStart(2, '0')}`;
}

/**
 * Get SEO score color
 */
function getSeoColor(score) {
  if (score >= 80) return 'var(--success)';
  if (score >= 60) return 'var(--warning)';
  return 'var(--danger)';
}

/**
 * Escape HTML to prevent XSS
 */
function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

/**
 * Show loading state
 */
function showLoadingState() {
  const mainContent = document.querySelector('.page-content');
  if (mainContent) {
    mainContent.style.opacity = '0.6';
    mainContent.style.pointerEvents = 'none';
  }
}

/**
 * Hide loading state
 */
function hideLoadingState() {
  const mainContent = document.querySelector('.page-content');
  if (mainContent) {
    mainContent.style.opacity = '1';
    mainContent.style.pointerEvents = 'auto';
  }
}

/**
 * Show error message
 */
function showError(message) {
  showToast(message, 'error');
}
