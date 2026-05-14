/**
 * AI Generator – Step-by-step workflow
 *
 * Step 1: Generate Title   → renders title cards with Apply button
 * Step 2: Apply Title      → sets appliedTitle, updates topic input
 * Step 3: Generate Description → requires titles to exist
 * Step 4: Generate Tags    → requires titles to exist
 *
 * Each step makes exactly ONE API call.
 * State is persisted to sessionStorage so refreshing the page restores progress.
 */

// Protect this page – require authentication
if (!requireAuth()) {
  // User will be redirected to login
}

// ─── State ────────────────────────────────────────────────────────────────────
const state = {
  generatedTitles: [],         // array of { title, seo_score, reasoning }
  generatedDescription: null,  // object from API
  generatedTags: null,         // object from API
  appliedTitle: null,          // string — the title the user clicked "Apply" on
  isGeneratingTitle: false,
  isGeneratingDescription: false,
  isGeneratingTags: false,
  currentStep: 0,              // 0=idle, 1=titles done, 2=title applied, 3=desc done, 4=tags done
};

// sessionStorage key
const _SS_KEY = 'vt_gen_state';

// ─── Persistence ──────────────────────────────────────────────────────────────
function _saveState() {
  try {
    // Don't persist the "isGenerating" flags — they should always start false
    const toSave = Object.assign({}, state, {
      isGeneratingTitle: false,
      isGeneratingDescription: false,
      isGeneratingTags: false,
    });
    sessionStorage.setItem(_SS_KEY, JSON.stringify(toSave));
  } catch (e) { /* sessionStorage full — ignore */ }
}

function _loadState() {
  try {
    const raw = sessionStorage.getItem(_SS_KEY);
    if (!raw) return;
    const saved = JSON.parse(raw);
    Object.assign(state, saved);
  } catch (e) { /* ignore */ }
}

// ─── Boot ─────────────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  // Restore session state
  _loadState();

  // Character counters
  updateCharCount('videoTopic', 'topicCount', 100);
  updateCharCount('videoDesc', 'descCount', 500);

  // Pre-fill from URL param (coming from analyzer)
  const urlParams = new URLSearchParams(window.location.search);
  const videoIdFromUrl = urlParams.get('video');
  if (videoIdFromUrl) {
    loadVideoContext(videoIdFromUrl);
  }

  // Load user for sidebar
  loadUser();

  // Restore UI from saved state
  _restoreUI();
});

// ─── Restore UI after page load / session restore ─────────────────────────────
function _restoreUI() {
  // Restore topic input if we have an applied title
  if (state.appliedTitle) {
    const topicInput = document.getElementById('videoTopic');
    if (topicInput && !topicInput.value) {
      topicInput.value = state.appliedTitle;
      updateCharCount('videoTopic', 'topicCount', 100);
    }
  }

  if (state.currentStep >= 1) {
    // Titles were generated
    _enableDescAndTagsButtons();
    _updateStepIndicator(1, 'done');
    _setButtonDone('btnGenerateTitle', '✓ Regenerate Title');
    document.getElementById('btnApplyTitle').style.display = 'block';
    _hideApplyHint();
    renderTitles();
  }

  if (state.currentStep >= 2) {
    // Title was applied
    _updateStepIndicator(2, 'done');
  }

  if (state.currentStep >= 3) {
    // Description was generated
    _updateStepIndicator(3, 'done');
    _setButtonDone('btnGenerateDescription', '✓ Regenerate Description');
    renderDescription();
  }

  if (state.currentStep >= 4) {
    // Tags were generated
    _updateStepIndicator(4, 'done');
    _setButtonDone('btnGenerateTags', '✓ Regenerate Tags');
    renderTags();
  }

  // Show empty states for panels not yet generated
  if (state.currentStep < 1) {
    _showEmptyPanel('titlesOutput', '📝', 'No titles yet', 'Click "✨ Generate Title" to start.');
  }
  if (state.currentStep < 3) {
    _showEmptyPanel('descriptionOutput', '📄', 'No description yet', 'Generate a title first, then click "📄 Generate Description".');
  }
  if (state.currentStep < 4) {
    _showEmptyPanel('tagsOutput', '🏷️', 'No tags yet', 'Generate a title first, then click "🏷️ Generate Tags".');
  }
}

