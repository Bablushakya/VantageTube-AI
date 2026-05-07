/**
 * Video SEO Analyzer
 *
 * Flow:
 *  1. Page loads → fetch video list only (no AI calls)
 *  2. User clicks a video → show its current title/description from DB
 *  3. User clicks "Generate AI SEO Content" → sequential AI calls:
 *       Step 1: generate titles   (await)
 *       Step 2: generate description (await, only after step 1 succeeds)
 *       Step 3: generate tags     (await, only after step 2 succeeds)
 *  4. isGenerating flag blocks any concurrent requests
 */

if (!requireAuth()) { /* redirected */ }

// ─── State ────────────────────────────────────────────────────────────────────
let channelVideos   = [];
let selectedVideo   = null;
let isGenerating    = false;   // global lock – no concurrent AI calls

let generatedContent = {
  titles:      null,
  description: null,
  tags:        null
};

let currentTab = 'titles';

// ─── sessionStorage cache key helpers ────────────────────────────────────────
// 6.2: Results are stored per video-id so navigating away and back restores
//      them instantly without re-generating (and without burning quota).
const _SS_PREFIX = 'vt_analyzer_';

function _cacheKey(videoId) {
  return `${_SS_PREFIX}${videoId}`;
}

function _saveToSession(videoId, content) {
  try {
    sessionStorage.setItem(_cacheKey(videoId), JSON.stringify({
      content,
      savedAt: Date.now()
    }));
  } catch (e) { /* sessionStorage full — ignore */ }
}

function _loadFromSession(videoId) {
  try {
    const raw = sessionStorage.getItem(_cacheKey(videoId));
    if (!raw) return null;
    const { content, savedAt } = JSON.parse(raw);
    // Expire after 30 minutes (session is short-lived anyway)
    if (Date.now() - savedAt > 30 * 60 * 1000) {
      sessionStorage.removeItem(_cacheKey(videoId));
      return null;
    }
    return content;
  } catch (e) { return null; }
}

// ─── Boot ─────────────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  const urlParams = new URLSearchParams(window.location.search);
  const videoIdFromUrl = urlParams.get('video');
  loadVideos(videoIdFromUrl);
  // 6.1: Load quota bar once on page load (non-blocking)
  _loadQuotaBar();
});

// ─────────────────────────────────────────────────────────────────────────────
// 6.1  QUOTA BAR
// Fetches quota once on load and renders a compact usage bar in the sidebar.
// Updates again after each successful generation.
// ─────────────────────────────────────────────────────────────────────────────
async function _loadQuotaBar() {
  try {
    const data = await api.getQuotaInfo();
    _renderQuotaBar(data.quota);
  } catch (e) {
    // Quota bar is non-critical — fail silently
  }
}

function _renderQuotaBar(quota) {
  const container = document.getElementById('quotaBarContainer');
  if (!container || !quota) return;

  const reqUsed  = quota.requests?.used_day  || 0;
  const reqLimit = quota.requests?.limit_day || 1500;
  const tokUsed  = quota.tokens?.used_day    || 0;
  const tokLimit = quota.tokens?.limit_day   || 500000;

  const reqPct = Math.min(100, Math.round((reqUsed / reqLimit) * 100));
  const tokPct = Math.min(100, Math.round((tokUsed / tokLimit) * 100));

  const _color = pct => pct >= 90 ? '#EF4444' : pct >= 70 ? '#F59E0B' : '#10B981';

  container.innerHTML = `
    <div style="padding:12px 16px;border-top:1px solid var(--border);">
      <div style="font-size:0.68rem;font-weight:600;text-transform:uppercase;letter-spacing:0.06em;
                  color:var(--text-muted);margin-bottom:8px;">AI Quota Today</div>

      <div style="margin-bottom:6px;">
        <div style="display:flex;justify-content:space-between;font-size:0.72rem;
                    color:var(--text-secondary);margin-bottom:3px;">
          <span>Requests</span>
          <span>${reqUsed} / ${reqLimit}</span>
        </div>
        <div style="height:4px;background:var(--bg-surface);border-radius:99px;overflow:hidden;">
          <div style="height:100%;width:${reqPct}%;background:${_color(reqPct)};
                      border-radius:99px;transition:width 0.4s ease;"></div>
        </div>
      </div>

      <div>
        <div style="display:flex;justify-content:space-between;font-size:0.72rem;
                    color:var(--text-secondary);margin-bottom:3px;">
          <span>Tokens</span>
          <span>${_fmtK(tokUsed)} / ${_fmtK(tokLimit)}</span>
        </div>
        <div style="height:4px;background:var(--bg-surface);border-radius:99px;overflow:hidden;">
          <div style="height:100%;width:${tokPct}%;background:${_color(tokPct)};
                      border-radius:99px;transition:width 0.4s ease;"></div>
        </div>
      </div>

      ${reqPct >= 90 ? `
        <div style="margin-top:8px;font-size:0.72rem;color:#EF4444;font-weight:600;">
          ⚠️ Quota almost exhausted — resets at midnight UTC
        </div>` : ''}
    </div>
  `;
}

