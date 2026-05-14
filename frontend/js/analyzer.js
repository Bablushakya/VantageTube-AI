/**
 * VantageTube AI – Video Analytics Dashboard
 *
 * Complete rewrite: pure analytics dashboard, no AI SEO generation.
 * Shows performance metrics, traffic sources, audience insights,
 * retention graphs, keyword performance, and rule-based insights.
 *
 * Data source priority:
 *   1. YouTube Analytics API (via backend)
 *   2. YouTube Data API (via backend)
 *   3. Mock data (backend fallback)
 *
 * Charts rendered with Chart.js (loaded from CDN in HTML).
 */

if (!requireAuth()) { /* redirected */ }

// ─── State ────────────────────────────────────────────────────────────────────
let channelVideos   = [];
let selectedVideo   = null;
let analyticsData   = null;
let chartInstances  = {};     // { chartId: Chart }
let isLoading       = false;

// ─── Cache ────────────────────────────────────────────────────────────────────
const _SS_PREFIX = 'vt_analytics_';

function _cacheKey(videoId) {
  return `${_SS_PREFIX}${videoId}`;
}

function _saveToSession(videoId, data) {
  try {
    sessionStorage.setItem(_cacheKey(videoId), JSON.stringify({
      data,
      savedAt: Date.now()
    }));
  } catch (e) { /* sessionStorage full */ }
}

function _loadFromSession(videoId) {
  try {
    const raw = sessionStorage.getItem(_cacheKey(videoId));
    if (!raw) return null;
    const { data, savedAt } = JSON.parse(raw);
    if (Date.now() - savedAt > 15 * 60 * 1000) { // 15 min expiry
      sessionStorage.removeItem(_cacheKey(videoId));
      return null;
    }
    return data;
  } catch (e) { return null; }
}

function _clearCache(videoId) {
  if (videoId) {
    sessionStorage.removeItem(_cacheKey(videoId));
  } else {
    // Clear all analytics caches
    Object.keys(sessionStorage).forEach(key => {
      if (key.startsWith(_SS_PREFIX)) {
        sessionStorage.removeItem(key);
      }
    });
  }
}

// ─── Boot ─────────────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  const urlParams = new URLSearchParams(window.location.search);
  const videoIdFromUrl = urlParams.get('video');
  loadVideos(videoIdFromUrl);
});

