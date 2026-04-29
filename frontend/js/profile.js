/**
 * Profile Page Logic with API Integration
 * Handles profile viewing, editing, and avatar upload
 */

// Protect this page - require authentication
if (!requireAuth()) {
  // User will be redirected to login
}

// Global state
let isEditMode = false;
let originalProfileData = {};
let currentUser = null;

// Fields that can be edited
const EDITABLE_FIELDS = ['firstName', 'lastName', 'displayName', 'bio'];

// Initialize profile page
document.addEventListener('DOMContentLoaded', () => {
  loadProfileData();
});

/**
 * Load all profile data
 */
async function loadProfileData() {
  try {
    showLoadingState();
    
    // Load user profile
    currentUser = await api.getUserProfile();
    
    // Store original data for cancel functionality
    originalProfileData = { ...currentUser };
    
    // Render profile
    renderProfile(currentUser);
    
    // Load channel data if available
    await loadChannelData();
    
    hideLoadingState();
  } catch (error) {
    console.error('Failed to load profile:', error);
    showError('Failed to load profile data. Please try again.');
  }
}

/**
 * Render profile data in the UI
 */
function renderProfile(user) {
  // Parse full name
  const nameParts = (user.full_name || '').split(' ');
  const firstName = nameParts[0] || '';
  const lastName = nameParts.slice(1).join(' ') || '';
  
  // Update form fields
  document.getElementById('firstName').value = firstName;
  document.getElementById('lastName').value = lastName;
  document.getElementById('displayName').value = user.full_name || '';
  document.getElementById('email').value = user.email || '';
  document.getElementById('bio').value = user.bio || '';
  
  // Update avatar displays
  updateAvatarDisplays(user);
  
  // Update sidebar
  const sidebarName = document.getElementById('sidebarUserName');
  if (sidebarName) {
    sidebarName.textContent = user.full_name || user.email;
  }
  
  // Update account info
  updateAccountInfo(user);
}

/**
 * Update avatar displays throughout the page
 */
function updateAvatarDisplays(user) {
  const avatarEl = document.getElementById('profileAvatarDisplay');
  const nameEl = document.getElementById('avatarDisplayName');
  const emailEl = document.getElementById('avatarDisplayEmail');
  
  if (user.avatar_url) {
    // Show avatar image
    avatarEl.style.backgroundImage = `url(${user.avatar_url})`;
    avatarEl.style.backgroundSize = 'cover';
    avatarEl.style.backgroundPosition = 'center';
    avatarEl.textContent = '';
  } else {
    // Show initials
    const initials = user.full_name 
      ? user.full_name.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2)
      : user.email[0].toUpperCase();
    avatarEl.textContent = initials;
    avatarEl.style.backgroundImage = 'none';
  }
  
  if (nameEl) nameEl.textContent = user.full_name || user.email;
  if (emailEl) emailEl.textContent = user.email;
}

/**
 * Update account information section
 */
function updateAccountInfo(user) {
  // Member since
  if (user.created_at) {
    const memberSince = new Date(user.created_at);
    const memberSinceEl = document.querySelector('[data-field="member-since"]');
    if (memberSinceEl) {
      memberSinceEl.textContent = memberSince.toLocaleDateString('en-US', { 
        month: 'long', 
        year: 'numeric' 
      });
    }
  }
  
  // Last login (use current time as placeholder)
  const lastLoginEl = document.querySelector('[data-field="last-login"]');
  if (lastLoginEl) {
    const now = new Date();
    lastLoginEl.textContent = now.toLocaleTimeString('en-US', { 
      hour: 'numeric', 
      minute: '2-digit',
      hour12: true 
    });
  }
}

/**
 * Load YouTube channel data
 */
async function loadChannelData() {
  try {
    const channels = await api.getYouTubeChannels();
    
    if (channels && channels.length > 0) {
      const channel = channels[0];
      renderChannelData(channel);
      
      // Update quick stats
      updateQuickStats(channel);
    } else {
      showNoChannelState();
    }
  } catch (error) {
    console.error('Failed to load channel data:', error);
    showNoChannelState();
  }
}

/**
 * Render channel data
 */