// ─── Step 1: Generate Title ───────────────────────────────────────────────────
async function generateTitle() {
  const topic = document.getElementById('videoTopic').value.trim();
  const audience = document.getElementById('audience').value.trim();
  const keyword = document.getElementById('keyword').value.trim();
  const tone = document.getElementById('tone').value;

  if (!topic) {
    showToast('Please enter a video topic', 'error');
    return;
  }

  if (state.isGeneratingTitle) return;
  state.isGeneratingTitle = true;

  const btn = document.getElementById('btnGenerateTitle');
  _setButtonLoading(btn, 'Generating…');

  try {
    const result = await api.generateTitles({
      topic,
      keywords: keyword ? [keyword] : [],
      tone,
      target_audience: audience || undefined,
      count: 3,
    });

    // Normalise: API returns { titles: [{text, score, reasoning}] } (Pydantic model)
    // or legacy { titles: [{title, seo_score, reasoning}] }
    state.generatedTitles = (result.titles || []).map(t => ({
      title: t.text || t.title || '',
      seo_score: t.score !== undefined ? t.score : (t.seo_score || 0),
      reasoning: t.reasoning || '',
    }));

    state.currentStep = Math.max(state.currentStep, 1);
    _saveState();

    renderTitles();
    _enableDescAndTagsButtons();
    _updateStepIndicator(1, 'done');
    _setButtonDone(btn, '✓ Regenerate Title');

    // Show Apply Title button and hide hint
    document.getElementById('btnApplyTitle').style.display = 'block';
    _hideApplyHint();

    showToast('✅ Title generated! Click "Apply Title" on your preferred option.', 'success');

    // Switch to titles tab
    switchOutputTab('titles', document.getElementById('tab-titles'));

  } catch (err) {
    console.error('generateTitle error:', err);
    _handleApiError(err, btn, 'btnGenerateTitle', '✨ Generate Title');
  } finally {
    state.isGeneratingTitle = false;
  }
}

// ─── Step 2: Apply Title ──────────────────────────────────────────────────────
function applyTitle(titleText) {
  state.appliedTitle = titleText;
  state.currentStep = Math.max(state.currentStep, 2);
  _saveState();

  // Update topic input
  const topicInput = document.getElementById('videoTopic');
  if (topicInput) {
    topicInput.value = titleText;
    updateCharCount('videoTopic', 'topicCount', 100);
  }

  // Re-render titles to highlight the applied one
  renderTitles();

  _updateStepIndicator(2, 'done');

  showToast('✅ Title applied! Now generate your description.', 'success');
}

// Called by the sidebar "Apply Selected Title" button — applies the first title
function applySelectedTitle() {
  if (!state.generatedTitles || state.generatedTitles.length === 0) {
    showToast('Generate a title first', 'error');
    return;
  }
  const titleToApply = state.appliedTitle || state.generatedTitles[0].title;
  applyTitle(titleToApply);
}

// ─── Step 3: Generate Description ────────────────────────────────────────────
async function generateDescription() {
  if (!state.generatedTitles || state.generatedTitles.length === 0) {
    showToast('Generate a title first', 'error');
    return;
  }

  const topic = document.getElementById('videoTopic').value.trim();
  const keyword = document.getElementById('keyword').value.trim();
  const tone = document.getElementById('tone').value;
  const appliedTitle = state.appliedTitle || state.generatedTitles[0]?.title || topic;

  if (state.isGeneratingDescription) return;
  state.isGeneratingDescription = true;

  const btn = document.getElementById('btnGenerateDescription');
  _setButtonLoading(btn, 'Generating…');

  try {
    const result = await api.generateDescription({
      topic,
      title: appliedTitle,
      keywords: keyword ? [keyword] : [],
      tone,
      include_cta: true,
      include_timestamps: true,
    });

    state.generatedDescription = result;
    state.currentStep = Math.max(state.currentStep, 3);
    _saveState();

    renderDescription();
    _updateStepIndicator(3, 'done');
    _setButtonDone(btn, '✓ Regenerate Description');

    showToast('✅ Description generated!', 'success');

    // Switch to description tab
    switchOutputTab('description', document.getElementById('tab-description'));

  } catch (err) {
    console.error('generateDescription error:', err);
    _handleApiError(err, btn, 'btnGenerateDescription', '📄 Generate Description');
  } finally {
    state.isGeneratingDescription = false;
  }
}

