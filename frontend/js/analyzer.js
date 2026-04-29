/**
 * Video Analyzer Page Logic with API Integration
 * Handles video selection, SEO analysis, and results display
 */

// Protect this page - require authentication
if (!requireAuth()) {
  // User will be redirected to login
}

// Global state
let channelVideos = [];
let selectedVideoId = null;
let currentAnalysis = null;

// Initialize analyzer page
document.addEventListener('DOMContentLoaded', () => {
  // Check if video ID is in URL
  const urlParams = new URLSearchParams(window.location.search);
  const videoIdFromUrl = urlParams.get('video');
  
  if (videoIdFromUrl) {
    selectedVideoId = videoIdFromUrl;
  }
  
  loadVideos();
});

/**
 * Load channel videos
 */
async function loadVideos() {
  try {
    showLoadingState();
    
    // Get connected channels
    const channels = await api.getYouTubeChannels();
    
    if (!channels || channels.length === 0) {
      showNoChannelState();
      return;
    }
    
    // Get videos from first channel
    const channelId = channels[0].id;
    channelVideos = await api.getChannelVideos(channelId, 100);
    
    // Render video selector
    renderVideoSelector();
    
    // If video ID was provided, analyze it
    if (selectedVideoId) {
      const video = channelVideos.find(v => v.id === selectedVideoId);
      if (video) {
        await selectVideo(selectedVideoId);
      } else {
        // Video not found, select first video
        if (channelVideos.length > 0) {
          await selectVideo(channelVideos[0].id);
        }
      }
    } else if (channelVideos.length > 0) {
      // Select first video by default
      await selectVideo(channelVideos[0].id);
    }
    
    // Load user for sidebar
    const user = await api.getCurrentUser();
    updateSidebar(user);
    
    hideLoadingState();
  } catch (error) {
    console.error('Failed to load videos:', error);
    showError('Failed to load videos. Please try again.');
    hideLoadingState();
  }
}

/**
 * Render video selector list
 */
function renderVideoSelector() {
  const list = document.getElementById('videoSelectorList');
  if (!list) return;
  
  // Update video count
  const countEl = document.querySelector('.card-header span:last-child');
  if (countEl) {
    countEl.textContent = `${channelVideos.length} videos`;
  }
  
  if (channelVideos.length === 0) {
    list.innerHTML = `
      <div style="text-align:center;padding:var(--space-xl);color:var(--text-muted);">
        <div style="font-size:2rem;margin-bottom:var(--space-sm);">🎬</div>
        <p>No videos found</p>
        <button class="btn btn-primary btn-sm" onclick="window.location.href='channel.html'" style="margin-top:var(--space-md);">
          Go to Channel
        </button>
      </div>
    `;
    return;
  }
  
  list.innerHTML = channelVideos.map(v => {
    const seoScore = v.seo_score || 0;
    const scoreColor = getSeoColor(seoScore);
    const isSelected = v.id === selectedVideoId;
    const thumbnail = v.thumbnail_url || 'https://via.placeholder.com/120x68?text=No+Thumbnail';
    
    return `
      <div class="video-selector-item ${isSelected ? 'selected' : ''}"
           onclick="selectVideo('${v.id}')" id="vs-${v.id}">
        <div class="vs-thumb" style="background-image:url('${thumbnail}');background-size:cover;background-position:center;"></div>
        <div class="vs-info">
          <div class="vs-title">${escapeHtml(v.title)}</div>
          <div class="vs-views">👁️ ${formatNumber(v.view_count || 0)} · ${formatTimeAgo(v.published_at)}</div>
        </div>
        <span class="vs-score" style="color:${scoreColor};">${seoScore}</span>
      </div>
    `;
  }).join('');
}

/**
 * Select and analyze a video
 */
async function selectVideo(videoId) {
  // Update selection state
  document.querySelectorAll('.video-selector-item').forEach(el => el.classList.remove('selected'));
  const el = document.getElementById(`vs-${videoId}`);
  if (el) el.classList.add('selected');
  
  selectedVideoId = videoId;
  
  // Update URL without reload
  const url = new URL(window.location);
  url.searchParams.set('video', videoId);
  window.history.pushState({}, '', url);
  
  // Show loading state
  showAnalysisLoading();
  
  try {
    // Analyze video via API
    const analysis = await api.analyzeVideoSEO(videoId, false);
    currentAnalysis = analysis;
    
    // Render analysis results
    renderAnalysis(videoId, analysis);
  } catch (error) {
    console.error('Failed to analyze video:', error);
    showAnalysisError('Failed to analyze video. Please try again.');
  }
}

/**
 * Show analysis loading state
 */