function renderChannelData(channel) {
  // Update channel card (if elements exist)
  const channelName = document.querySelector('.channel-connect-name');
  const channelHandle = document.querySelector('.channel-connect-handle');
  const channelAvatar = document.querySelector('.channel-connect-avatar');
  
  if (channelName) channelName.textContent = channel.title;
  if (channelHandle) {
    channelHandle.textContent = `@${channel.custom_url || channel.title} · youtube.com/@${channel.custom_url || channel.title}`;
  }
  if (channelAvatar && channel.thumbnail_url) {
    channelAvatar.style.backgroundImage = `url(${channel.thumbnail_url})`;
    channelAvatar.style.backgroundSize = 'cover';
    channelAvatar.textContent = '';
  }
  
  // Update channel meta
  const metaContainer = document.querySelector('.channel-connect-meta');
  if (metaContainer) {
    metaContainer.innerHTML = `
      <span>👥 <strong>${formatNumber(channel.subscriber_count || 0)}</strong> subscribers</span>
      <span>🎬 <strong>${formatNumber(channel.video_count || 0)}</strong> videos</span>
      <span>👁️ <strong>${formatNumber(channel.view_count || 0)}</strong> total views</span>
      <span>📅 Connected <strong>${formatDate(channel.connected_at)}</strong></span>
    `;
  }
}

/**
 * Update quick stats in avatar card
 */
function updateQuickStats(channel) {
  const stats = document.querySelectorAll('.avatar-stat');
  if (stats.length >= 4) {
    // Videos
    stats[0].querySelector('.as-value').textContent = formatNumber(channel.video_count || 0);
    // Subscribers
    stats[1].querySelector('.as-value').textContent = formatNumber(channel.subscriber_count || 0);
    // Avg SEO (placeholder - would come from SEO stats)
    stats[2].querySelector('.as-value').textContent = '--';
    // Views
    stats[3].querySelector('.as-value').textContent = formatNumber(channel.view_count || 0);
  }
}

/**
 * Show no channel state
 */
function showNoChannelState() {
  const channelCard = document.querySelector('.channel-connect-card');
  if (channelCard) {
    channelCard.innerHTML = `
      <div style="text-align: center; padding: 40px; color: var(--text-muted);">
        <div style="font-size: 3rem; margin-bottom: 10px;">📺</div>
        <p>No YouTube channel connected</p>
        <p style="font-size: 0.9rem; margin-top: 10px;">
          <a href="channel.html" class="btn btn-primary btn-sm">Connect Channel</a>
        </p>
      </div>
    `;
  }
}

/**
 * Enable edit mode
 */
function enableEditMode() {
  isEditMode = true;
  
  EDITABLE_FIELDS.forEach(id => {
    const el = document.getElementById(id);
    if (el) {
      el.disabled = false;
      el.classList.add('editable');
    }
  });
  
  // Show/hide buttons
  document.getElementById('editProfileBtn').style.display = 'none';
  document.getElementById('saveProfileBtn').style.display = 'inline-flex';
  document.getElementById('cancelEditBtn').style.display = 'inline-flex';
  document.getElementById('saveBtnInCard').style.display = 'inline-flex';
  document.getElementById('cancelBtnInCard').style.display = 'inline-flex';
  
  // Show editing indicator
  document.getElementById('editModeIndicator').classList.add('show');
  
  // Focus first field
  document.getElementById('firstName').focus();
  
  showToast('Edit mode enabled. Make your changes.', 'info');
}

/**
 * Cancel edit mode
 */
function cancelEditMode() {
  isEditMode = false;
  
  // Restore original values
  renderProfile(originalProfileData);
  
  disableFields();
  showToast('Changes discarded.', 'info');
}

/**
 * Save profile changes
 */
async function saveProfile() {
  try {
    // Get form values
    const firstName = document.getElementById('firstName').value.trim();
    const lastName = document.getElementById('lastName').value.trim();
    const displayName = document.getElementById('displayName').value.trim();
    const bio = document.getElementById('bio').value.trim();
    
    // Validation
    if (!firstName || !displayName) {
      showToast('Please fill in all required fields.', 'error');
      return;
    }
    
    // Show loading
    const saveBtn = document.getElementById('saveProfileBtn');
    const originalText = saveBtn.textContent;
    saveBtn.disabled = true;
    saveBtn.innerHTML = '<span class="spinner"></span> Saving...';
    
    // Combine first and last name
    const fullName = `${firstName} ${lastName}`.trim();
    
    // Update profile via API
    const updatedUser = await api.updateUserProfile({
      full_name: fullName,
      bio: bio
    });
    
    // Update current user and original data
    currentUser = updatedUser;
    originalProfileData = { ...updatedUser };
    
    // Update UI
    renderProfile(updatedUser);
    updateAvatarDisplays(updatedUser);
    
    // Update sidebar
    const sidebarName = document.getElementById('sidebarUserName');
    if (sidebarName) {
      sidebarName.textContent = updatedUser.full_name || updatedUser.email;
    }
    
    // Save to localStorage
    saveUserData(updatedUser);
    
    disableFields();
    
    // Restore button
    saveBtn.disabled = false;
    saveBtn.textContent = originalText;
    
    showToast('✅ Profile updated successfully!', 'success');
  } catch (error) {
    console.error('Failed to save profile:', error);
    showToast('Failed to save profile. Please try again.', 'error');
    
    // Restore button
    const saveBtn = document.getElementById('saveProfileBtn');
    saveBtn.disabled = false;
    saveBtn.textContent = '💾 Save Changes';
  }
}