// ─── Step 4: Generate Tags ────────────────────────────────────────────────────
async function generateTags() {
  if (!state.generatedTitles || state.generatedTitles.length === 0) {
    showToast('Generate a title first', 'error');
    return;
  }

  const topic = document.getElementById('videoTopic').value.trim();
  const keyword = document.getElementById('keyword').value.trim();
  const appliedTitle = state.appliedTitle || topic;

  if (state.isGeneratingTags) return;
  state.isGeneratingTags = true;

  const btn = document.getElementById('btnGenerateTags');
  _setButtonLoading(btn, 'Generating…');

  try {
    const result = await api.generateTags({
      topic,
      title: appliedTitle,
      keywords: keyword ? [keyword] : [],
      count: 20,
    });

    state.generatedTags = result;
    state.currentStep = Math.max(state.currentStep, 4);
    _saveState();

    renderTags();
    _updateStepIndicator(4, 'done');
    _setButtonDone(btn, '✓ Regenerate Tags');

    showToast('✅ Tags generated!', 'success');

    // Switch to tags tab
    switchOutputTab('tags', document.getElementById('tab-tags'));

  } catch (err) {
    console.error('generateTags error:', err);
    _handleApiError(err, btn, 'btnGenerateTags', '🏷️ Generate Tags');
  } finally {
    state.isGeneratingTags = false;
  }
}

// ─── Render: Titles ───────────────────────────────────────────────────────────
function renderTitles() {
  const container = document.getElementById('titlesOutput');
  if (!container) return;

  if (!state.generatedTitles || state.generatedTitles.length === 0) {
    _showEmptyPanel('titlesOutput', '📝', 'No titles yet', 'Click "✨ Generate Title" to start.');
    return;
  }

  const cards = state.generatedTitles.map((t, i) => {
    const isApplied = state.appliedTitle === t.title;
    const score = t.seo_score || 0;
    const scoreColor = score >= 80 ? 'var(--success)' : score >= 60 ? 'var(--warning)' : 'var(--danger)';
    const titleJson = JSON.stringify(t.title);

    return `
      <div class="output-item title-card"
           style="margin-bottom:var(--space-md);${isApplied ? 'border-color:var(--primary);background:var(--bg-surface);' : ''}">
        <div style="display:flex;justify-content:space-between;align-items:flex-start;gap:var(--space-sm);margin-bottom:var(--space-sm);">
          <div style="display:flex;align-items:center;gap:var(--space-sm);flex-wrap:wrap;">
            <span class="output-item-label">Option ${i + 1}${i === 0 ? ' ⭐' : ''}</span>
            <span style="font-size:0.72rem;font-weight:700;color:${scoreColor};background:${scoreColor}1a;padding:2px 8px;border-radius:99px;">${score}/100</span>
            ${isApplied ? '<span style="font-size:0.72rem;color:var(--primary);font-weight:600;">✓ Applied</span>' : ''}
          </div>
          <div style="display:flex;gap:var(--space-sm);flex-shrink:0;">
            <button class="btn btn-ghost btn-sm" onclick="_copyText(${titleJson}, this)">📋 Copy</button>
            <button class="btn btn-primary btn-sm" onclick="applyTitle(${titleJson})">✅ Apply</button>
          </div>
        </div>
        <div class="output-text" style="font-weight:600;line-height:1.4;margin-bottom:var(--space-sm);">${escapeHtml(t.title)}</div>
        ${t.reasoning ? `<div style="font-size:0.8rem;color:var(--text-muted);line-height:1.5;">${escapeHtml(t.reasoning)}</div>` : ''}
        <div style="margin-top:var(--space-sm);font-size:0.72rem;color:var(--text-muted);">📏 ${t.title.length} chars</div>
      </div>
    `;
  }).join('');

  container.innerHTML = `
    <p style="font-size:0.78rem;color:var(--text-muted);margin-bottom:var(--space-md);">
      ${state.generatedTitles.length} AI-optimized options. Click "✅ Apply" to use one as your title.
    </p>
    ${cards}
  `;
}

