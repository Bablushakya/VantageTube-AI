/**
 * Trending Topics Page Logic with API Integration
 * Handles trending video discovery, filtering, and content opportunities
 */

// Protect this page - require authentication
if (!requireAuth()) {
  // User will be redirected to login
}

// Global state
let trendingVideos = [];
let currentFilter = 'all';
let currentRegion = 'US';
let currentNiche = 'tech';

// Initialize trending page
document.addEventListener('DOMContentLoaded', () => {
  loadTrendingData();
  loadUser();
});

/**
 * Load trending data from API
 */
async function loadTrendingData() {
  try {
    showLoadingState();
    
    // Fetch trending videos
    await fetchTrendingVideos();
    
    // Render trending cards
    renderTrendingCards(trendingVideos);
    
    // Update stats
    updateStats();
    
    hideLoadingState();
  } catch (error) {
    console.error('Failed to load trending data:', error);
    showError('Failed to load trending topics. Please try again.');
    hideLoadingState();
  }
}

/**
 * Fetch trending videos from API
 */
async function fetchTrendingVideos() {
  try {
    showToast('Fetching trending videos...', 'info');
    
    // Fetch trending videos for region
    const result = await api.fetchTrendingVideos(currentRegion, null, 50);
    
    // Filter by niche if needed
    if (currentNiche && currentNiche !== 'all') {
      const filtered = await api.filterTrendingVideos({
        niche: currentNiche,
        min_viral_score: 0,
        max_results: 50
      });
      trendingVideos = filtered.videos || [];
    } else {
      trendingVideos = result.videos || [];
    }
    
    showToast('✅ Trending data loaded!', 'success');
  } catch (error) {
    console.error('Failed to fetch trending videos:', error);
    trendingVideos = [];
    throw error;
  }
}

/**
 * Refresh trending data
 */
async function refreshTrending() {
  await loadTrendingData();
  showToast('✅ Trending data refreshed!', 'success');
}

/**
 * Change niche filter
 */
async function changeNiche(niche) {
  currentNiche = niche;
  await loadTrendingData();
}

/**
 * Filter trending by trend type
 */
function filterTrending(filter, button) {
  currentFilter = filter;
  
  // Update active button
  document.querySelectorAll('.filter-chip').forEach(btn => btn.classList.remove('active'));
  if (button) button.classList.add('active');
  
  // Filter videos
  let filtered = [...trendingVideos];
  
  if (filter !== 'all') {
    filtered = filtered.filter(video => {
      const viralScore = video.viral_score || 0;
      const growthRate = video.growth_rate || 0;
      
      switch (filter) {
        case 'exploding':
          return viralScore >= 80 && growthRate >= 50;
        case 'rising':
          return viralScore >= 60 && viralScore < 80;
        case 'growing':
          return viralScore >= 40 && viralScore < 60;
        case 'stable':
          return viralScore < 40;
        default:
          return true;
      }
    });
  }
  
  renderTrendingCards(filtered);
}

/**
 * Render trending cards
 */