// ─────────────────────────────────────────────────────────────────────────────
// LOAD VIDEO LIST
// ─────────────────────────────────────────────────────────────────────────────
async function loadVideos(preselectedId = null) {
  try {
    showPageLoading(true);

    const channels = await api.getYouTubeChannels();
    if (!channels || channels.length === 0) {
      showNoChannelState();
      return;
    }

    channelVideos = await api.getChannelVideos(channels[0].id, 100);
    renderVideoSelector();

    const target = preselectedId
      ? channelVideos.find(v => v.id === preselectedId)
      : channelVideos[0];

    if (target) selectVideo(target.id);

    const user = await api.getCurrentUser();
    updateSidebar(user);
  } catch (err) {
    console.error('Failed to load videos:', err);
    showToast('Failed to load videos. Please try again.', 'error');
  } finally {
    showPageLoading(false);
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// VIDEO SELECTOR
// ─────────────────────────────────────────────────────────────────────────────
function renderVideoSelector() {
  const list = document.getElementById('videoSelectorList');
  if (!list) return;

  const countEl = document.querySelector('.video-selector-count');
  if (countEl) countEl.textContent = `${channelVideos.length} videos`;

  if (channelVideos.length === 0) {
    list.innerHTML = `
      <div style="text-align:center;padding:var(--space-xl);color:var(--text-muted);">
        <div style="font-size:2rem;margin-bottom:var(--space-sm);">🎬</div>
        <p>No videos found</p>
        <button class="btn btn-primary btn-sm" onclick="window.location.href='channel.html'"
                style="margin-top:var(--space-md);">Go to Channel</button>
      </div>`;
    return;
  }

  list.innerHTML = channelVideos.map(v => {
    const thumbnail = v.thumbnail_url || 'https://via.placeholder.com/120x68?text=No+Thumbnail';
    return `
      <div class="video-selector-item" id="vs-${v.id}" onclick="selectVideo('${v.id}')">
        <div class="vs-thumb"
             style="background-image:url('${escapeHtml(thumbnail)}');background-size:cover;background-position:center;"></div>
        <div class="vs-info">
          <div class="vs-title">${escapeHtml(v.title)}</div>
          <div class="vs-meta">👁️ ${formatNumber(v.view_count || 0)} · ${formatTimeAgo(v.published_at)}</div>
        </div>
      </div>`;
  }).join('');
}

// ─────────────────────────────────────────────────────────────────────────────
// SELECT VIDEO
// ─────────────────────────────────────────────────────────────────────────────
async function selectVideo(videoId) {
  // Highlight in list
  document.querySelectorAll('.video-selector-item').forEach(el => el.classList.remove('selected'));
  const el = document.getElementById(`vs-${videoId}`);
  if (el) el.classList.add('selected');

  selectedVideo = channelVideos.find(v => v.id === videoId);
  if (!selectedVideo) return;

  // Update URL
  const url = new URL(window.location);
  url.searchParams.set('video', videoId);
  window.history.pushState({}, '', url);

  // Show refresh button
  document.getElementById('refreshAnalyticsBtn').style.display = 'block';

  // Check cache
  const cached = _loadFromSession(videoId);
  if (cached) {
    analyticsData = cached;
    renderAnalyticsDashboard();
    return;
  }

  // Load fresh analytics
  await loadAnalytics(videoId);
}

// ─────────────────────────────────────────────────────────────────────────────
// LOAD ANALYTICS
// ─────────────────────────────────────────────────────────────────────────────
async function loadAnalytics(videoId) {
  if (isLoading) return;
  isLoading = true;

  // Show loading, hide other states
  document.getElementById('emptyState').style.display = 'none';
  document.getElementById('analyticsContent').style.display = 'block';
  document.getElementById('analyticsLoading').style.display = 'flex';
  document.getElementById('analyticsError').style.display = 'none';

  try {
    analyticsData = await api.getVideoAnalytics(videoId);
    _saveToSession(videoId, analyticsData);
    renderAnalyticsDashboard();
  } catch (err) {
    console.error('Failed to load analytics:', err);
    document.getElementById('analyticsLoading').style.display = 'none';
    document.getElementById('analyticsError').style.display = 'flex';
    document.getElementById('analyticsErrorMessage').textContent =
      err.message || 'Unable to fetch analytics data. Please try again.';
  } finally {
    isLoading = false;
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// RETRY / REFRESH
// ─────────────────────────────────────────────────────────────────────────────
function retryLoadAnalytics() {
  if (selectedVideo) {
    loadAnalytics(selectedVideo.id);
  }
}

function refreshAnalytics() {
  if (selectedVideo) {
    _clearCache(selectedVideo.id);
    loadAnalytics(selectedVideo.id);
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// RENDER ANALYTICS DASHBOARD
// ─────────────────────────────────────────────────────────────────────────────
function renderAnalyticsDashboard() {
  if (!analyticsData || !selectedVideo) return;

  document.getElementById('analyticsLoading').style.display = 'none';
  document.getElementById('analyticsError').style.display = 'none';
  document.getElementById('analyticsContent').style.display = 'block';

  // Destroy existing charts
  destroyCharts();

  renderVideoHeader();
  renderPerformanceScore();
  renderKPIMetrics();
  renderViewsOverTime();
  renderTrafficSources();
  renderAudienceInsights();
  // Render device bar chart after DOM is ready
  setTimeout(() => {
    const devices = analyticsData.audience?.device_types || [];
    renderDeviceChart(devices);
  }, 100);
  renderRetention();
  renderKeywords();
  renderInsights();
}

// ─────────────────────────────────────────────────────────────────────────────
// VIDEO HEADER
// ─────────────────────────────────────────────────────────────────────────────
function renderVideoHeader() {
  const section = document.getElementById('videoHeaderSection');
  if (!section) return;

  const v = selectedVideo;
  const d = analyticsData;
  const classification = d.classification || 'Average';

  const badgeClass = {
    'Viral': 'badge-viral',
    'High Performer': 'badge-high',
    'Average': 'badge-average',
    'Underperforming': 'badge-low'
  }[classification] || 'badge-average';

  const badgeIcon = {
    'Viral': '🏆',
    'High Performer': '⭐',
    'Average': '📊',
    'Underperforming': '⚠️'
  }[classification] || '📊';

  section.innerHTML = `
    <div class="card" style="margin-bottom:var(--space-lg);">
      <div class="video-header">
        <img src="${v.thumbnail_url || 'https://via.placeholder.com/200x113?text=No+Thumbnail'}"
             alt="Thumbnail" class="video-header-thumb">
        <div class="video-header-info">
          <div class="video-header-title">${escapeHtml(v.title)}</div>
          <div class="video-header-meta">
            <span>👁️ ${formatNumber(v.view_count || 0)} views</span>
            <span>👍 ${formatNumber(v.like_count || 0)}</span>
            <span>💬 ${formatNumber(v.comment_count || 0)}</span>
            <span>⏱️ ${formatDuration(v.duration)}</span>
            <span>📅 ${formatDate(v.published_at)}</span>
          </div>
          <div style="display:flex;gap:var(--space-sm);flex-wrap:wrap;align-items:center;">
            <span class="video-header-badge ${badgeClass}">${badgeIcon} ${classification}</span>
            ${d.is_mock ? `<span class="mock-badge">🔄 Estimated Data</span>` : `<span class="mock-badge" style="background:rgba(16,185,129,0.12);color:#10B981;">✓ Live Data</span>`}
            ${d.analytics_source ? `<span style="font-size:0.68rem;color:var(--text-muted);">Source: ${d.analytics_source}</span>` : ''}
          </div>
        </div>
      </div>
    </div>`;
}

// ─────────────────────────────────────────────────────────────────────────────
// PERFORMANCE SCORE
// ─────────────────────────────────────────────────────────────────────────────
function renderPerformanceScore() {
  const section = document.getElementById('performanceScoreSection');
  if (!section) return;

  const score = analyticsData.performance_score || 0;
  const engagementScore = analyticsData.engagement_score || 0;
  const retentionScore = analyticsData.retention_score || 0;
  const ctrScore = analyticsData.ctr_score || 0;

  const circumference = 2 * Math.PI * 42; // r=42
  const offset = circumference - (score / 100) * circumference;

  const scoreColor = score >= 85 ? '#10B981' : score >= 70 ? '#3B82F6' : score >= 45 ? '#F59E0B' : '#EF4444';

  section.innerHTML = `
    <div class="card" style="margin-bottom:var(--space-lg);">
      <div class="performance-score-card">
        <div class="score-ring">
          <svg viewBox="0 0 100 100">
            <circle class="score-ring-bg" cx="50" cy="50" r="42"/>
            <circle class="score-ring-fill" cx="50" cy="50" r="42"
                    stroke="${scoreColor}"
                    stroke-dasharray="${circumference}"
                    stroke-dashoffset="${offset}"/>
          </svg>
          <div class="score-text">
            <div class="score-value" style="color:${scoreColor}">${score}</div>
            <div class="score-label">Score</div>
          </div>
        </div>
        <div class="score-details">
          <div class="score-detail-item">
            <div class="score-detail-value">${engagementScore}</div>
            <div class="score-detail-label">Engagement</div>
          </div>
          <div class="score-detail-item">
            <div class="score-detail-value">${retentionScore}</div>
            <div class="score-detail-label">Retention</div>
          </div>
          <div class="score-detail-item">
            <div class="score-detail-value">${ctrScore}</div>
            <div class="score-detail-label">CTR</div>
          </div>
        </div>
      </div>
    </div>`;
}

// ─────────────────────────────────────────────────────────────────────────────
// KPI METRICS
// ─────────────────────────────────────────────────────────────────────────────
function renderKPIMetrics() {
  const section = document.getElementById('kpiMetricsSection');
  if (!section) return;

  const m = analyticsData.metrics || {};

  const kpis = [
    { icon: '👁️', value: formatNumber(m.views || 0), label: 'Views' },
    { icon: '⏱️', value: formatWatchTime(m.watch_time_hours || 0), label: 'Watch Time' },
    { icon: '📏', value: formatDuration(m.average_view_duration || 0), label: 'Avg. View Duration' },
    { icon: '➕', value: formatNumber(m.subscribers_gained || 0), label: 'Subs Gained' },
    { icon: '👍', value: formatNumber(m.likes || 0), label: 'Likes' },
    { icon: '💬', value: formatNumber(m.comments || 0), label: 'Comments' },
    { icon: '🔗', value: formatNumber(m.shares || 0), label: 'Shares' },
    { icon: '📈', value: `${m.ctr || 0}%`, label: 'CTR' },
    { icon: '👀', value: formatNumber(m.impressions || 0), label: 'Impressions' },
    { icon: '💵', value: m.estimated_revenue ? `$${m.estimated_revenue.toFixed(2)}` : 'N/A', label: 'Est. Revenue' },
    { icon: '📊', value: `${m.impression_ctr || 0}%`, label: 'Impression CTR' },
    { icon: '❤️', value: `${m.engagement_rate || 0}%`, label: 'Engagement Rate' },
  ];

  section.innerHTML = `
    <div class="card" style="margin-bottom:var(--space-lg);">
      <div class="card-header">
        <span class="card-title">Performance Metrics</span>
      </div>
      <div style="padding:var(--space-lg);">
        <div class="kpi-grid">
          ${kpis.map(kpi => `
            <div class="kpi-card">
              <div class="kpi-icon">${kpi.icon}</div>
              <div class="kpi-value">${kpi.value}</div>
              <div class="kpi-label">${kpi.label}</div>
            </div>
          `).join('')}
        </div>
      </div>
    </div>`;
}

// ─────────────────────────────────────────────────────────────────────────────
// VIEWS OVER TIME (line chart)
// ─────────────────────────────────────────────────────────────────────────────
function renderViewsOverTime() {
  const section = document.getElementById('viewsOverTimeSection');
  if (!section) return;

  const viewsOverTime = analyticsData.views_over_time || [];

  if (!viewsOverTime || viewsOverTime.length === 0) {
    section.innerHTML = '';
    return;
  }

  section.innerHTML = `
    <div class="card" style="margin-bottom:var(--space-lg);">
      <div class="card-header">
        <span class="card-title">Views Over Time</span>
      </div>
      <div class="chart-container">
        <canvas id="viewsOverTimeChart"></canvas>
      </div>
    </div>`;

  setTimeout(() => {
    const ctx = document.getElementById('viewsOverTimeChart');
    if (!ctx) return;

    const labels = viewsOverTime.map(v => v.date);
    const views = viewsOverTime.map(v => v.views);

    chartInstances.viewsOverTimeChart = new Chart(ctx, {
      type: 'line',
      data: {
        labels,
        datasets: [{
          label: 'Daily Views',
          data: views,
          borderColor: '#3B82F6',
          backgroundColor: (ctx) => {
            const gradient = ctx.chart.ctx.createLinearGradient(0, 0, 0, 200);
            gradient.addColorStop(0, 'rgba(59, 130, 246, 0.2)');
            gradient.addColorStop(1, 'rgba(59, 130, 246, 0.0)');
            return gradient;
          },
          fill: true,
          tension: 0.3,
          pointRadius: 1,
          pointHoverRadius: 4,
          borderWidth: 2,
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: true,
        scales: {
          x: {
            ticks: { color: '#64748B', font: { size: 9 }, maxTicksLimit: 10 },
            grid: { color: 'rgba(255,255,255,0.04)' },
          },
          y: {
            ticks: { color: '#64748B', font: { size: 9 } },
            grid: { color: 'rgba(255,255,255,0.04)' },
            beginAtZero: true,
          }
        },
        plugins: {
          legend: { display: false },
          tooltip: {
            callbacks: {
              label: (ctx) => `${formatNumber(ctx.parsed.y)} views`
            }
          }
        },
        interaction: { intersect: false, mode: 'index' },
      }
    });
  }, 50);
}

// ─────────────────────────────────────────────────────────────────────────────
// TRAFFIC SOURCES (donut chart)
// ─────────────────────────────────────────────────────────────────────────────
function renderTrafficSources() {
  const section = document.getElementById('trafficSourcesSection');
  if (!section) return;

  const sources = analyticsData.traffic_sources || [];

  if (sources.length === 0) {
    section.innerHTML = `<div class="card"><div class="card-header"><span class="card-title">Traffic Sources</span></div><div style="padding:var(--space-lg);color:var(--text-muted);text-align:center;">No traffic source data available.</div></div>`;
    return;
  }

  section.innerHTML = `
    <div class="card" style="height:100%;">
      <div class="card-header">
        <span class="card-title">Traffic Sources</span>
      </div>
      <div class="chart-container">
        <canvas id="trafficChart"></canvas>
      </div>
    </div>`;

  // Render chart after DOM update
  setTimeout(() => {
    const ctx = document.getElementById('trafficChart');
    if (!ctx) return;

    const labels = sources.map(s => s.source);
    const data = sources.map(s => s.percentage);
    const colors = [
      '#6C63FF', '#3B82F6', '#10B981', '#F59E0B',
      '#EF4444', '#8B5CF6', '#EC4899', '#14B8A6'
    ];

    chartInstances.trafficChart = new Chart(ctx, {
      type: 'doughnut',
      data: {
        labels,
        datasets: [{
          data,
          backgroundColor: colors.slice(0, labels.length),
          borderWidth: 0,
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: true,
        plugins: {
          legend: {
            position: 'bottom',
            labels: {
              color: '#94A3B8',
              font: { size: 11 },
              padding: 12,
              usePointStyle: true,
            }
          },
          tooltip: {
            callbacks: {
              label: (ctx) => `${ctx.label}: ${ctx.parsed}%`
            }
          }
        }
      }
    });
  }, 50);
}

// ─────────────────────────────────────────────────────────────────────────────
// DEVICE TYPES (bar chart)
// ─────────────────────────────────────────────────────────────────────────────
function renderDeviceChart(devices) {
  // Renders inside the audience section, no separate canvas needed
  // Just find existing device list and convert to bar chart
  setTimeout(() => {
    const canvas = document.getElementById('deviceBarChart');
    if (!canvas || !devices || devices.length === 0) return;

    chartInstances.deviceBarChart = new Chart(canvas, {
      type: 'bar',
      data: {
        labels: devices.map(d => d.device),
        datasets: [{
          label: 'Device Type %',
          data: devices.map(d => d.percentage),
          backgroundColor: ['#6C63FF', '#3B82F6', '#10B981', '#F59E0B'],
          borderRadius: 4,
          maxBarThickness: 40,
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: true,
        indexAxis: 'y',
        scales: {
          x: {
            ticks: { color: '#64748B', font: { size: 9 }, callback: (v) => `${v}%` },
            grid: { color: 'rgba(255,255,255,0.04)' },
            max: 100,
          },
          y: {
            ticks: { color: '#94A3B8', font: { size: 10 } },
            grid: { display: false },
          }
        },
        plugins: {
          legend: { display: false },
          tooltip: { callbacks: { label: (ctx) => `${ctx.parsed.x}%` } }
        },
      }
    });
  }, 50);
}

// ─────────────────────────────────────────────────────────────────────────────
// AUDIENCE INSIGHTS
// ─────────────────────────────────────────────────────────────────────────────
function renderAudienceInsights() {
  const section = document.getElementById('audienceSection');
  if (!section) return;

  const audience = analyticsData.audience || {};
  const countries = audience.top_countries || [];
  const devices = audience.device_types || [];
  const returningNew = audience.returning_vs_new || { returning: 0, new: 0 };
  const subNonSub = audience.subscriber_vs_non || { subscriber: 0, non_subscriber: 0 };

  const deviceIcons = { Mobile: '📱', Desktop: '💻', Tablet: '📟', TV: '📺' };

  const colors = ['#6C63FF', '#3B82F6', '#10B981', '#F59E0B', '#EF4444'];

  // Country flags mapping (simple)
  const countryFlags = {
    'United States': '🇺🇸', 'India': '🇮🇳', 'United Kingdom': '🇬🇧',
    'Canada': '🇨🇦', 'Australia': '🇦🇺', 'Germany': '🇩🇪',
    'France': '🇫🇷', 'Brazil': '🇧🇷', 'Japan': '🇯🇵',
    'South Korea': '🇰🇷', 'Russia': '🇷🇺', 'Mexico': '🇲🇽',
    'Indonesia': '🇮🇩', 'Turkey': '🇹🇷', 'Spain': '🇪🇸',
  };

  section.innerHTML = `
    <div class="card" style="height:100%;">
      <div class="card-header">
        <span class="card-title">Audience Insights</span>
      </div>
      <div class="audience-grid">
        <div>
          <div class="audience-section-title">Top Countries</div>
          <div class="audience-country-list">
            ${countries.slice(0, 5).map((c, i) => `
              <div class="audience-country-item">
                <span class="audience-country-flag">${countryFlags[c.country] || '🌍'}</span>
                <span class="audience-country-name">${c.country}</span>
                <div class="audience-country-bar">
                  <div class="audience-country-fill" style="width:${c.percentage}%;background:${colors[i]};"></div>
                </div>
                <span class="audience-country-pct">${c.percentage}%</span>
              </div>
            `).join('')}
          </div>
        </div>
        <div>
          <div class="audience-section-title">Device Types</div>
          <div style="height:160px;margin-bottom:var(--space-md);">
            <canvas id="deviceBarChart"></canvas>
          </div>

          <div class="audience-section-title" style="margin-top:var(--space-lg);">Viewer Type</div>
          <div class="split-row">
            <div class="split-item returning">
              <div class="split-value">${returningNew.returning}%</div>
              <div class="split-label">Returning</div>
            </div>
            <div class="split-item new">
              <div class="split-value">${returningNew.new}%</div>
              <div class="split-label">New</div>
            </div>
          </div>

          <div class="audience-section-title" style="margin-top:var(--space-md);">Subscription</div>
          <div class="split-row">
            <div class="split-item subscriber">
              <div class="split-value">${subNonSub.subscriber}%</div>
              <div class="split-label">Subscriber</div>
            </div>
            <div class="split-item non-sub">
              <div class="split-value">${subNonSub.non_subscriber}%</div>
              <div class="split-label">Non-Subscriber</div>
            </div>
          </div>
        </div>
      </div>
    </div>`;
}

// ─────────────────────────────────────────────────────────────────────────────
// RETENTION ANALYSIS (line chart)
// ─────────────────────────────────────────────────────────────────────────────
function renderRetention() {
  const section = document.getElementById('retentionSection');
  if (!section) return;

  const retention = analyticsData.retention || {};
  const points = retention.points || [];
  const avgPct = retention.average_percentage_viewed || 0;
  const dropOffs = retention.drop_off_points || [];
  const bestTimestamps = retention.best_performing_timestamps || [];

  section.innerHTML = `
    <div class="card" style="margin-bottom:var(--space-lg);">
      <div class="card-header">
        <span class="card-title">Audience Retention</span>
      </div>
      <div class="chart-container">
        <canvas id="retentionChart"></canvas>
      </div>
      <div class="retention-info">
        <div class="retention-stat">
          <div class="retention-stat-value">${avgPct}%</div>
          <div class="retention-stat-label">Avg. Viewed</div>
        </div>
        ${dropOffs.slice(0, 3).map(d => `
          <div class="retention-stat">
            <div class="retention-stat-value">-${d.percentage}%</div>
            <div class="retention-stat-label">${escapeHtml(d.label)}</div>
          </div>
        `).join('')}
      </div>
      ${bestTimestamps.length > 0 ? `
      <div style="padding:0 var(--space-lg) var(--space-lg);border-top:1px solid var(--border);padding-top:var(--space-md);">
        <div style="font-size:0.75rem;font-weight:700;color:var(--text-muted);margin-bottom:var(--space-sm);text-transform:uppercase;letter-spacing:0.04em;">Best Performing Segments</div>
        <div style="display:flex;flex-wrap:wrap;gap:var(--space-sm);">
          ${bestTimestamps.map(t => `
            <span style="background:rgba(16,185,129,0.1);color:var(--success);padding:4px 12px;border-radius:var(--radius-full);font-size:0.78rem;font-weight:600;">
              ${formatTimestamp(t.at_seconds)} – ${escapeHtml(t.label)}
            </span>
          `).join('')}
        </div>
      </div>` : ''}
    </div>`;

  // Render retention chart
  setTimeout(() => {
    const ctx = document.getElementById('retentionChart');
    if (!ctx) return;

    const labels = points.map(p => `${p.percentage_watched}%`);
    const data = points.map(p => p.viewer_percentage);

    chartInstances.retentionChart = new Chart(ctx, {
      type: 'line',
      data: {
        labels,
        datasets: [{
          label: 'Viewers Retained',
          data,
          borderColor: '#6C63FF',
          backgroundColor: (ctx) => {
            const gradient = ctx.chart.ctx.createLinearGradient(0, 0, 0, 300);
            gradient.addColorStop(0, 'rgba(108, 99, 255, 0.2)');
            gradient.addColorStop(1, 'rgba(108, 99, 255, 0.0)');
            return gradient;
          },
          fill: true,
          tension: 0.4,
          pointRadius: 2,
          pointHoverRadius: 5,
          borderWidth: 2,
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: true,
        scales: {
          x: {
            display: true,
            title: {
              display: true,
              text: 'Percentage of Video Watched',
              color: '#64748B',
              font: { size: 10 },
            },
            ticks: {
              color: '#64748B',
              font: { size: 9 },
              maxTicksLimit: 10,
            },
            grid: { color: 'rgba(255,255,255,0.04)' },
          },
          y: {
            display: true,
            title: {
              display: true,
              text: 'Viewers (%)',
              color: '#64748B',
              font: { size: 10 },
            },
            ticks: {
              color: '#64748B',
              font: { size: 9 },
              callback: (v) => `${v}%`,
            },
            grid: { color: 'rgba(255,255,255,0.04)' },
            min: 0,
            max: 100,
          }
        },
        plugins: {
          legend: { display: false },
          tooltip: {
            callbacks: {
              label: (ctx) => `${ctx.parsed.y}% viewers retained`
            }
          }
        },
        interaction: {
          intersect: false,
          mode: 'index',
        },
      }
    });
  }, 50);
}

// ─────────────────────────────────────────────────────────────────────────────
// KEYWORD PERFORMANCE
// ─────────────────────────────────────────────────────────────────────────────
function renderKeywords() {
  const section = document.getElementById('keywordsSection');
  if (!section) return;

  const keywords = analyticsData.keywords || [];

  if (!keywords || keywords.length === 0) {
    section.innerHTML = '';
    return;
  }

  // Sort by impressions descending
  const sorted = [...keywords].sort((a, b) => b.impressions - a.impressions);

  section.innerHTML = `
    <div class="card" style="margin-bottom:var(--space-lg);">
      <div class="card-header">
        <span class="card-title">Keyword Performance</span>
        <span style="font-size:0.75rem;color:var(--text-muted);">${keywords.length} keywords</span>
      </div>
      <div style="overflow-x:auto;padding:0 var(--space-sm) var(--space-sm);">
        <table class="keywords-table">
          <thead>
            <tr>
              <th>Search Term</th>
              <th style="text-align:right;">Impressions</th>
              <th style="text-align:right;">Clicks</th>
              <th style="text-align:right;">CTR</th>
            </tr>
          </thead>
          <tbody>
            ${sorted.map(k => `
              <tr>
                <td><span class="keyword-term">${escapeHtml(k.term)}</span></td>
                <td style="text-align:right;">${formatNumber(k.impressions)}</td>
                <td style="text-align:right;">${formatNumber(k.clicks)}</td>
                <td style="text-align:right;font-weight:600;color:${k.ctr > 5 ? 'var(--success)' : k.ctr > 2 ? 'var(--text-primary)' : 'var(--text-muted)'}">${k.ctr}%</td>
              </tr>
            `).join('')}
          </tbody>
        </table>
      </div>
    </div>`;
}

// ─────────────────────────────────────────────────────────────────────────────
// INSIGHTS
// ─────────────────────────────────────────────────────────────────────────────
function renderInsights() {
  const section = document.getElementById('insightsSection');
  if (!section) return;

  const insights = analyticsData.insights || [];

  if (!insights || insights.length === 0) {
    section.innerHTML = '';
    return;
  }

  const typeIcons = {
    positive: '✅',
    warning: '⚠️',
    info: '💡',
  };

  section.innerHTML = `
    <div class="card" style="margin-bottom:var(--space-lg);">
      <div class="card-header">
        <span class="card-title">Content Quality Insights</span>
        <span style="font-size:0.75rem;color:var(--text-muted);">Rule-based analysis</span>
      </div>
      <div class="insights-grid">
        ${insights.map(insight => `
          <div class="insight-item ${insight.type}">
            <span class="insight-icon">${typeIcons[insight.type] || '💡'}</span>
            <div class="insight-content">
              <div class="insight-category">${escapeHtml(insight.category)}</div>
              <div class="insight-message">${escapeHtml(insight.message)}</div>
            </div>
          </div>
        `).join('')}
      </div>
    </div>`;
}

// ─────────────────────────────────────────────────────────────────────────────
// CHART MANAGEMENT
// ─────────────────────────────────────────────────────────────────────────────
function destroyCharts() {
  Object.values(chartInstances).forEach(chart => {
    if (chart) {
      try { chart.destroy(); } catch (e) { /* ignore */ }
    }
  });
  chartInstances = {};
}

// ─────────────────────────────────────────────────────────────────────────────
// FORMATTERS
// ─────────────────────────────────────────────────────────────────────────────
function formatNumber(num) {
  if (num === null || num === undefined) return '0';
  if (num >= 1_000_000) return (num / 1_000_000).toFixed(1) + 'M';
  if (num >= 1_000)     return (num / 1_000).toFixed(1) + 'K';
  return String(num);
}

function formatWatchTime(hours) {
  if (hours >= 1000) return (hours / 1000).toFixed(1) + 'K hrs';
  if (hours >= 1) return hours.toFixed(1) + ' hrs';
  return (hours * 60).toFixed(0) + ' min';
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

function formatDate(dateString) {
  if (!dateString) return 'Unknown';
  try {
    const d = new Date(dateString);
    return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
  } catch (e) {
    return 'Unknown';
  }
}

function formatDuration(duration) {
  if (duration === null || duration === undefined) return '0:00';
  let total;
  if (typeof duration === 'number') {
    total = Math.floor(duration);
  } else if (typeof duration === 'string') {
    if (/^\d+$/.test(duration)) {
      total = parseInt(duration, 10);
    } else {
      const m = duration.match(/PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?/);
      if (!m) return '0:00';
      total = (parseInt(m[1]||0)*3600) + (parseInt(m[2]||0)*60) + parseInt(m[3]||0);
    }
  } else { return '0:00'; }
  const h = Math.floor(total / 3600);
  const m = Math.floor((total % 3600) / 60);
  const s = total % 60;
  return h > 0
    ? `${h}:${String(m).padStart(2,'0')}:${String(s).padStart(2,'0')}`
    : `${m}:${String(s).padStart(2,'0')}`;
}

function formatTimestamp(seconds) {
  if (!seconds) return '0:00';
  const m = Math.floor(seconds / 60);
  const s = seconds % 60;
  return `${m}:${String(s).padStart(2, '0')}`;
}

function escapeHtml(text) {
  if (text === null || text === undefined) return '';
  const d = document.createElement('div');
  d.textContent = text;
  return d.innerHTML;
}

// ─────────────────────────────────────────────────────────────────────────────
// MISC UI
// ─────────────────────────────────────────────────────────────────────────────
function showNoChannelState() {
  document.querySelector('.page-content').innerHTML = `
    <div style="text-align:center;padding:80px 20px;">
      <div style="font-size:5rem;margin-bottom:24px;">📺</div>
      <h2 style="margin-bottom:12px;">No YouTube Channel Connected</h2>
      <p style="color:var(--text-muted);margin-bottom:32px;max-width:500px;margin-left:auto;margin-right:auto;">
        Connect your YouTube channel to analyse your video performance.
      </p>
      <button class="btn btn-primary" onclick="window.location.href='channel.html'">
        🔗 Connect YouTube Channel
      </button>
    </div>`;
}

function updateSidebar(user) {
  const name   = document.querySelector('.sidebar-user .user-name');
  const avatar = document.querySelector('.sidebar-user .avatar');
  if (name) name.textContent = user.full_name || user.email;
  if (avatar) {
    if (user.avatar_url) {
      avatar.style.backgroundImage = `url(${user.avatar_url})`;
      avatar.style.backgroundSize  = 'cover';
      avatar.textContent = '';
    } else {
      avatar.textContent = user.full_name
        ? user.full_name.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2)
        : user.email[0].toUpperCase();
    }
  }
}

function showPageLoading(show) {
  const el = document.querySelector('.page-content');
  if (el) {
    el.style.opacity = show ? '0.6' : '1';
    el.style.pointerEvents = show ? 'none' : 'auto';
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// TOAST NOTIFICATIONS
// ─────────────────────────────────────────────────────────────────────────────
function showToast(message, type = 'info') {
  const existing = document.querySelector('.custom-toast');
  if (existing) existing.remove();

  const toast = document.createElement('div');
  toast.className = 'custom-toast';
  toast.style.cssText = `
    position: fixed; bottom: 24px; right: 24px; z-index: 10000;
    padding: 12px 20px; border-radius: 10px; font-size: 0.85rem;
    font-weight: 600; color: white; max-width: 400px;
    box-shadow: 0 8px 32px rgba(0,0,0,0.3);
    animation: slideIn 0.3s ease;
    background: ${type === 'error' ? '#EF4444' : type === 'success' ? '#10B981' : '#3B82F6'};
  `;
  toast.textContent = message;
  document.body.appendChild(toast);

  // Inject animation
  if (!document.getElementById('toastAnim')) {
    const style = document.createElement('style');
    style.id = 'toastAnim';
    style.textContent = `
      @keyframes slideIn { from { transform: translateX(100%); opacity: 0; } to { transform: translateX(0); opacity: 1; } }
      .custom-toast { transition: opacity 0.3s; }
    `;
    document.head.appendChild(style);
  }

  setTimeout(() => {
    toast.style.opacity = '0';
    setTimeout(() => toast.remove(), 300);
  }, 4000);
}