// ─── Render: Description ──────────────────────────────────────────────────────
function renderDescription() {
  const container = document.getElementById('descriptionOutput');
  if (!container) return;

  if (!state.generatedDescription) {
    _showEmptyPanel('descriptionOutput', '📄', 'No description yet', 'Generate a title first, then click "📄 Generate Description".');
    return;
  }

  const desc = state.generatedDescription;
  const descText = desc.description || '';
  const wordCount = desc.word_count || descText.split(/\s+/).filter(Boolean).length;
  const seoTips = desc.seo_tips || [];
  const descJson = JSON.stringify(descText);

  container.innerHTML = `
    <div class="output-item">
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:var(--space-md);">
        <span class="output-item-label">Full Description</span>
        <div style="display:flex;gap:var(--space-sm);">
          <button class="btn btn-ghost btn-sm" onclick="_copyText(${descJson}, this)">📋 Copy</button>
          <button class="btn btn-primary btn-sm" onclick="_applyDescription(${descJson})">✅ Apply Description</button>
        </div>
      </div>
      <div class="output-text" style="white-space:pre-wrap;line-height:1.7;max-height:320px;overflow-y:auto;margin-bottom:var(--space-md);">${escapeHtml(descText)}</div>
      <div style="display:flex;gap:var(--space-md);flex-wrap:wrap;font-size:0.72rem;color:var(--text-muted);margin-bottom:${seoTips.length ? 'var(--space-md)' : '0'};">
        <span>📝 ${wordCount} words</span>
        <span>📏 ${descText.length} chars</span>
        ${desc.includes_cta ? '<span style="color:var(--success);">✓ CTA included</span>' : ''}
        ${desc.includes_timestamps ? '<span style="color:var(--success);">✓ Timestamps</span>' : ''}
      </div>
      ${seoTips.length > 0 ? `
        <div style="border-top:1px solid var(--border);padding-top:var(--space-md);">
          <div style="font-size:0.82rem;font-weight:600;color:var(--text-secondary);margin-bottom:var(--space-sm);">💡 SEO Tips</div>
          <ul style="margin-left:var(--space-md);color:var(--text-secondary);font-size:0.85rem;line-height:1.7;">
            ${seoTips.map(tip => `<li>${escapeHtml(tip)}</li>`).join('')}
          </ul>
        </div>
      ` : ''}
    </div>
  `;
}

// ─── Render: Tags ─────────────────────────────────────────────────────────────
function renderTags() {
  const container = document.getElementById('tagsOutput');
  if (!container) return;

  if (!state.generatedTags) {
    _showEmptyPanel('tagsOutput', '🏷️', 'No tags yet', 'Generate a title first, then click "🏷️ Generate Tags".');
    return;
  }

  const tags = state.generatedTags;
  const allTags = tags.tags || tags.all_tags || [];

  container.innerHTML = `
    <div class="output-item">
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:var(--space-md);">
        <span class="output-item-label">${allTags.length} Tags Generated</span>
        <div style="display:flex;gap:var(--space-sm);">
          <button class="btn btn-ghost btn-sm" onclick="_copyAllTags(this)">📋 Copy All</button>
          <button class="btn btn-primary btn-sm" onclick="_applyTags()">✅ Apply Tags</button>
        </div>
      </div>
      <div style="display:flex;flex-wrap:wrap;gap:var(--space-sm);margin-bottom:var(--space-md);">
        ${allTags.map(tag => `
          <span class="tag-chip clickable" style="cursor:pointer;" onclick="_copyText(${JSON.stringify(tag)}, this)" title="Click to copy">
            #${escapeHtml(tag)}
          </span>
        `).join('')}
      </div>
      <div style="font-size:0.72rem;color:var(--text-muted);">
        💡 Click any tag to copy it individually, or use "Copy All" to copy all tags at once.
      </div>
    </div>
  `;
}