function _fmtK(n) {
  if (n >= 1_000_000) return (n / 1_000_000).toFixed(1) + 'M';
  if (n >= 1_000)     return (n / 1_000).toFixed(1) + 'K';
  return String(n);
}

// ─────────────────────────────────────────────────────────────────────────────
// LOAD VIDEO LIST  (no AI calls here)
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

    // Pre-select from URL param or first video – but only show the detail panel,
    // do NOT auto-generate AI content.
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
    const score     = v.seo_score || 0;
    const thumbnail = v.thumbnail_url || 'https://via.placeholder.com/120x68?text=No+Thumbnail';
    return `
      <div class="video-selector-item" id="vs-${v.id}" onclick="selectVideo('${v.id}')">
        <div class="vs-thumb"
             style="background-image:url('${thumbnail}');background-size:cover;background-position:center;"></div>
        <div class="vs-info">
          <div class="vs-title">${escapeHtml(v.title)}</div>
          <div class="vs-views">👁️ ${formatNumber(v.view_count || 0)} · ${formatTimeAgo(v.published_at)}</div>
        </div>
        <span class="vs-score" style="color:${getSeoColor(score)};">${score}</span>
      </div>`;
  }).join('');
}

// ─────────────────────────────────────────────────────────────────────────────
// SELECT VIDEO  – shows current data, NO AI calls
// ─────────────────────────────────────────────────────────────────────────────
function selectVideo(videoId) {
  // Highlight in list
  document.querySelectorAll('.video-selector-item').forEach(el => el.classList.remove('selected'));
  const el = document.getElementById(`vs-${videoId}`);
  if (el) el.classList.add('selected');

  selectedVideo = channelVideos.find(v => v.id === videoId);
  if (!selectedVideo) return;

  // 6.2: Try to restore previously generated content from sessionStorage
  const cached = _loadFromSession(videoId);
  if (cached) {
    generatedContent = cached;
    currentTab = 'titles';
  } else {
    // Reset generated content whenever a new video is selected
    generatedContent = { titles: null, description: null, tags: null };
    currentTab = 'titles';
  }

  // Update URL
  const url = new URL(window.location);
  url.searchParams.set('video', videoId);
  window.history.pushState({}, '', url);

  // Render the detail panel with current DB data + generate button
  renderDetailPanel();
}