function showAnalysisLoading() {
  const panel = document.getElementById('analysisPanel');
  panel.innerHTML = `
    <div class="card" style="text-align:center;padding:var(--space-3xl);">
      <div style="font-size:2rem;margin-bottom:var(--space-md);">🔍</div>
      <div style="font-size:0.9rem;color:var(--text-secondary);">Analyzing video SEO...</div>
      <div style="display:flex;justify-content:center;gap:6px;margin-top:var(--space-md);">
        <div class="ai-dot"></div>
        <div class="ai-dot"></div>
        <div class="ai-dot"></div>
      </div>
    </div>
  `;
}

/**
 * Show analysis error
 */
function showAnalysisError(message) {
  const panel = document.getElementById('analysisPanel');
  panel.innerHTML = `
    <div class="card" style="text-align:center;padding:var(--space-3xl);">
      <div style="font-size:2rem;margin-bottom:var(--space-md);">❌</div>
      <div style="font-size:0.9rem;color:var(--text-secondary);margin-bottom:var(--space-md);">${message}</div>
      <button class="btn btn-primary" onclick="selectVideo('${selectedVideoId}')">
        🔄 Try Again
      </button>
    </div>
  `;
}

/**
 * Render analysis results
 */
function renderAnalysis(videoId, analysis) {
  const panel = document.getElementById('analysisPanel');
  if (!panel) return;
  
  const video = channelVideos.find(v => v.id === videoId);
  if (!video) return;
  
  const score = analysis.overall_score || 0;
  const { grade, color } = getSeoGrade(score);
  
  // SVG ring: circumference = 2 * PI * 54 ≈ 339
  const circumference = 339;
  const offset = circumference * (1 - score / 100);
  
  // Parse criteria scores
  const criteria = [
    {
      name: 'Title Optimization',
      detail: analysis.title_analysis?.feedback || 'Title analysis',
      score: analysis.title_score || 0,
      status: getStatus(analysis.title_score || 0)
    },
    {
      name: 'Description Quality',
      detail: analysis.description_analysis?.feedback || 'Description analysis',
      score: analysis.description_score || 0,
      status: getStatus(analysis.description_score || 0)
    },
    {
      name: 'Tags Effectiveness',
      detail: analysis.tags_analysis?.feedback || 'Tags analysis',
      score: analysis.tags_score || 0,
      status: getStatus(analysis.tags_score || 0)
    },
    {
      name: 'Thumbnail Quality',
      detail: analysis.thumbnail_analysis?.feedback || 'Thumbnail analysis',
      score: analysis.thumbnail_score || 0,
      status: getStatus(analysis.thumbnail_score || 0)
    },
    {
      name: 'Engagement Metrics',
      detail: analysis.engagement_analysis?.feedback || 'Engagement analysis',
      score: analysis.engagement_score || 0,
      status: getStatus(analysis.engagement_score || 0)
    }
  ];
  
  // Parse suggestions
  const suggestions = analysis.suggestions || [];
  
  const statusIcons = { good: '✅', warn: '⚠️', bad: '❌' };
  const statusColors = {
    good: 'rgba(16,185,129,0.12)',
    warn: 'rgba(245,158,11,0.12)',
    bad:  'rgba(239,68,68,0.12)',
  };
  const statusTextColors = {
    good: 'var(--success)',
    warn: 'var(--warning)',
    bad:  'var(--danger)',
  };
  
  panel.innerHTML = `
    <!-- Score Card -->
    <div class="card" style="margin-bottom:var(--space-lg);">
      <div class="card-header">
        <span class="card-title">SEO Score</span>
        <span class="badge badge-${score >= 80 ? 'success' : score >= 60 ? 'warning' : 'danger'}">${grade}</span>
      </div>

      <div style="display:flex;align-items:center;gap:var(--space-xl);flex-wrap:wrap;">
        <!-- Ring -->
        <div class="seo-score-display">
          <div class="score-ring-large">
            <svg viewBox="0 0 120 120">
              <defs>
                <linearGradient id="ringGrad" x1="0%" y1="0%" x2="100%" y2="0%">
                  <stop offset="0%" stop-color="${color}"/>
                  <stop offset="100%" stop-color="${color}" stop-opacity="0.6"/>
                </linearGradient>
              </defs>
              <circle class="ring-bg"   cx="60" cy="60" r="54"/>
              <circle class="ring-fill" cx="60" cy="60" r="54"
                stroke="${color}"
                style="stroke-dasharray:${circumference};stroke-dashoffset:${circumference};"
                id="analyzerRing"/>
            </svg>
            <div class="score-ring-center">
              <div class="score-num">${score}</div>
              <div class="score-label">/ 100</div>
            </div>
          </div>
        </div>

        <!-- Video Info -->
        <div style="flex:1;min-width:200px;">
          <div style="font-size:0.95rem;font-weight:700;color:var(--text-primary);margin-bottom:var(--space-sm);line-height:1.4;">${escapeHtml(video.title)}</div>
          <div style="display:flex;flex-wrap:wrap;gap:var(--space-md);font-size:0.8rem;color:var(--text-muted);">
            <span>👁️ ${formatNumber(video.view_count || 0)} views</span>
            <span>👍 ${formatNumber(video.like_count || 0)} likes</span>
            <span>💬 ${formatNumber(video.comment_count || 0)} comments</span>
            <span>⏱️ ${formatDuration(video.duration)}</span>
          </div>
          <div style="margin-top:var(--space-md);display:flex;gap:var(--space-sm);flex-wrap:wrap;">
            ${video.tags ? video.tags.slice(0, 5).map(t => `<span class="tag-chip">#${escapeHtml(t)}</span>`).join('') : ''}
          </div>
          <div style="margin-top:var(--space-md);display:flex;gap:var(--space-sm);">
            <a href="generator.html?video=${video.id}" class="btn btn-primary btn-sm">✨ Generate Better Content</a>
            <button class="btn btn-ghost btn-sm" onclick="reanalyzeVideo()">🔄 Re-analyze</button>
          </div>
        </div>
      </div>
    </div>

    <!-- SEO Criteria -->
    <div class="card" style="margin-bottom:var(--space-lg);">
      <div class="card-header">
        <span class="card-title">SEO Criteria Breakdown</span>
      </div>
      <div class="seo-criteria">
        ${criteria.map(c => `
          <div class="criteria-item">
            <div class="criteria-icon" style="background:${statusColors[c.status]};">
              ${statusIcons[c.status]}
            </div>
            <div class="criteria-info">
              <div class="criteria-name">${c.name}</div>
              <div class="criteria-detail">${c.detail}</div>
            </div>
            <div class="criteria-score" style="color:${statusTextColors[c.status]};">${c.score}/100</div>
          </div>
        `).join('')}
      </div>
    </div>

    <!-- Suggestions -->
    <div class="card">
      <div class="card-header">
        <span class="card-title">💡 Improvement Suggestions</span>
        <span style="font-size:0.75rem;color:var(--text-muted);">${suggestions.length} suggestions</span>
      </div>
      <div class="suggestions-list">
        ${suggestions.length > 0 ? suggestions.map(s => {
          const type = s.priority === 'high' ? 'bad' : s.priority === 'medium' ? 'warn' : 'good';
          return `
            <div class="suggestion-card">
              <div class="sug-icon" style="background:${statusColors[type]};">${statusIcons[type]}</div>
              <div class="sug-text">
                <strong>${escapeHtml(s.category || 'Suggestion')}</strong>
                ${escapeHtml(s.suggestion)}
              </div>
            </div>
          `;
        }).join('') : '<div style="text-align:center;padding:var(--space-xl);color:var(--text-muted);">No suggestions available</div>'}
      </div>
    </div>
  `;
  
  // Animate the ring
  setTimeout(() => {
    const ring = document.getElementById('analyzerRing');
    if (ring) ring.style.strokeDashoffset = offset;
  }, 100);
}

/**
 * Re-analyze current video (force re-analysis)
 */
async function reanalyzeVideo() {
  if (!selectedVideoId) return;
  
  showAnalysisLoading();
  showToast('Re-analyzing video...', 'info');
  
  try {
    // Force re-analysis
    const analysis = await api.analyzeVideoSEO(selectedVideoId, true);
    currentAnalysis = analysis;
    
    // Render analysis results
    renderAnalysis(selectedVideoId, analysis);
    
    showToast('✅ Video re-analyzed successfully!', 'success');
  } catch (error) {
    console.error('Failed to re-analyze video:', error);
    showAnalysisError('Failed to re-analyze video. Please try again.');
    showToast('Failed to re-analyze video', 'error');
  }
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
        Connect your YouTube channel to analyze your videos and get SEO optimization insights.
      </p>
      <button class="btn btn-primary" onclick="window.location.href='channel.html'">
        🔗 Connect YouTube Channel
      </button>
    </div>
  `;
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
 * Get status based on score
 */
function getStatus(score) {
  if (score >= 80) return 'good';
  if (score >= 60) return 'warn';
  return 'bad';
}

/**
 * Get SEO grade and color
 */
function getSeoGrade(score) {
  if (score >= 90) return { grade: 'A+', color: '#10B981' };
  if (score >= 80) return { grade: 'A', color: '#10B981' };
  if (score >= 70) return { grade: 'B', color: '#3B82F6' };
  if (score >= 60) return { grade: 'C', color: '#F59E0B' };
  if (score >= 50) return { grade: 'D', color: '#EF4444' };
  return { grade: 'F', color: '#EF4444' };
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
 * Format number with K/M suffix
 */
function formatNumber(num) {
  if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M';
  if (num >= 1000) return (num / 1000).toFixed(1) + 'K';
  return num.toString();
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