// ─── Apply helpers ────────────────────────────────────────────────────────────
function _applyDescription(text) {
  navigator.clipboard.writeText(text).then(() => {
    showToast('✅ Description copied to clipboard — paste it into YouTube Studio!', 'success');
  }).catch(() => {
    showToast('Failed to copy description', 'error');
  });
}

function _applyTags() {
  const tags = state.generatedTags;
  if (!tags) return;
  const allTags = tags.tags || tags.all_tags || [];
  navigator.clipboard.writeText(allTags.join(', ')).then(() => {
    showToast('✅ All tags copied to clipboard — paste them into YouTube Studio!', 'success');
  }).catch(() => {
    showToast('Failed to copy tags', 'error');
  });
}

function _copyAllTags(btn) {
  const tags = state.generatedTags;
  if (!tags) return;
  const allTags = tags.tags || tags.all_tags || [];
  _copyText(allTags.join(', '), btn);
}

// ─── Button state helpers ─────────────────────────────────────────────────────
function _setButtonLoading(btn, label) {
  if (!btn) return;
  btn.disabled = true;
  btn.innerHTML = `<span style="display:inline-block;width:12px;height:12px;border:2px solid currentColor;border-top-color:transparent;border-radius:50%;animation:_gen_spin 0.7s linear infinite;margin-right:6px;vertical-align:middle;"></span>${label}`;
}

function _setButtonDone(btnOrId, label) {
  const btn = typeof btnOrId === 'string' ? document.getElementById(btnOrId) : btnOrId;
  if (!btn) return;
  btn.disabled = false;
  btn.innerHTML = label;
}

function _enableDescAndTagsButtons() {
  const btnDesc = document.getElementById('btnGenerateDescription');
  const btnTags = document.getElementById('btnGenerateTags');
  if (btnDesc) { btnDesc.disabled = false; btnDesc.removeAttribute('title'); }
  if (btnTags) { btnTags.disabled = false; btnTags.removeAttribute('title'); }
}

function _hideApplyHint() {
  const hint = document.getElementById('applyTitleHint');
  if (hint) hint.style.display = 'none';
}

// ─── Step indicator ───────────────────────────────────────────────────────────
function _updateStepIndicator(stepNum, status) {
  const ind = document.getElementById(`step-ind-${stepNum}`);
  if (!ind) return;
  const dot = ind.querySelector('.step-dot');
  if (!dot) return;

  if (status === 'done') {
    dot.style.background = 'var(--success)';
    dot.style.color = '#fff';
    dot.textContent = '✓';
    ind.style.color = 'var(--success)';
    ind.style.fontWeight = '600';
  } else if (status === 'active') {
    dot.style.background = 'var(--primary)';
    dot.style.color = '#fff';
    ind.style.color = 'var(--primary)';
    ind.style.fontWeight = '600';
  } else {
    dot.style.background = 'var(--border)';
    dot.style.color = 'var(--text-muted)';
    ind.style.color = 'var(--text-muted)';
    ind.style.fontWeight = '';
  }
}

// ─── Error handling ───────────────────────────────────────────────────────────
function _handleApiError(err, btn, btnId, defaultLabel) {
  if (err.quotaExceeded) {
    const secs = err.retryAfterSeconds || 60;
    showToast(err.retryAfterMessage || `Quota exceeded. Retry in ${secs}s.`, 'error');
    _startRetryCountdown(secs, btn, defaultLabel);
  } else {
    showToast(`Error: ${err.message}`, 'error');
    _setButtonDone(btn, defaultLabel);
  }
}

/**
 * Show a live countdown in the button, then restore it when done.
 * Mirrors the pattern from analyzer.js _startRetryCountdown.
 */