function renderTrendingCards(videos) {
  const grid = document.getElementById('trendingGrid');
  if (!grid) return;
  
  if (!videos || videos.length === 0) {
    grid.innerHTML = `
      <div style="grid-column:1/-1;text-align:center;padding:var(--space-3xl);color:var(--text-muted);">
        <div style="font-size:2.5rem;margin-bottom:var(--space-md);">🔍</div>
        <div>No trending topics found for this filter.</div>
        <button class="btn btn-primary" onclick="refreshTrending()" style="margin-top:var(--space-md);">
          🔄 Refresh Trending
        </button>
      </div>
    `;
    return;
  }
  
  grid.innerHTML = videos.slice(0, 12).map((video, i) => {
    const viralScore = video.viral_score || 0;
    const viralPct = viralScore + '%';
    
    // Determine trend badge
    const trendBadge = getTrendBadge(viralScore, video.growth_rate || 0);
    
    // Determine competition level
    const competition = getCompetitionLevel(video.view_count || 0);
    const competitionColor = {
      'Low': 'var(--success)',
      'Medium': 'var(--warning)',
      'High': 'var(--danger)'
    }[competition] || 'var(--text-muted)';
    
    // Extract tags from title
    const tags = extractTags(video.title);
    
    // Generate content ideas
    const ideas = generateContentIdeas(video.title, video.description);
    
    return `
      <div class="trending-card" style="animation-delay:${i * 0.08}s;">
        <span class="fire-badge">${trendBadge.icon}</span>

        <div class="trending-card-header">
          <span class="trending-rank">#${i + 1} Trending</span>
          <span class="badge badge-${trendBadge.class}">${trendBadge.label}</span>
        </div>

        <div class="trending-topic">${escapeHtml(video.title)}</div>
        <div class="trending-desc">${escapeHtml(truncate(video.description || 'Trending video', 120))}</div>

        <!-- Tags -->
        <div style="display:flex;flex-wrap:wrap;gap:6px;margin-bottom:var(--space-md);">
          ${tags.slice(0, 3).map(tag => `<span class="tag-chip" style="font-size:0.7rem;padding:3px 8px;">#${escapeHtml(tag)}</span>`).join('')}
        </div>

        <!-- Meta -->
        <div class="trending-meta">
          <div class="trending-meta-item">�️ <strong>${formatNumber(video.view_count || 0)}</strong></div>
          <div class="trending-meta-item">
            ⚔️ Competition:
            <strong style="color:${competitionColor};">${competition}</strong>
          </div>
        </div>

        <!-- Viral Score Bar -->
        <div class="viral-score">
          <span class="viral-label">Viral Score</span>
          <div class="viral-bar">
            <div class="viral-fill" style="width:${viralPct};"></div>
          </div>
          <span class="viral-value">${viralScore}%</span>
        </div>

        <!-- Content Ideas -->
        <div style="margin-top:var(--space-md);padding-top:var(--space-md);border-top:1px solid var(--border);">
          <div style="font-size:0.72rem;font-weight:600;text-transform:uppercase;letter-spacing:0.06em;color:var(--text-muted);margin-bottom:var(--space-sm);">
            💡 Video Ideas
          </div>
          ${ideas.map(idea => `
            <div style="font-size:0.8rem;color:var(--text-secondary);margin-bottom:6px;padding-left:var(--space-sm);border-left:2px solid var(--primary);">
              ${escapeHtml(idea)}
            </div>
          `).join('')}
        </div>

        <!-- Actions -->
        <div style="margin-top:var(--space-md);display:flex;gap:var(--space-sm);">
          <button class="btn btn-primary btn-sm w-full" onclick="useTopicForGeneration('${escapeForAttribute(video.title)}')">
            ✨ Generate Content
          </button>
          <button class="btn btn-ghost btn-sm" onclick="viewVideoDetails('${video.video_id}')">
            � Details
          </button>
        </div>
      </div>
    `;
  }).join('');
}

/**
 * Update stats cards
 */
function updateStats() {
  if (!trendingVideos || trendingVideos.length === 0) return;
  
  // Calculate stats
  const totalTopics = trendingVideos.length;
  const totalViews = trendingVideos.reduce((sum, v) => sum + (v.view_count || 0), 0);
  const lowCompetition = trendingVideos.filter(v => (v.view_count || 0) < 100000).length;
  const topViralScore = Math.max(...trendingVideos.map(v => v.viral_score || 0));
  
  // Update stat cards
  const statCards = document.querySelectorAll('.stat-card');
  if (statCards.length >= 4) {
    // Trending Topics
    statCards[0].querySelector('.stat-value').textContent = totalTopics;
    statCards[0].querySelector('.stat-change').textContent = `↑ ${Math.min(totalTopics, 5)} new today`;
    
    // Total Views
    statCards[1].querySelector('.stat-value').textContent = formatNumber(totalViews);
    statCards[1].querySelector('.stat-change').textContent = '↑ in your niche';
    
    // Low Competition
    statCards[2].querySelector('.stat-value').textContent = lowCompetition;
    statCards[2].querySelector('.stat-change').textContent = lowCompetition > 0 ? '↑ Easy wins available' : 'No easy wins';
    
    // Top Viral Score
    statCards[3].querySelector('.stat-value').textContent = topViralScore + '%';
    statCards[3].querySelector('.stat-change').textContent = '↑ Top trending topic';
  }
}

/**
 * Get trend badge based on viral score and growth
 */
function getTrendBadge(viralScore, growthRate) {
  if (viralScore >= 80 && growthRate >= 50) {
    return { icon: '🔥', label: '🔥 Exploding', class: 'danger' };
  } else if (viralScore >= 60) {
    return { icon: '📈', label: '📈 Rising', class: 'warning' };
  } else if (viralScore >= 40) {
    return { icon: '🌱', label: '🌱 Growing', class: 'success' };
  } else {
    return { icon: '📊', label: '📊 Stable', class: 'primary' };
  }
}

/**
 * Get competition level based on views
 */
function getCompetitionLevel(views) {
  if (views < 100000) return 'Low';
  if (views < 1000000) return 'Medium';
  return 'High';
}

/**
 * Extract tags from title
 */
function extractTags(title) {
  // Simple tag extraction from title
  const words = title.toLowerCase().split(/\s+/);
  const stopWords = ['the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'];
  const tags = words
    .filter(word => word.length > 3 && !stopWords.includes(word))
    .slice(0, 5);
  return tags;
}

/**
 * Generate content ideas based on video
 */
function generateContentIdeas(title, description) {
  // Generate 3 content ideas
  const ideas = [
    `"${title}" - Your unique take`,
    `Beginner's guide to ${title.toLowerCase()}`,
    `${title} - Tips and tricks`
  ];
  return ideas;
}

/**
 * Use topic for content generation
 */
function useTopicForGeneration(topic) {
  // Navigate to generator with topic pre-filled
  window.location.href = `generator.html?topic=${encodeURIComponent(topic)}`;
}

/**
 * View video details
 */
async function viewVideoDetails(videoId) {
  try {
    showToast('Loading video details...', 'info');
    
    // Analyze trending video
    const analysis = await api.analyzeTrendingVideo(videoId, currentNiche);
    
    // Show analysis in modal or navigate to analyzer
    showToast('✅ Video analyzed!', 'success');
    
    // For now, just show a toast with key info
    const message = `Viral Score: ${analysis.viral_score}% | Views: ${formatNumber(analysis.view_count || 0)}`;
    showToast(message, 'info', 3000);
  } catch (error) {
    console.error('Failed to analyze video:', error);
    showToast('Failed to analyze video', 'error');
  }
}

/**
 * Load user for sidebar
 */
async function loadUser() {
  try {
    const user = await api.getCurrentUser();
    updateSidebar(user);
  } catch (error) {
    console.error('Failed to load user:', error);
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
 * Truncate text
 */
function truncate(text, maxLength) {
  if (text.length <= maxLength) return text;
  return text.substring(0, maxLength) + '...';
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
 * Escape for HTML attributes
 */
function escapeForAttribute(text) {
  return text.replace(/'/g, "\\'").replace(/"/g, '&quot;');
}

/**
 * Show loading state
 */
function showLoadingState() {
  const grid = document.getElementById('trendingGrid');
  if (grid) {
    grid.innerHTML = `
      <div style="grid-column:1/-1;text-align:center;padding:var(--space-3xl);">
        <div style="font-size:2rem;margin-bottom:var(--space-md);">🔍</div>
        <div style="font-size:0.9rem;color:var(--text-secondary);">Loading trending topics...</div>
        <div style="display:flex;justify-content:center;gap:6px;margin-top:var(--space-md);">
          <div class="ai-dot"></div>
          <div class="ai-dot"></div>
          <div class="ai-dot"></div>
        </div>
      </div>
    `;
  }
}

/**
 * Hide loading state
 */
function hideLoadingState() {
  // Loading state will be replaced by content
}

/**
 * Show error message
 */
function showError(message) {
  const grid = document.getElementById('trendingGrid');
  if (grid) {
    grid.innerHTML = `
      <div style="grid-column:1/-1;text-align:center;padding:var(--space-3xl);">
        <div style="font-size:2rem;margin-bottom:var(--space-md);">❌</div>
        <div style="font-size:0.9rem;color:var(--text-secondary);margin-bottom:var(--space-md);">${message}</div>
        <button class="btn btn-primary" onclick="refreshTrending()">
          🔄 Try Again
        </button>
      </div>
    `;
  }
  showToast(message, 'error');
}
