/**
 * AI Generator Page Logic with API Integration
 * Handles AI content generation for titles, descriptions, tags, and thumbnail text
 */

// Protect this page - require authentication
if (!requireAuth()) {
  // User will be redirected to login
}

// Global state
let generatedContent = {
  titles: [],
  description: '',
  tags: [],
  thumbnail_text: ''
};

// Initialize generator page
document.addEventListener('DOMContentLoaded', () => {
  // Update character counts
  updateCharCount('videoTopic', 'topicCount', 100);
  updateCharCount('videoDesc', 'descCount', 500);
  
  // Check if video ID is in URL (coming from analyzer)
  const urlParams = new URLSearchParams(window.location.search);
  const videoIdFromUrl = urlParams.get('video');
  
  if (videoIdFromUrl) {
    loadVideoContext(videoIdFromUrl);
  }
  
  // Load user for sidebar
  loadUser();
  
  // Show empty state initially
  showEmptyState();
});

/**
 * Load video context if coming from analyzer
 */
async function loadVideoContext(videoId) {
  try {
    // Get connected channels
    const channels = await api.getYouTubeChannels();
    if (!channels || channels.length === 0) return;
    
    // Get videos
    const videos = await api.getChannelVideos(channels[0].id, 100);
    const video = videos.find(v => v.id === videoId);
    
    if (video) {
      // Pre-fill form with video data
      document.getElementById('videoTopic').value = video.title || '';
      document.getElementById('videoDesc').value = video.description ? video.description.substring(0, 500) : '';
      
      // Extract keywords from tags
      if (video.tags && video.tags.length > 0) {
        document.getElementById('keyword').value = video.tags[0];
      }
      
      // Update character counts
      updateCharCount('videoTopic', 'topicCount', 100);
      updateCharCount('videoDesc', 'descCount', 500);
      
      showToast('Video context loaded!', 'info');
    }
  } catch (error) {
    console.error('Failed to load video context:', error);
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

/**
 * Character counter
 */
function updateCharCount(inputId, countId, max) {
  const input = document.getElementById(inputId);
  const counter = document.getElementById(countId);
  if (!input || !counter) return;
  const len = input.value.length;
  counter.textContent = len;
  counter.style.color = len > max * 0.9 ? 'var(--warning)' : 'var(--text-muted)';
}

/**
 * Switch output tab
 */
function switchOutputTab(tabName, btn) {
  document.querySelectorAll('.output-panel').forEach(p => p.classList.remove('active'));
  document.querySelectorAll('.output-tab').forEach(t => t.classList.remove('active'));
  const panel = document.getElementById(`panel-${tabName}`);
  if (panel) panel.classList.add('active');
  if (btn) btn.classList.add('active');
}

/**
 * Generate content via AI API
 */
async function generateContent() {
  // Get form values
  const topic = document.getElementById('videoTopic').value.trim();
  const description = document.getElementById('videoDesc').value.trim();
  const audience = document.getElementById('audience').value.trim();
  const keyword = document.getElementById('keyword').value.trim();
  const tone = document.getElementById('tone').value;
  
  // Get checkboxes
  const genTitles = document.getElementById('genTitles').checked;
  const genDesc = document.getElementById('genDesc').checked;
  const genTags = document.getElementById('genTags').checked;
  const genThumb = document.getElementById('genThumb').checked;
  
  // Validation
  if (!topic) {
    showToast('Please enter a video topic', 'error');
    return;
  }
  
  if (!description) {
    showToast('Please enter a video description', 'error');
    return;
  }
  
  if (!genTitles && !genDesc && !genTags && !genThumb) {
    showToast('Please select at least one content type to generate', 'error');
    return;
  }
  
  // Show loading state
  const btn = document.getElementById('generateBtn');
  const indicator = document.getElementById('generatingIndicator');
  btn.disabled = true;
  btn.style.opacity = '0.7';
  indicator.classList.add('show');
  
  try {
    // Prepare request data
    const requestData = {
      topic: topic,
      description: description,
      target_audience: audience || 'General audience',
      keywords: keyword ? [keyword] : [],
      tone: tone,
      video_length: 'medium' // Default
    };
    
    // Generate each type
    const promises = [];
    
    if (genTitles) {
      promises.push(
        api.generateTitles(requestData)
          .then(result => {
            generatedContent.titles = result.titles || [];
          })
          .catch(error => {
            console.error('Failed to generate titles:', error);
            showToast('Failed to generate titles', 'error');
          })
      );
    }
    
    if (genDesc) {
      promises.push(
        api.generateDescription(requestData)
          .then(result => {
            generatedContent.description = result.description || '';
          })
          .catch(error => {
            console.error('Failed to generate description:', error);
            showToast('Failed to generate description', 'error');
          })
      );
    }
    
    if (genTags) {
      promises.push(
        api.generateTags(requestData)
          .then(result => {
            generatedContent.tags = result.tags || [];
          })
          .catch(error => {
            console.error('Failed to generate tags:', error);
            showToast('Failed to generate tags', 'error');
          })
      );
    }
    
    if (genThumb) {
      promises.push(
        api.generateThumbnailText(requestData)
          .then(result => {
            generatedContent.thumbnail_text = result.thumbnail_text || '';
          })
          .catch(error => {
            console.error('Failed to generate thumbnail text:', error);
            showToast('Failed to generate thumbnail text', 'error');
          })
      );
    }
    
    // Wait for all generations to complete
    await Promise.all(promises);
    
    // Render output
    renderOutput();
    
    showToast('✨ Content generated successfully!', 'success');
  } catch (error) {
    console.error('Failed to generate content:', error);
    showToast('Failed to generate content. Please try again.', 'error');
  } finally {
    // Hide loading state
    btn.disabled = false;
    btn.style.opacity = '1';
    indicator.classList.remove('show');
  }
}

/**
 * Render all output
 */
function renderOutput() {
  renderTitles();
  renderDescription();
  renderTags();
  renderThumbnail();
}

/**
 * Render titles
 */
function renderTitles() {
  const container = document.getElementById('titlesOutput');
  if (!container) return;
  
  if (!generatedContent.titles || generatedContent.titles.length === 0) {
    container.innerHTML = `
      <div style="text-align:center;padding:var(--space-xl);color:var(--text-muted);">
        <div style="font-size:2rem;margin-bottom:var(--space-sm);">📝</div>
        <p>No titles generated yet</p>
        <p style="font-size:0.85rem;margin-top:var(--space-sm);">Check "Optimized Titles" and click Generate</p>
      </div>
    `;
    return;
  }
  
  container.innerHTML = generatedContent.titles.map((title, i) => {
    const hasKeyword = document.getElementById('keyword').value && 
                       title.toLowerCase().includes(document.getElementById('keyword').value.toLowerCase());
    const hasYear = /20\d{2}/.test(title);
    const hasHook = /[!?]/.test(title);
    
    return `
      <div class="output-item" style="cursor:pointer;" onclick="selectTitle(this, ${i})">
        <div class="output-item-header">
          <span class="output-item-label">Option ${i + 1} ${i === 0 ? '⭐ Recommended' : ''}</span>
          <button class="copy-btn" onclick="event.stopPropagation(); copyToClipboard(\`${escapeForTemplate(title)}\`, this)">
            📋 Copy
          </button>
        </div>
        <div class="output-text">${escapeHtml(title)}</div>
        <div style="margin-top:var(--space-sm);display:flex;gap:var(--space-sm);flex-wrap:wrap;">
          <span style="font-size:0.72rem;color:var(--text-muted);">📏 ${title.length} chars</span>
          ${hasKeyword ? '<span style="font-size:0.72rem;color:var(--success);">✓ Has keyword</span>' : ''}
          ${hasYear ? '<span style="font-size:0.72rem;color:var(--success);">✓ Has year</span>' : ''}
          ${hasHook ? '<span style="font-size:0.72rem;color:var(--success);">✓ Emotional hook</span>' : ''}
        </div>
      </div>
    `;
  }).join('');
}

/**
 * Select a title
 */
function selectTitle(el, index) {
  document.querySelectorAll('#titlesOutput .output-item').forEach(item => {
    item.style.borderColor = 'var(--border)';
  });
  el.style.borderColor = 'var(--primary)';
  showToast('Title selected!', 'info', 1500);
}

/**
 * Render description
 */
function renderDescription() {
  const container = document.getElementById('descriptionOutput');
  if (!container) return;
  
  if (!generatedContent.description) {
    container.innerHTML = `
      <div style="text-align:center;padding:var(--space-xl);color:var(--text-muted);">
        <div style="font-size:2rem;margin-bottom:var(--space-sm);">📄</div>
        <p>No description generated yet</p>
        <p style="font-size:0.85rem;margin-top:var(--space-sm);">Check "Full Description" and click Generate</p>
      </div>
    `;
    return;
  }
  
  const desc = generatedContent.description;
  const wordCount = desc.split(/\s+/).length;
  const charCount = desc.length;
  
  container.innerHTML = `
    <div class="output-item">
      <div class="output-item-header">
        <span class="output-item-label">Full Description</span>
        <button class="copy-btn" onclick="copyToClipboard(\`${escapeForTemplate(desc)}\`, this)">
          📋 Copy
        </button>
      </div>
      <div class="output-text" style="white-space:pre-wrap;line-height:1.6;">${escapeHtml(desc)}</div>
      <div style="margin-top:var(--space-md);display:flex;gap:var(--space-md);flex-wrap:wrap;font-size:0.72rem;color:var(--text-muted);">
        <span>📏 ${charCount} characters</span>
        <span>📝 ${wordCount} words</span>
        <span style="color:var(--success);">✓ SEO optimized</span>
      </div>
    </div>
  `;
}

/**
 * Render tags
 */
function renderTags() {
  const container = document.getElementById('tagsOutput');
  if (!container) return;
  
  if (!generatedContent.tags || generatedContent.tags.length === 0) {
    container.innerHTML = `
      <div style="text-align:center;padding:var(--space-xl);color:var(--text-muted);">
        <div style="font-size:2rem;margin-bottom:var(--space-sm);">🏷️</div>
        <p>No tags generated yet</p>
        <p style="font-size:0.85rem;margin-top:var(--space-sm);">Check "SEO Tags" and click Generate</p>
      </div>
    `;
    return;
  }
  
  container.innerHTML = `
    <div class="output-item">
      <div class="output-item-header">
        <span class="output-item-label">${generatedContent.tags.length} Tags Generated</span>
        <button class="copy-btn" onclick="copyAllTags()">
          📋 Copy All
        </button>
      </div>
      <div class="tags-grid">
        ${generatedContent.tags.map(tag => `
          <span class="tag-chip clickable" onclick="copyToClipboard('${escapeForAttribute(tag)}', this)">
            #${escapeHtml(tag)}
          </span>
        `).join('')}
      </div>
      <div style="margin-top:var(--space-md);font-size:0.72rem;color:var(--text-muted);">
        💡 Tip: Click any tag to copy it individually, or use "Copy All" to copy all tags at once.
      </div>
    </div>
  `;
}

/**
 * Copy all tags
 */
function copyAllTags() {
  const tagsText = generatedContent.tags.join(', ');
  copyToClipboard(tagsText);
}

/**
 * Render thumbnail text
 */
function renderThumbnail() {
  const container = document.getElementById('thumbnailOutput');
  if (!container) return;
  
  if (!generatedContent.thumbnail_text) {
    container.innerHTML = `
      <div style="text-align:center;padding:var(--space-xl);color:var(--text-muted);">
        <div style="font-size:2rem;margin-bottom:var(--space-sm);">🖼️</div>
        <p>No thumbnail text generated yet</p>
        <p style="font-size:0.85rem;margin-top:var(--space-sm);">Check "Thumbnail Concept" and click Generate</p>
      </div>
    `;
    return;
  }
  
  const thumbText = generatedContent.thumbnail_text;
  
  container.innerHTML = `
    <div class="output-item">
      <div class="output-item-header">
        <span class="output-item-label">Thumbnail Text Suggestion</span>
        <button class="copy-btn" onclick="copyToClipboard(\`${escapeForTemplate(thumbText)}\`, this)">
          📋 Copy
        </button>
      </div>
      <div class="thumbnail-preview">
        <div class="thumbnail-text-large">${escapeHtml(thumbText)}</div>
      </div>
      <div style="margin-top:var(--space-md);font-size:0.72rem;color:var(--text-muted);">
        💡 Tip: Use bold, contrasting colors and large fonts for maximum impact. Keep text short and punchy.
      </div>
    </div>
  `;
}

/**
 * Show empty state
 */
function showEmptyState() {
  const panels = ['titlesOutput', 'descriptionOutput', 'tagsOutput', 'thumbnailOutput'];
  const messages = [
    { icon: '📝', title: 'No titles generated yet', tip: 'Check "Optimized Titles" and click Generate' },
    { icon: '📄', title: 'No description generated yet', tip: 'Check "Full Description" and click Generate' },
    { icon: '🏷️', title: 'No tags generated yet', tip: 'Check "SEO Tags" and click Generate' },
    { icon: '🖼️', title: 'No thumbnail text generated yet', tip: 'Check "Thumbnail Concept" and click Generate' }
  ];
  
  panels.forEach((panelId, index) => {
    const container = document.getElementById(panelId);
    if (container) {
      const msg = messages[index];
      container.innerHTML = `
        <div style="text-align:center;padding:var(--space-xl);color:var(--text-muted);">
          <div style="font-size:2rem;margin-bottom:var(--space-sm);">${msg.icon}</div>
          <p>${msg.title}</p>
          <p style="font-size:0.85rem;margin-top:var(--space-sm);">${msg.tip}</p>
        </div>
      `;
    }
  });
}

/**
 * Copy all content
 */
function copyAllContent() {
  let allContent = '';
  
  if (generatedContent.titles && generatedContent.titles.length > 0) {
    allContent += '=== TITLES ===\n';
    generatedContent.titles.forEach((title, i) => {
      allContent += `${i + 1}. ${title}\n`;
    });
    allContent += '\n';
  }
  
  if (generatedContent.description) {
    allContent += '=== DESCRIPTION ===\n';
    allContent += generatedContent.description + '\n\n';
  }
  
  if (generatedContent.tags && generatedContent.tags.length > 0) {
    allContent += '=== TAGS ===\n';
    allContent += generatedContent.tags.join(', ') + '\n\n';
  }
  
  if (generatedContent.thumbnail_text) {
    allContent += '=== THUMBNAIL TEXT ===\n';
    allContent += generatedContent.thumbnail_text + '\n';
  }
  
  if (allContent) {
    copyToClipboard(allContent);
    showToast('✅ All content copied to clipboard!', 'success');
  } else {
    showToast('No content to copy. Generate content first.', 'info');
  }
}

/**
 * Copy to clipboard
 */
function copyToClipboard(text, button) {
  navigator.clipboard.writeText(text).then(() => {
    if (button) {
      const originalText = button.textContent;
      button.textContent = '✓ Copied!';
      button.style.color = 'var(--success)';
      setTimeout(() => {
        button.textContent = originalText;
        button.style.color = '';
      }, 2000);
    } else {
      showToast('Copied to clipboard!', 'success', 1500);
    }
  }).catch(err => {
    console.error('Failed to copy:', err);
    showToast('Failed to copy to clipboard', 'error');
  });
}

// ==================== Helper Functions ====================

/**
 * Escape HTML to prevent XSS
 */
function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

/**
 * Escape for template literals
 */
function escapeForTemplate(text) {
  return text.replace(/`/g, '\\`').replace(/\$/g, '\\$').replace(/\\/g, '\\\\');
}

/**
 * Escape for HTML attributes
 */
function escapeForAttribute(text) {
  return text.replace(/'/g, "\\'").replace(/"/g, '&quot;');
}