/**
 * Disable all editable fields
 */
function disableFields() {
  isEditMode = false;
  
  EDITABLE_FIELDS.forEach(id => {
    const el = document.getElementById(id);
    if (el) {
      el.disabled = true;
      el.classList.remove('editable');
    }
  });
  
  document.getElementById('editProfileBtn').style.display = 'inline-flex';
  document.getElementById('saveProfileBtn').style.display = 'none';
  document.getElementById('cancelEditBtn').style.display = 'none';
  document.getElementById('saveBtnInCard').style.display = 'none';
  document.getElementById('cancelBtnInCard').style.display = 'none';
  document.getElementById('editModeIndicator').classList.remove('show');
}

/**
 * Handle avatar upload
 */
async function handleAvatarUpload() {
  // Create file input
  const input = document.createElement('input');
  input.type = 'file';
  input.accept = 'image/*';
  
  input.onchange = async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    
    // Validate file size (max 5MB)
    if (file.size > 5 * 1024 * 1024) {
      showToast('Image must be less than 5MB', 'error');
      return;
    }
    
    // Validate file type
    if (!file.type.startsWith('image/')) {
      showToast('Please select an image file', 'error');
      return;
    }
    
    try {
      showToast('Uploading avatar...', 'info');
      
      // Upload via API
      const result = await api.uploadAvatar(file);
      
      // Update current user
      currentUser.avatar_url = result.avatar_url;
      originalProfileData.avatar_url = result.avatar_url;
      
      // Update UI
      updateAvatarDisplays(currentUser);
      
      // Save to localStorage
      saveUserData(currentUser);
      
      showToast('✅ Avatar updated successfully!', 'success');
    } catch (error) {
      console.error('Failed to upload avatar:', error);
      showToast('Failed to upload avatar. Please try again.', 'error');
    }
  };
  
  input.click();
}

/**
 * Refresh channel data
 */
async function refreshChannelData() {
  try {
    showToast('Refreshing channel data...', 'info');
    await loadChannelData();
    showToast('✅ Channel data refreshed!', 'success');
  } catch (error) {
    console.error('Failed to refresh channel:', error);
    showToast('Failed to refresh channel data', 'error');
  }
}

/**
 * Disconnect YouTube channel
 */
async function disconnectChannel() {
  if (!confirm('Are you sure you want to disconnect your YouTube channel? This will remove all synced videos.')) {
    return;
  }
  
  try {
    const channels = await api.getYouTubeChannels();
    if (channels && channels.length > 0) {
      const channelId = channels[0].id;
      
      showToast('Disconnecting channel...', 'info');
      await api.disconnectYouTubeChannel(channelId);
      
      showNoChannelState();
      showToast('✅ Channel disconnected successfully', 'success');
    }
  } catch (error) {
    console.error('Failed to disconnect channel:', error);
    showToast('Failed to disconnect channel', 'error');
  }
}

/**
 * Confirm logout
 */
function confirmLogout() {
  if (confirm('Are you sure you want to log out?')) {
    logout();
  }
}

// ==================== Helper Functions ====================

function formatNumber(num) {
  if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M';
  if (num >= 1000) return (num / 1000).toFixed(1) + 'K';
  return num.toString();
}

function formatDate(dateString) {
  if (!dateString) return 'Recently';
  const date = new Date(dateString);
  return date.toLocaleDateString('en-US', { month: 'short', year: 'numeric' });
}

function showLoadingState() {
  // Could add a loading overlay if needed
}

function hideLoadingState() {
  // Hide loading overlay
}

function showError(message) {
  showToast(message, 'error');
}

// ==================== Sidebar Helpers ====================

function toggleSidebar() {
  document.getElementById('sidebar').classList.toggle('open');
  document.getElementById('sidebarOverlay').style.display = 'block';
}

function closeSidebar() {
  document.getElementById('sidebar').classList.remove('open');
  document.getElementById('sidebarOverlay').style.display = 'none';
}