// ─────────────────────────────────────────────────────────────────────────────
// DETAIL PANEL  – shows current title/description + generate button
// ─────────────────────────────────────────────────────────────────────────────
function renderDetailPanel() {
  const panel = document.getElementById('analysisPanel');
  if (!panel || !selectedVideo) return;

  const v = selectedVideo;

  panel.innerHTML = `
    <!-- Video info card -->
    <div class="card" style="margin-bottom:var(--space-lg);">
      <div class="card-header">
        <span class="card-title">Video Details</span>
        <span style="font-size:0.75rem;color:var(--text-muted);">${formatTimeAgo(v.published_at)}</span>
      </div>
      <div style="display:flex;align-items:flex-start;gap:var(--space-lg);flex-wrap:wrap;">
        <img src="${v.thumbnail_url || 'https://via.placeholder.com/160x90?text=No+Thumbnail'}"
             alt="Thumbnail"
             style="width:160px;height:90px;border-radius:8px;object-fit:cover;flex-shrink:0;">
        <div style="flex:1;min-width:220px;">
          <div style="font-size:0.95rem;font-weight:700;color:var(--text-primary);margin-bottom:var(--space-sm);line-height:1.4;">
            ${escapeHtml(v.title)}
          </div>
          <div style="display:flex;flex-wrap:wrap;gap:var(--space-md);font-size:0.8rem;color:var(--text-muted);">
            <span>👁️ ${formatNumber(v.view_count || 0)}</span>
            <span>👍 ${formatNumber(v.like_count || 0)}</span>
            <span>💬 ${formatNumber(v.comment_count || 0)}</span>
            <span>⏱️ ${formatDuration(v.duration)}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Current content card -->
    <div class="card" style="margin-bottom:var(--space-lg);">
      <div class="card-header">
        <span class="card-title">Current Content (from Database)</span>
      </div>

      <div style="margin-bottom:var(--space-lg);">
        <div class="current-label">📌 Current Title</div>
        <div class="current-box">
          <div style="font-weight:600;line-height:1.4;margin-bottom:var(--space-sm);">${escapeHtml(v.title)}</div>
          <button class="btn btn-sm btn-ghost" onclick="copyToClipboard(${JSON.stringify(v.title)})">📋 Copy</button>
        </div>
      </div>

      <div>
        <div class="current-label">📄 Current Description</div>
        <div class="current-box" style="max-height:160px;overflow-y:auto;">
          <div style="font-size:0.9rem;line-height:1.6;white-space:pre-wrap;margin-bottom:var(--space-sm);">
            ${v.description ? escapeHtml(v.description) : '<span style="color:var(--text-muted);font-style:italic;">No description</span>'}
          </div>
          ${v.description ? `<button class="btn btn-sm btn-ghost" onclick="copyToClipboard(${JSON.stringify(v.description)})">📋 Copy</button>` : ''}
        </div>
      </div>
    </div>

    <!-- Generate button card -->
    <div class="card" style="margin-bottom:var(--space-lg);">
      <div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:var(--space-md);">
        <div>
          <div style="font-weight:600;margin-bottom:4px;">✨ AI SEO Content Generator</div>
          <div style="font-size:0.82rem;color:var(--text-muted);">
            Generates optimised titles → description → tags sequentially to respect API rate limits.
          </div>
          ${generatedContent.titles ? `
            <div style="margin-top:6px;font-size:0.75rem;color:var(--success);font-weight:600;">
              ✓ Results restored from session cache — no quota used
            </div>` : ''}
        </div>
        <div style="display:flex;gap:var(--space-sm);flex-wrap:wrap;align-items:center;">
          ${generatedContent.titles ? `
            <button class="btn btn-ghost btn-sm" onclick="_clearSessionAndRegen()"
                    title="Discard cached results and generate fresh content">
              🔄 Regenerate
            </button>` : ''}
          <button id="generateBtn"
                  class="btn btn-primary"
                  onclick="startSequentialGeneration()"
                  ${isGenerating ? 'disabled' : ''}>
            ${isGenerating ? '<span class="btn-spinner"></span> Generating…' : (generatedContent.titles ? '✅ Generated' : '🚀 Generate AI SEO Content')}
          </button>
        </div>
      </div>
    </div>

    <!-- Results area (shown after generation) -->
    <div id="resultsArea" style="display:${generatedContent.titles ? 'block' : 'none'};">
      ${renderResultsTabs()}
    </div>
  `;

  injectAnalyzerStyles();
}