function _startRetryCountdown(seconds, btn, defaultLabel) {
  if (!btn) return;
  let remaining = seconds;

  const tick = () => {
    if (remaining <= 0) {
      _setButtonDone(btn, defaultLabel);
      return;
    }
    btn.disabled = true;
    btn.innerHTML = `⏳ Retry in ${remaining}s`;
    remaining--;
    setTimeout(tick, 1000);
  };

  tick();
}

// ─── Empty state helper ───────────────────────────────────────────────────────
function _showEmptyPanel(containerId, icon, title, tip) {
  const container = document.getElementById(containerId);
  if (!container) return;
  container.innerHTML = `
    <div style="text-align:center;padding:var(--space-xl);color:var(--text-muted);">
      <div style="font-size:2rem;margin-bottom:var(--space-sm);">${icon}</div>
      <p style="font-weight:600;margin-bottom:var(--space-xs);">${title}</p>
      <p style="font-size:0.85rem;">${tip}</p>
    </div>
  `;
}

// ─── Copy helper ──────────────────────────────────────────────────────────────
function _copyText(text, btn) {
  navigator.clipboard.writeText(text).then(() => {
    if (btn) {
      const original = btn.innerHTML;
      btn.innerHTML = '✓ Copied!';
      btn.style.color = 'var(--success)';
      setTimeout(() => {
        btn.innerHTML = original;
        btn.style.color = '';
      }, 2000);
    } else {
      showToast('Copied to clipboard!', 'success');
    }
  }).catch(() => {
    showToast('Failed to copy', 'error');
  });
}

// ─── Tab switching ────────────────────────────────────────────────────────────
function switchOutputTab(tabName, btn) {
  document.querySelectorAll('.output-panel').forEach(p => p.classList.remove('active'));
  document.querySelectorAll('.output-tab').forEach(t => t.classList.remove('active'));
  const panel = document.getElementById(`panel-${tabName}`);
  if (panel) panel.classList.add('active');
  if (btn) btn.classList.add('active');
}

// ─── Character counter ────────────────────────────────────────────────────────
function updateCharCount(inputId, countId, max) {
  const input = document.getElementById(inputId);
  const counter = document.getElementById(countId);
  if (!input || !counter) return;
  const len = input.value.length;
  counter.textContent = len;
  counter.style.color = len > max * 0.9 ? 'var(--warning)' : 'var(--text-muted)';
}

// ─── Load video context (from analyzer via ?video= param) ─────────────────────
async function loadVideoContext(videoId) {
  try {
    const channels = await api.getYouTubeChannels();
    if (!channels || channels.length === 0) return;

    const videos = await api.getChannelVideos(channels[0].id, 100);
    const video = videos.find(v => v.id === videoId);

    if (video) {
      document.getElementById('videoTopic').value = video.title || '';
      document.getElementById('videoDesc').value = video.description
        ? video.description.substring(0, 500)
        : '';

      if (video.tags && video.tags.length > 0) {
        document.getElementById('keyword').value = video.tags[0];
      }

      updateCharCount('videoTopic', 'topicCount', 100);
      updateCharCount('videoDesc', 'descCount', 500);

      showToast('Video context loaded!', 'info');
    }
  } catch (error) {
    console.error('Failed to load video context:', error);
  }
}

// ─── Load user / sidebar ──────────────────────────────────────────────────────
async function loadUser() {
  try {
    const user = await api.getCurrentUser();
    updateSidebar(user);
  } catch (error) {
    console.error('Failed to load user:', error);
  }
}

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

// ─── HTML escape helpers ──────────────────────────────────────────────────────
function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = String(text);
  return div.innerHTML;
}

// ─── Inject spinner keyframe once ────────────────────────────────────────────
(function _injectSpinnerStyle() {
  if (document.getElementById('_gen_spinner_style')) return;
  const style = document.createElement('style');
  style.id = '_gen_spinner_style';
  style.textContent = '@keyframes _gen_spin { to { transform: rotate(360deg); } }';
  document.head.appendChild(style);
})();
