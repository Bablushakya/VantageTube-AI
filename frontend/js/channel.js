/**
 * Channel Overview Page Logic with API Integration
 * Handles channel data display, video list, and sync functionality
 * Features: lazy-load pagination (10 per page), infinite scroll
 */

// Protect this page - require authentication
if (!requireAuth()) {
  // User will be redirected to login
}

// ─── Global state ────────────────────────────────────────────────────────────
let currentChannel  = null;
let channelVideos   = [];          // all videos fetched so far
let displayedCount  = 0;           // how many are currently rendered
const PAGE_SIZE     = 10;          // videos per page
let isLoadingMore   = false;       // guard against double-loads
let currentSort     = 'latest';

// ─── Boot ────────────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  loadChannelData();
});

// ─────────────────────────────────────────────────────────────────────────────
// LOAD CHANNEL DATA
// ─────────────────────────────────────────────────────────────────────────────

/**
 * Main entry point – fetches channel + first page of videos
 */
async function loadChannelData() {
  try {
    showLoadingState();

    const channels = await api.getYouTubeChannels();

    if (!channels || channels.length === 0) {
      showNoChannelState();
      hideLoadingState();
      return;
    }

    currentChannel = channels[0];

    // Load only the first PAGE_SIZE videos on initial load
    await loadChannelVideos(currentChannel.id, PAGE_SIZE);

    renderChannelHeader(currentChannel);
    renderVideos(channelVideos, false);   // false = replace, not append

    const user = await api.getCurrentUser();
    updateSidebar(user);

    hideLoadingState();
  } catch (error) {
    console.error('Failed to load channel data:', error);
    showError('Failed to load channel data. Please try again.');
    hideLoadingState();
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// VIDEO FETCHING
// ─────────────────────────────────────────────────────────────────────────────

/**
 * Fetch videos from the API.
 * @param {string} channelId
 * @param {number} limit  - how many to fetch (default 10 for initial, 100 for full)
 */
async function loadChannelVideos(channelId, limit = PAGE_SIZE) {
  try {
    const videos = await api.getChannelVideos(channelId, limit);
    channelVideos  = videos || [];
    displayedCount = channelVideos.length;
  } catch (error) {
    console.error('Failed to load videos:', error);
    channelVideos  = [];
    displayedCount = 0;
    showToast('Failed to load videos', 'error');
  }
}

/**
 * Load the next PAGE_SIZE videos (called on scroll or "Load more" click).
 * Fetches a larger batch from the API and renders the new slice.
 */
async function loadMoreVideos() {
  if (isLoadingMore || !currentChannel) return;

  const nextLimit = displayedCount + PAGE_SIZE;

  // If we already have enough in memory, just render the next slice
  if (nextLimit <= channelVideos.length) {
    displayedCount = nextLimit;
    renderVideos(channelVideos.slice(0, displayedCount), false);
    updateLoadMoreButton();
    return;
  }

  // Otherwise fetch more from the API
  isLoadingMore = true;
  showLoadMoreSpinner(true);

  try {
    const videos = await api.getChannelVideos(currentChannel.id, nextLimit);
    channelVideos  = applySortToVideos(videos || [], currentSort);
    displayedCount = Math.min(nextLimit, channelVideos.length);
    renderVideos(channelVideos.slice(0, displayedCount), false);
    updateLoadMoreButton();
  } catch (error) {
    console.error('Failed to load more videos:', error);
    showToast('Failed to load more videos', 'error');
  } finally {
    isLoadingMore = false;
    showLoadMoreSpinner(false);
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// RENDER CHANNEL HEADER
// ─────────────────────────────────────────────────────────────────────────────

function renderChannelHeader(channel) {
  const pageContent = document.getElementById('pageContent');

  const avatarStyle = channel.thumbnail_url
    ? `style="background-image:url('${channel.thumbnail_url}');background-size:cover;background-position:center;"`
    : '';
  const avatarText = channel.thumbnail_url
    ? ''
    : channel.channel_name.split(' ').map(w => w[0]).join('').toUpperCase().slice(0, 2);

  const headerHTML = `
    <div class="channel-header-card">
      <div class="channel-avatar" ${avatarStyle}>${avatarText}</div>
      <div class="channel-info">
        <h2>${escapeHtml(channel.channel_name)}</h2>
        <div class="channel-handle">@${escapeHtml(channel.channel_handle || channel.channel_name.replace(/\s+/g, '').toLowerCase())}</div>
        <div class="channel-meta">
          <div class="channel-meta-item">👥 <strong>${formatNumber(channel.subscriber_count || 0)}</strong> subscribers</div>
          <div class="channel-meta-item">🎬 <strong>${formatNumber(channel.video_count || 0)}</strong> videos</div>
          <div class="channel-meta-item">👁️ <strong>${formatNumber(channel.view_count || 0)}</strong> total views</div>
          <div class="channel-meta-item">📅 Joined <strong>${formatDate(channel.published_at)}</strong></div>
          <div class="channel-meta-item">🌍 <strong>${channel.country || 'Unknown'}</strong></div>
        </div>
      </div>
      <div class="channel-header-actions">
        <span class="badge badge-success">✓ Connected</span>
        <button class="btn btn-outline btn-sm" onclick="refreshChannel()">🔄 Refresh</button>
        <button class="btn btn-primary btn-sm" onclick="syncChannel()">🔄 Sync Videos</button>
      </div>
    </div>
  `;

  const avgSeoScore = channelVideos.length > 0
    ? Math.round(channelVideos.reduce((sum, v) => sum + (v.seo_score || 0), 0) / channelVideos.length)
    : 0;
  const totalLikes  = channelVideos.reduce((sum, v) => sum + (v.like_count  || 0), 0);
  const totalViews  = channelVideos.reduce((sum, v) => sum + (v.view_count  || 0), 0);
  const engagementRate = totalViews > 0 ? ((totalLikes / totalViews) * 100).toFixed(1) : 0;

  const statsHTML = `
    <div class="stats-grid" style="margin-bottom:var(--space-xl);">
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
    </div>
  `;

  const videosHTML = `
    <div class="card">
      <div class="card-header">
        <span class="card-title" id="videoCountLabel">Videos (${channelVideos.length})</span>
        <div style="display:flex;gap:var(--space-sm);">
          <select onchange="sortVideos(this.value)" style="background:var(--bg-surface);border:1px solid var(--border);border-radius:var(--radius-md);padding:6px 10px;color:var(--text-primary);font-size:0.8rem;">
            <option value="latest">Sort: Latest</option>
            <option value="views">Sort: Most Views</option>
            <option value="seo">Sort: SEO Score</option>
            <option value="engagement">Sort: Engagement</option>
          </select>
          <button class="btn btn-primary btn-sm" onclick="syncChannel()">🔄 Sync All</button>
        </div>
      </div>

      <!-- Videos grid -->
      <div class="videos-grid" id="videosGrid"></div>

      <!-- Load more controls -->
      <div id="loadMoreContainer" style="text-align:center;padding:24px 0;display:none;">
        <div id="loadMoreSpinner" style="display:none;margin-bottom:8px;">
          <span style="color:var(--text-muted);font-size:0.85rem;">Loading more videos…</span>
        </div>
        <button id="loadMoreBtn" class="btn btn-outline" onclick="loadMoreVideos()">
          Load more videos
        </button>
      </div>
    </div>
  `;

  pageContent.innerHTML = headerHTML + statsHTML + videosHTML;

  // Attach infinite-scroll listener after DOM is ready
  attachScrollListener();
}

// ─────────────────────────────────────────────────────────────────────────────
// RENDER VIDEOS
// ─────────────────────────────────────────────────────────────────────────────

/**
 * Render a list of videos into the grid.
 * @param {Array}   videos  - array of video objects to render
 * @param {boolean} append  - if true, append to existing grid; if false, replace
 */
function renderVideos(videos, append = false) {
  const grid = document.getElementById('videosGrid');
  if (!grid) return;

  if (!append && videos.length === 0) {
    grid.innerHTML = `
      <div style="grid-column:1/-1;text-align:center;padding:60px 20px;color:var(--text-muted);">
        <div style="font-size:3rem;margin-bottom:16px;">🎬</div>
        <h3 style="margin-bottom:8px;">No videos found</h3>
        <p>Sync your channel to see your videos here.</p>
        <button class="btn btn-primary" onclick="syncChannel()" style="margin-top:16px;">
          🔄 Sync Channel
        </button>
      </div>
    `;
    return;
  }

  const html = videos.map(video => {
    const seoScore  = video.seo_score || 0;
    const scoreColor = getSeoColor(seoScore);
    const thumbnail  = video.thumbnail_url || 'https://via.placeholder.com/320x180?text=No+Thumbnail';

    return `
      <div class="video-card" onclick="viewVideo('${video.id}')">
        <div class="video-thumbnail"
             style="background-image:url('${thumbnail}');background-size:cover;background-position:center;">
          <div class="play-overlay"><div class="play-btn">▶</div></div>
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

  if (append) {
    grid.insertAdjacentHTML('beforeend', html);
  } else {
    grid.innerHTML = html;
  }

  updateLoadMoreButton();
}

// ─────────────────────────────────────────────────────────────────────────────
// LOAD MORE / INFINITE SCROLL
// ─────────────────────────────────────────────────────────────────────────────

/**
 * Show or hide the "Load more" button based on whether there are more videos.
 */
function updateLoadMoreButton() {
  const container = document.getElementById('loadMoreContainer');
  const btn       = document.getElementById('loadMoreBtn');
  const label     = document.getElementById('videoCountLabel');

  if (!container) return;

  // Update the header label with current count
  if (label) {
    label.textContent = `Videos (showing ${displayedCount} of ${channelVideos.length}+)`;
  }

  // Show "Load more" only if we might have more videos
  // We know there are more if the last fetch returned exactly the limit we asked for
  const hasMore = channelVideos.length >= displayedCount;
  container.style.display = hasMore ? 'block' : 'none';

  if (btn) {
    btn.textContent = `Load more videos (showing ${displayedCount})`;
  }
}

function showLoadMoreSpinner(show) {
  const spinner = document.getElementById('loadMoreSpinner');
  const btn     = document.getElementById('loadMoreBtn');
  if (spinner) spinner.style.display = show ? 'block' : 'none';
  if (btn)     btn.style.display     = show ? 'none'  : 'block';
}

/**
 * Attach an IntersectionObserver to the load-more container so videos
 * load automatically when the user scrolls near the bottom.
 */
function attachScrollListener() {
  const sentinel = document.getElementById('loadMoreContainer');
  if (!sentinel || !('IntersectionObserver' in window)) return;

  const observer = new IntersectionObserver((entries) => {
    if (entries[0].isIntersecting && !isLoadingMore) {
      loadMoreVideos();
    }
  }, { rootMargin: '200px' });   // trigger 200px before it enters viewport

  observer.observe(sentinel);
}

// ─────────────────────────────────────────────────────────────────────────────
// SYNC / REFRESH
// ─────────────────────────────────────────────────────────────────────────────

function viewVideo(videoId) {
  window.location.href = `analyzer.html?video=${videoId}`;
}

async function syncChannel() {
  if (!currentChannel) {
    showToast('No channel connected', 'error');
    return;
  }

  try {
    showToast('Syncing channel data…', 'info');
    await api.syncChannelVideos(currentChannel.id);

    // After sync, reload from scratch
    displayedCount = 0;
    channelVideos  = [];
    await loadChannelData();

    showToast('✅ Channel synced successfully!', 'success');
  } catch (error) {
    console.error('Failed to sync channel:', error);
    showToast('Failed to sync channel. Please try again.', 'error');
  }
}

async function refreshChannel() {
  displayedCount = 0;
  channelVideos  = [];
  await loadChannelData();
  showToast('✅ Channel data refreshed!', 'success');
}

// ─────────────────────────────────────────────────────────────────────────────
// SORT
// ─────────────────────────────────────────────────────────────────────────────

function sortVideos(sortBy) {
  currentSort   = sortBy;
  channelVideos = applySortToVideos(channelVideos, sortBy);
  renderVideos(channelVideos.slice(0, displayedCount), false);
}

function applySortToVideos(videos, sortBy) {
  const sorted = [...videos];
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
  return sorted;
}

// ─────────────────────────────────────────────────────────────────────────────
// NO CHANNEL STATE
// ─────────────────────────────────────────────────────────────────────────────

function showNoChannelState() {
  const mainContent = document.querySelector('.page-content');
  mainContent.innerHTML = `
    <div style="text-align:center;padding:80px 20px;">
      <div style="font-size:5rem;margin-bottom:24px;">📺</div>
      <h2 style="margin-bottom:12px;">No YouTube Channel Connected</h2>
      <p style="color:var(--text-muted);margin-bottom:32px;max-width:500px;margin-left:auto;margin-right:auto;">
        Connect your YouTube channel to view analytics, manage videos, and optimise your content with AI-powered insights.
      </p>
      <button class="btn btn-primary" onclick="connectChannel()">
        🔗 Connect YouTube Channel
      </button>
    </div>
  `;
}

async function connectChannel() {
  try {
    showToast('Redirecting to YouTube…', 'info');

    const token = localStorage.getItem('auth_token');
    if (!token) { showToast('Not authenticated. Please login first.', 'error'); return; }

    const userData = localStorage.getItem('user_data');
    if (!userData) { showToast('User data not found. Please login again.', 'error'); return; }

    const user   = JSON.parse(userData);
    const userId = user.id;
    if (!userId) { showToast('User ID not found. Please login again.', 'error'); return; }

    window.location.href = `${api.baseURL}/youtube/oauth/authorize?user_id=${encodeURIComponent(userId)}`;
  } catch (error) {
    console.error('Failed to connect channel:', error);
    showToast('Failed to connect channel. Please try again.', 'error');
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// SIDEBAR
// ─────────────────────────────────────────────────────────────────────────────

function updateSidebar(user) {
  const sidebarName   = document.querySelector('.sidebar-user .user-name');
  const sidebarAvatar = document.querySelector('.sidebar-user .avatar');

  if (sidebarName) sidebarName.textContent = user.full_name || user.email;

  if (sidebarAvatar) {
    if (user.avatar_url) {
      sidebarAvatar.style.backgroundImage = `url(${user.avatar_url})`;
      sidebarAvatar.style.backgroundSize  = 'cover';
      sidebarAvatar.textContent = '';
    } else {
      sidebarAvatar.textContent = user.full_name
        ? user.full_name.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2)
        : user.email[0].toUpperCase();
    }
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// HELPER FUNCTIONS
// ─────────────────────────────────────────────────────────────────────────────

function formatNumber(num) {
  if (num >= 1_000_000) return (num / 1_000_000).toFixed(1) + 'M';
  if (num >= 1_000)     return (num / 1_000).toFixed(1) + 'K';
  return String(num);
}

function formatDate(dateString) {
  if (!dateString) return 'Unknown';
  return new Date(dateString).toLocaleDateString('en-US', { month: 'long', year: 'numeric' });
}

function formatTimeAgo(dateString) {
  if (!dateString) return 'Unknown';
  const seconds = Math.floor((Date.now() - new Date(dateString)) / 1000);
  const intervals = { year: 31536000, month: 2592000, week: 604800, day: 86400, hour: 3600, minute: 60 };
  for (const [unit, s] of Object.entries(intervals)) {
    const n = Math.floor(seconds / s);
    if (n >= 1) return `${n} ${unit}${n > 1 ? 's' : ''} ago`;
  }
  return 'Just now';
}

/**
 * Format duration – handles BOTH:
 *   • integer seconds  (e.g. 3723  → "1:02:03")   ← what the DB stores
 *   • ISO 8601 string  (e.g. "PT1H2M3S" → "1:02:03")  ← raw YouTube API value
 */
function formatDuration(duration) {
  if (duration === null || duration === undefined) return '0:00';

  let totalSeconds;

  if (typeof duration === 'number') {
    // DB stores duration as integer seconds
    totalSeconds = Math.floor(duration);
  } else if (typeof duration === 'string') {
    if (/^\d+$/.test(duration)) {
      // Numeric string like "3723"
      totalSeconds = parseInt(duration, 10);
    } else {
      // ISO 8601 string like "PT1H2M3S"
      const match = duration.match(/PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?/);
      if (!match) return '0:00';
      totalSeconds = (parseInt(match[1] || 0) * 3600)
                   + (parseInt(match[2] || 0) * 60)
                   +  parseInt(match[3] || 0);
    }
  } else {
    return '0:00';
  }

  const h = Math.floor(totalSeconds / 3600);
  const m = Math.floor((totalSeconds % 3600) / 60);
  const s = totalSeconds % 60;

  if (h > 0) {
    return `${h}:${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`;
  }
  return `${m}:${String(s).padStart(2, '0')}`;
}

function getSeoColor(score) {
  if (score >= 80) return 'var(--success)';
  if (score >= 60) return 'var(--warning)';
  return 'var(--danger)';
}

function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

function showLoadingState() {
  const el = document.querySelector('.page-content');
  if (el) { el.style.opacity = '0.6'; el.style.pointerEvents = 'none'; }
}

function hideLoadingState() {
  const el = document.querySelector('.page-content');
  if (el) { el.style.opacity = '1'; el.style.pointerEvents = 'auto'; }
}

function showError(message) {
  showToast(message, 'error');
}