// ─────────────────────────────────────────────────────────────────────────────
// SEQUENTIAL GENERATION  – the core of the fix
// ─────────────────────────────────────────────────────────────────────────────
async function startSequentialGeneration() {
  if (isGenerating) return;          // hard lock – ignore double-clicks
  if (!selectedVideo) return;

  isGenerating = true;
  setGenerateButton(true);

  const v       = selectedVideo;
  const topic   = v.title;
  const keywords = v.tags || [];

  try {
    // ── STEP 1: Titles ────────────────────────────────────────────────────────
    showStepStatus('titles', 'loading');

    generatedContent.titles = await api.generateTitles({
      topic,
      keywords,
      tone: 'engaging',
      target_audience: 'YouTube viewers',
      count: 5,
      video_id: v.id
    });

    showStepStatus('titles', 'done');

    // ── STEP 2: Description  (only runs after titles succeed) ─────────────────
    showStepStatus('description', 'loading');

    generatedContent.description = await api.generateDescription({
      topic,
      title: v.title,
      keywords,
      tone: 'engaging',
      target_audience: 'YouTube viewers',
      video_length: 'medium',
      include_timestamps: true,
      include_links: true,
      include_cta: true,
      video_id: v.id
    });

    showStepStatus('description', 'done');

    // ── STEP 3: Tags  (only runs after description succeeds) ──────────────────
    showStepStatus('tags', 'loading');

    generatedContent.tags = await api.generateTags({
      topic,
      title: v.title,
      keywords,
      count: 20,
      video_id: v.id
    });

    showStepStatus('tags', 'done');

    // Show results
    currentTab = 'titles';
    showResults();

    // 6.2: Persist results to sessionStorage so navigation doesn't lose them
    _saveToSession(v.id, generatedContent);

    // 6.1: Refresh quota bar to reflect the tokens just consumed
    _loadQuotaBar();

  } catch (err) {
    console.error('Generation error:', err);

    let msg;
    if (err.quotaExceeded) {
      const secs = err.retryAfterSeconds || 60;
      msg = err.retryAfterMessage || `Quota exceeded. Try again in ${secs} seconds.`;
      // Start a visible countdown in the UI
      _startRetryCountdown(secs);
    } else {
      msg = `Generation failed: ${err.message}`;
    }

    showToast(msg, 'error');
    showGenerationError(msg);
  } finally {
    isGenerating = false;
    setGenerateButton(false);
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// UI HELPERS FOR GENERATION FLOW
// ─────────────────────────────────────────────────────────────────────────────

/** Enable / disable the generate button */
function setGenerateButton(loading) {
  const btn = document.getElementById('generateBtn');
  if (!btn) return;
  btn.disabled = loading;
  btn.innerHTML = loading
    ? '<span class="btn-spinner"></span> Generating…'
    : '🚀 Generate AI SEO Content';
}

/**
 * Show a step status indicator inside the generate card.
 * Creates the progress area on first call.
 */
function showStepStatus(step, state) {
  // Ensure progress container exists
  let progress = document.getElementById('generationProgress');
  if (!progress) {
    const card = document.getElementById('generateBtn')?.closest('.card');
    if (!card) return;
    progress = document.createElement('div');
    progress.id = 'generationProgress';
    progress.style.cssText = 'margin-top:var(--space-md);display:flex;flex-direction:column;gap:8px;';
    card.appendChild(progress);
  }

  const icons = { titles: '📝', description: '📄', tags: '🏷️' };
  const labels = { titles: 'Titles', description: 'Description', tags: 'Tags' };

  let row = document.getElementById(`step-${step}`);
  if (!row) {
    row = document.createElement('div');
    row.id = `step-${step}`;
    row.style.cssText = 'display:flex;align-items:center;gap:10px;font-size:0.85rem;';
    progress.appendChild(row);
  }

  const spinnerHTML = `<span class="step-spinner"></span>`;
  const doneHTML    = `<span style="color:var(--success);">✓</span>`;

  row.innerHTML = state === 'loading'
    ? `${spinnerHTML} <span style="color:var(--text-secondary);">${icons[step]} Generating ${labels[step]}…</span>`
    : `${doneHTML} <span style="color:var(--text-muted);">${icons[step]} ${labels[step]} ready</span>`;
}

function showGenerationError(msg) {
  let progress = document.getElementById('generationProgress');
  if (!progress) return;
  progress.insertAdjacentHTML('beforeend', `
    <div style="color:var(--danger);font-size:0.85rem;margin-top:4px;">❌ ${escapeHtml(msg)}</div>
  `);
}

function showResults() {
  const area = document.getElementById('resultsArea');
  if (!area) return;
  area.style.display = 'block';
  area.innerHTML = renderResultsTabs();
}

/**
 * 6.2: Clear the sessionStorage cache for the current video and trigger
 * a fresh generation.  Called by the "Regenerate" button.
 */
function _clearSessionAndRegen() {
  if (!selectedVideo) return;
  sessionStorage.removeItem(_cacheKey(selectedVideo.id));
  generatedContent = { titles: null, description: null, tags: null };
  renderDetailPanel();
  startSequentialGeneration();
}

// ─────────────────────────────────────────────────────────────────────────────
// RESULTS TABS
// ─────────────────────────────────────────────────────────────────────────────
function renderResultsTabs() {
  return `
    <div class="card" style="margin-bottom:var(--space-lg);">
      <div style="display:flex;gap:0;border-bottom:1px solid var(--border-color);overflow-x:auto;">
        ${['titles','description','tags'].map(t => `
          <button class="tab-btn ${currentTab === t ? 'active' : ''}" onclick="switchTab('${t}')">
            ${{ titles:'📝 Titles', description:'📄 Description', tags:'🏷️ Tags' }[t]}
          </button>`).join('')}
      </div>
    </div>
    <div id="tabContent">${renderTabContent()}</div>
  `;
}

function switchTab(tab) {
  currentTab = tab;
  const content = document.getElementById('tabContent');
  if (content) content.innerHTML = renderTabContent();

  document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
  document.querySelectorAll('.tab-btn').forEach(b => {
    if (b.textContent.toLowerCase().includes(tab)) b.classList.add('active');
  });
}

function renderTabContent() {
  switch (currentTab) {
    case 'titles':      return renderTitlesTab();
    case 'description': return renderDescriptionTab();
    case 'tags':        return renderTagsTab();
    default:            return '';
  }
}

// ── Titles tab ────────────────────────────────────────────────────────────────
function renderTitlesTab() {
  if (!generatedContent.titles) {
    return loadingPlaceholder('Titles will appear here after generation.');
  }

  const titles = generatedContent.titles.titles || [];

  return `
    <div class="card">
      <div class="card-header">
        <span class="card-title">AI-Generated Titles</span>
        <span style="font-size:0.75rem;color:var(--text-muted);">${titles.length} options</span>
      </div>
      <div style="display:grid;gap:var(--space-md);">
        ${titles.map(t => `
          <div class="result-item">
            <div style="display:flex;justify-content:space-between;align-items:flex-start;gap:var(--space-sm);margin-bottom:var(--space-sm);">
              <div style="font-weight:600;flex:1;line-height:1.4;">${escapeHtml(t.title)}</div>
              <span class="score-badge">${t.seo_score || 0}/100</span>
            </div>
            <div style="font-size:0.82rem;color:var(--text-muted);margin-bottom:var(--space-sm);">${escapeHtml(t.reasoning || '')}</div>
            <button class="btn btn-sm btn-primary" onclick="copyToClipboard(${JSON.stringify(t.title)})">📋 Copy</button>
          </div>`).join('')}
      </div>
    </div>`;
}

// ── Description tab ───────────────────────────────────────────────────────────
function renderDescriptionTab() {
  if (!generatedContent.description) {
    return loadingPlaceholder('Description will appear here after generation.');
  }

  const desc = generatedContent.description;

  return `
    <div class="card">
      <div class="card-header">
        <span class="card-title">AI-Generated Description</span>
      </div>
      <div class="result-item" style="margin-bottom:var(--space-lg);">
        <div style="font-size:0.9rem;line-height:1.7;white-space:pre-wrap;max-height:320px;overflow-y:auto;margin-bottom:var(--space-md);">
          ${escapeHtml(desc.description || '')}
        </div>
        <button class="btn btn-sm btn-primary" onclick="copyToClipboard(${JSON.stringify(desc.description || '')})">📋 Copy Description</button>
      </div>
      ${desc.seo_tips && desc.seo_tips.length ? `
        <div>
          <div style="font-size:0.85rem;font-weight:600;color:var(--text-secondary);margin-bottom:var(--space-sm);">💡 SEO Tips</div>
          <ul style="margin-left:var(--space-md);color:var(--text-secondary);font-size:0.88rem;line-height:1.7;">
            ${desc.seo_tips.map(tip => `<li>${escapeHtml(tip)}</li>`).join('')}
          </ul>
        </div>` : ''}
    </div>`;
}

// ── Tags tab ──────────────────────────────────────────────────────────────────
function renderTagsTab() {
  if (!generatedContent.tags) {
    return loadingPlaceholder('Tags will appear here after generation.');
  }

  const tags = generatedContent.tags;
  const allTags = tags.tags || tags.all_tags || [];

  return `
    <div class="card">
      <div class="card-header">
        <span class="card-title">AI-Generated Tags</span>
        <span style="font-size:0.75rem;color:var(--text-muted);">${allTags.length} tags</span>
      </div>
      <div style="display:flex;flex-wrap:wrap;gap:var(--space-sm);margin-bottom:var(--space-lg);">
        ${allTags.map(t => `<span class="tag-chip accent">#${escapeHtml(t)}</span>`).join('')}
      </div>
      <button class="btn btn-sm btn-primary" onclick="copyToClipboard(${JSON.stringify(allTags.join(', '))})">📋 Copy All Tags</button>
    </div>`;
}

function loadingPlaceholder(msg) {
  return `
    <div class="card">
      <div style="text-align:center;padding:var(--space-xl);color:var(--text-muted);">
        <div style="font-size:2rem;margin-bottom:var(--space-sm);">✨</div>
        <p>${msg}</p>
      </div>
    </div>`;
}

// ─────────────────────────────────────────────────────────────────────────────
// RETRY COUNTDOWN
// ─────────────────────────────────────────────────────────────────────────────

/**
 * Show a live countdown inside the generate button area so the user knows
 * exactly when they can retry.  Automatically re-enables the button when done.
 */
function _startRetryCountdown(seconds) {
  const btn = document.getElementById('generateBtn');
  if (!btn) return;

  let remaining = seconds;

  const tick = () => {
    if (remaining <= 0) {
      // Re-enable the button
      isGenerating = false;
      setGenerateButton(false);

      // Remove any progress rows so the panel looks clean for the next attempt
      const progress = document.getElementById('generationProgress');
      if (progress) progress.remove();
      return;
    }

    btn.disabled = true;
    btn.innerHTML = `⏳ Retry in ${remaining}s`;
    remaining--;
    setTimeout(tick, 1000);
  };

  tick();
}

// ─────────────────────────────────────────────────────────────────────────────
// MISC UI
// ─────────────────────────────────────────────────────────────────────────────
function copyToClipboard(text) {
  navigator.clipboard.writeText(text)
    .then(() => showToast('✅ Copied to clipboard!', 'success'))
    .catch(() => showToast('Failed to copy', 'error'));
}

function showNoChannelState() {
  document.querySelector('.page-content').innerHTML = `
    <div style="text-align:center;padding:80px 20px;">
      <div style="font-size:5rem;margin-bottom:24px;">📺</div>
      <h2 style="margin-bottom:12px;">No YouTube Channel Connected</h2>
      <p style="color:var(--text-muted);margin-bottom:32px;max-width:500px;margin-left:auto;margin-right:auto;">
        Connect your YouTube channel to analyse your videos and get SEO optimisation insights.
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
  if (el) { el.style.opacity = show ? '0.6' : '1'; el.style.pointerEvents = show ? 'none' : 'auto'; }
}

// ─────────────────────────────────────────────────────────────────────────────
// FORMATTERS
// ─────────────────────────────────────────────────────────────────────────────
function formatNumber(num) {
  if (num >= 1_000_000) return (num / 1_000_000).toFixed(1) + 'M';
  if (num >= 1_000)     return (num / 1_000).toFixed(1) + 'K';
  return String(num);
}

function formatTimeAgo(dateString) {
  if (!dateString) return 'Unknown';
  const seconds = Math.floor((Date.now() - new Date(dateString)) / 1000);
  const intervals = { year:31536000, month:2592000, week:604800, day:86400, hour:3600, minute:60 };
  for (const [unit, s] of Object.entries(intervals)) {
    const n = Math.floor(seconds / s);
    if (n >= 1) return `${n} ${unit}${n > 1 ? 's' : ''} ago`;
  }
  return 'Just now';
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

function getSeoColor(score) {
  if (score >= 80) return 'var(--success)';
  if (score >= 60) return 'var(--warning)';
  return 'var(--danger)';
}

function escapeHtml(text) {
  const d = document.createElement('div');
  d.textContent = text;
  return d.innerHTML;
}

// ─────────────────────────────────────────────────────────────────────────────
// STYLES  (injected once)
// ─────────────────────────────────────────────────────────────────────────────
function injectAnalyzerStyles() {
  if (document.getElementById('analyzerStyles')) return;
  const s = document.createElement('style');
  s.id = 'analyzerStyles';
  s.textContent = `
    /* Tab buttons */
    .tab-btn {
      padding: 12px 18px;
      background: none;
      border: none;
      color: var(--text-secondary);
      font-size: 0.88rem;
      font-weight: 500;
      cursor: pointer;
      border-bottom: 2px solid transparent;
      white-space: nowrap;
      transition: color 0.2s, border-color 0.2s;
    }
    .tab-btn:hover { color: var(--text-primary); }
    .tab-btn.active { color: var(--accent-color); border-bottom-color: var(--accent-color); }

    /* Result items */
    .result-item {
      background: var(--bg-secondary);
      padding: var(--space-md);
      border-radius: 8px;
      border-left: 3px solid var(--accent-color);
    }

    /* Current content boxes */
    .current-label {
      font-size: 0.82rem;
      font-weight: 600;
      color: var(--text-muted);
      margin-bottom: var(--space-sm);
      text-transform: uppercase;
      letter-spacing: 0.04em;
    }
    .current-box {
      background: var(--bg-secondary);
      padding: var(--space-md);
      border-radius: 8px;
      border: 1px solid var(--border-color);
    }

    /* Score badge */
    .score-badge {
      background: var(--accent-color);
      color: white;
      padding: 2px 8px;
      border-radius: 4px;
      font-size: 0.75rem;
      font-weight: 700;
      white-space: nowrap;
      flex-shrink: 0;
    }

    /* Tag chips */
    .tag-chip {
      display: inline-block;
      background: var(--bg-tertiary);
      color: var(--text-secondary);
      padding: 4px 12px;
      border-radius: 20px;
      font-size: 0.82rem;
      font-weight: 500;
    }
    .tag-chip.accent {
      background: var(--accent-color);
      color: white;
    }

    /* Button spinner */
    .btn-spinner, .step-spinner {
      display: inline-block;
      width: 14px;
      height: 14px;
      border: 2px solid rgba(255,255,255,0.35);
      border-top-color: white;
      border-radius: 50%;
      animation: spin 0.7s linear infinite;
      vertical-align: middle;
    }
    .step-spinner {
      border-color: rgba(108,99,255,0.3);
      border-top-color: var(--accent-color);
    }
    @keyframes spin { to { transform: rotate(360deg); } }
  `;
  document.head.appendChild(s);
}
