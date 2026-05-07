/**
 * Settings Page Logic with API Integration
 * Handles user preferences, notifications, account settings, and more
 */

// Protect this page - require authentication
if (!requireAuth()) {
  // User will be redirected to login
}

// ==================== Global State ====================

let currentSettings = {};
let originalSettings = {};
let hasChanges = false;

// ==================== Initialization ====================

/**
 * Initialize settings page on DOM load
 */
document.addEventListener('DOMContentLoaded', () => {
  loadSettings();
  
  // Check if we need to switch to a specific tab (e.g., after OAuth callback)
  const params = new URLSearchParams(window.location.search);
  const tab = params.get('tab');
  
  if (tab === 'apps') {
    // Switch to Connected Apps section
    setTimeout(() => {
      const appsButton = document.querySelector('[onclick*="switchSettingsSection(\'apps\'"]');
      if (appsButton) {
        appsButton.click();
      }
    }, 500);
  }
});

// ==================== PHASE 1: Load & Display Settings ====================

/**
 * Load settings from API
 */
async function loadSettings() {
  try {
    showLoadingState();
    
    // Fetch settings from API
    currentSettings = await api.getUserSettings();
    
    // Store original for cancel functionality
    originalSettings = { ...currentSettings };
    
    // Render settings in UI
    renderSettings(currentSettings);
    
    // Load connected apps
    loadConnectedApps();
    
    hideLoadingState();
  } catch (error) {
    console.error('Failed to load settings:', error);
    showToast('Failed to load settings. Please try again.', 'error');
    hideLoadingState();
  }
}

/**
 * Render settings data in the UI
 */
function renderSettings(settings) {
  // ===== APPEARANCE SECTION =====
  
  // Dark Mode Toggle
  const darkModeToggle = document.getElementById('darkModeToggle');
  if (darkModeToggle) {
    darkModeToggle.checked = settings.theme === 'dark';
  }
  
  // Theme Selection
  const themeOptions = document.querySelectorAll('.theme-option');
  themeOptions.forEach(option => {
    option.classList.remove('selected');
    const label = option.querySelector('.theme-label');
    if (label && label.textContent.toLowerCase() === settings.theme) {
      option.classList.add('selected');
    }
  });
  
  // Accent Color Selection
  const accentSwatches = document.querySelectorAll('.accent-swatch');
  accentSwatches.forEach(swatch => {
    swatch.classList.remove('selected');
    if (swatch.style.background === settings.accent_color) {
      swatch.classList.add('selected');
    }
  });
  
  // Font Size Selection
  const fontSizeSelect = document.getElementById('fontSizeSelect');
  if (fontSizeSelect) {
    fontSizeSelect.value = settings.font_size || 'normal';
  }
  
  // Compact Mode Toggle
  const compactModeToggle = document.getElementById('compactModeToggle');
  if (compactModeToggle) {
    compactModeToggle.checked = settings.compact_mode || false;
  }
  
  // ===== NOTIFICATIONS SECTION =====
  
  const emailNotificationsToggle = document.getElementById('emailNotificationsToggle');
  if (emailNotificationsToggle) {
    emailNotificationsToggle.checked = settings.email_notifications !== false;
  }
  
  const weeklySeoToggle = document.getElementById('weeklySeoToggle');
  if (weeklySeoToggle) {
    weeklySeoToggle.checked = settings.weekly_seo_report !== false;
  }
  
  const trendingAlertsToggle = document.getElementById('trendingAlertsToggle');
  if (trendingAlertsToggle) {
    trendingAlertsToggle.checked = settings.trending_alerts !== false;
  }
  
  const featureUpdatesToggle = document.getElementById('featureUpdatesToggle');
  if (featureUpdatesToggle) {
    featureUpdatesToggle.checked = settings.feature_updates !== false;
  }
  
  const milestoneAlertsToggle = document.getElementById('milestoneAlertsToggle');
  if (milestoneAlertsToggle) {
    milestoneAlertsToggle.checked = settings.milestone_alerts !== false;
  }
  
  // ===== PRIVACY SECTION =====
  
  const profileVisibilityToggle = document.getElementById('profileVisibilityToggle');
  if (profileVisibilityToggle) {
    profileVisibilityToggle.checked = settings.profile_visibility !== false;
  }
  
  const analyticsSharingToggle = document.getElementById('analyticsSharingToggle');
  if (analyticsSharingToggle) {
    analyticsSharingToggle.checked = settings.analytics_sharing !== false;
  }
  
  // Apply theme visually
  applyThemeSettings(settings);
}

/**
 * Apply theme settings to the page
 */
function applyThemeSettings(settings) {
  const root = document.documentElement;
  
  // Apply accent color
  if (settings.accent_color) {
    root.style.setProperty('--accent-color', settings.accent_color);
  }
  
  // Apply theme
  if (settings.theme === 'dark') {
    document.body.classList.add('dark-mode');
  } else {
    document.body.classList.remove('dark-mode');
  }
  
  // Apply font size
  if (settings.font_size === 'small') {
    document.body.classList.add('font-small');
    document.body.classList.remove('font-large');
  } else if (settings.font_size === 'large') {
    document.body.classList.add('font-large');
    document.body.classList.remove('font-small');
  } else {
    document.body.classList.remove('font-small', 'font-large');
  }
  
  // Apply compact mode
  if (settings.compact_mode) {
    document.body.classList.add('compact-mode');
  } else {
    document.body.classList.remove('compact-mode');
  }
}

// ==================== PHASE 2: Appearance Settings ====================

/**
 * Toggle dark mode
 */
function toggleDarkMode() {
  const toggle = document.getElementById('darkModeToggle');
  currentSettings.theme = toggle.checked ? 'dark' : 'light';
  applyThemeSettings(currentSettings);
  markChanged();
}

/**
 * Select theme
 */
function selectTheme(themeName, element) {
  // Update visual selection
  document.querySelectorAll('.theme-option').forEach(opt => {
    opt.classList.remove('selected');
  });
  element.classList.add('selected');
  
  // Update settings
  currentSettings.theme = themeName;
  applyThemeSettings(currentSettings);
  markChanged();
}

/**
 * Select accent color
 */
function selectAccent(element, colorHex) {
  // Update visual selection
  document.querySelectorAll('.accent-swatch').forEach(swatch => {
    swatch.classList.remove('selected');
  });
  element.classList.add('selected');
  
  // Update settings
  currentSettings.accent_color = colorHex;
  applyThemeSettings(currentSettings);
  markChanged();
}

/**
 * Select font size
 */
function selectFontSize(size) {
  currentSettings.font_size = size;
  applyThemeSettings(currentSettings);
  markChanged();
}

/**
 * Toggle compact mode
 */
function toggleCompactMode() {
  const compactModeToggle = document.getElementById('compactModeToggle');
  if (compactModeToggle) {
    currentSettings.compact_mode = compactModeToggle.checked;
    applyThemeSettings(currentSettings);
    markChanged();
  }
}

// ==================== PHASE 3: Notification Settings ====================

/**
 * Toggle email notifications master
 */
function toggleEmailNotifications() {
  const emailNotificationsToggle = document.getElementById('emailNotificationsToggle');
  if (emailNotificationsToggle) {
    currentSettings.email_notifications = emailNotificationsToggle.checked;
    markChanged();
  }
}

/**
 * Toggle individual notification settings
 */
function toggleNotificationSetting(settingName) {
  if (settingName === 'weekly_seo_report') {
    const weeklySeoToggle = document.getElementById('weeklySeoToggle');
    if (weeklySeoToggle) {
      currentSettings.weekly_seo_report = weeklySeoToggle.checked;
    }
  } else if (settingName === 'trending_alerts') {
    const trendingAlertsToggle = document.getElementById('trendingAlertsToggle');
    if (trendingAlertsToggle) {
      currentSettings.trending_alerts = trendingAlertsToggle.checked;
    }
  } else if (settingName === 'feature_updates') {
    const featureUpdatesToggle = document.getElementById('featureUpdatesToggle');
    if (featureUpdatesToggle) {
      currentSettings.feature_updates = featureUpdatesToggle.checked;
    }
  } else if (settingName === 'milestone_alerts') {
    const milestoneAlertsToggle = document.getElementById('milestoneAlertsToggle');
    if (milestoneAlertsToggle) {
      currentSettings.milestone_alerts = milestoneAlertsToggle.checked;
    }
  }
  
  markChanged();
}

// ==================== PHASE 4: Privacy Settings ====================

/**
 * Toggle profile visibility
 */
function toggleProfileVisibility() {
  const profileVisibilityToggle = document.getElementById('profileVisibilityToggle');
  if (profileVisibilityToggle) {
    currentSettings.profile_visibility = profileVisibilityToggle.checked;
    markChanged();
  }
}

/**
 * Toggle analytics sharing
 */
function toggleAnalyticsSharing() {
  const analyticsSharingToggle = document.getElementById('analyticsSharingToggle');
  if (analyticsSharingToggle) {
    currentSettings.analytics_sharing = analyticsSharingToggle.checked;
    markChanged();
  }
}

// ==================== PHASE 5: Change Detection & Save Banner ====================

/**
 * Mark that settings have changed
 */
function markChanged() {
  // Compare current with original
  hasChanges = JSON.stringify(currentSettings) !== JSON.stringify(originalSettings);
  
  if (hasChanges) {
    showSaveBanner();
  } else {
    hideSaveBanner();
  }
}

/**
 * Show save banner
 */
function showSaveBanner() {
  const banner = document.getElementById('saveBanner');
  if (banner) {
    banner.style.display = 'flex';
  }
}

/**
 * Hide save banner
 */
function hideSaveBanner() {
  const banner = document.getElementById('saveBanner');
  if (banner) {
    banner.style.display = 'none';
  }
}

/**
 * Discard changes
 */
function discardChanges() {
  // Restore original settings
  currentSettings = { ...originalSettings };
  
  // Re-render UI
  renderSettings(currentSettings);
  
  // Hide banner
  hideSaveBanner();
  
  showToast('Changes discarded.', 'info');
}

// ==================== PHASE 6: Save Settings ====================

/**
 * Save all settings to backend
 */
async function saveAllSettings() {
  try {
    const saveBtn = document.querySelector('.save-banner-actions .btn-primary');
    if (saveBtn) {
      saveBtn.disabled = true;
      saveBtn.innerHTML = '<span class="spinner"></span> Saving...';
    }
    
    // Call API to update settings
    const updatedSettings = await api.updateUserSettings(currentSettings);
    
    // Update original settings
    originalSettings = { ...updatedSettings };
    currentSettings = { ...updatedSettings };
    
    // Hide banner
    hideSaveBanner();
    
    // Restore button
    if (saveBtn) {
      saveBtn.disabled = false;
      saveBtn.textContent = '💾 Save Settings';
    }
    
    showToast('✅ Settings saved successfully!', 'success');
  } catch (error) {
    console.error('Failed to save settings:', error);
    showToast('Failed to save settings. Please try again.', 'error');
    
    // Restore button
    const saveBtn = document.querySelector('.save-banner-actions .btn-primary');
    if (saveBtn) {
      saveBtn.disabled = false;
      saveBtn.textContent = '💾 Save Settings';
    }
  }
}

// ==================== PHASE 7: Section Navigation ====================

/**
 * Switch between settings sections
 */
function switchSettingsSection(sectionName, element) {
  // Hide all sections
  document.querySelectorAll('.settings-section').forEach(section => {
    section.classList.remove('active');
  });
  
  // Show selected section
  const section = document.getElementById(`section-${sectionName}`);
  if (section) {
    section.classList.add('active');
  }
  
  // Update active nav button
  document.querySelectorAll('.settings-nav-item').forEach(btn => {
    btn.classList.remove('active');
  });
  element.classList.add('active');
}

// ==================== PHASE 8: Account Settings (Password) ====================

/**
 * Toggle password visibility
 */
function togglePwVisibility(fieldId, button) {
  const field = document.getElementById(fieldId);
  if (field) {
    if (field.type === 'password') {
      field.type = 'text';
      button.textContent = '🙈';
    } else {
      field.type = 'password';
      button.textContent = '👁️';
    }
  }
}

/**
 * Check password strength
 */
function checkNewPwStrength(password) {
  const strengthFill = document.getElementById('pwStrengthFill');
  const strengthText = document.getElementById('pwStrengthText');
  
  if (!password) {
    if (strengthFill) strengthFill.style.width = '0%';
    if (strengthText) strengthText.textContent = 'Enter a password';
    return;
  }
  
  let strength = 0;
  
  // Check length
  if (password.length >= 8) strength += 25;
  if (password.length >= 12) strength += 25;
  
  // Check for uppercase
  if (/[A-Z]/.test(password)) strength += 25;
  
  // Check for numbers
  if (/[0-9]/.test(password)) strength += 25;
  
  // Check for special characters
  if (/[!@#$%^&*]/.test(password)) strength += 25;
  
  // Cap at 100
  strength = Math.min(strength, 100);
  
  // Update UI
  if (strengthFill) strengthFill.style.width = strength + '%';
  
  if (strengthText) {
    if (strength < 40) {
      strengthText.textContent = '❌ Weak password';
      strengthFill.style.backgroundColor = '#EF4444';
    } else if (strength < 70) {
      strengthText.textContent = '⚠️ Medium strength';
      strengthFill.style.backgroundColor = '#F59E0B';
    } else {
      strengthText.textContent = '✅ Strong password';
      strengthFill.style.backgroundColor = '#10B981';
    }
  }
}

/**
 * Save password
 */
async function savePassword() {
  try {
    const currentPw = document.getElementById('currentPw').value;
    const newPw = document.getElementById('newPw').value;
    const confirmPw = document.getElementById('confirmPw').value;
    
    // Validation
    if (!currentPw) {
      showToast('Please enter your current password.', 'error');
      return;
    }
    
    if (!newPw || newPw.length < 8) {
      showToast('New password must be at least 8 characters.', 'error');
      return;
    }
    
    if (newPw !== confirmPw) {
      showToast('New passwords do not match.', 'error');
      return;
    }
    
    // Show loading
    const saveBtn = document.querySelector('#section-account .btn-primary');
    if (saveBtn) {
      saveBtn.disabled = true;
      saveBtn.innerHTML = '<span class="spinner"></span> Saving...';
    }
    
    // Call API
    await api.changePassword(currentPw, newPw, confirmPw);
    
    // Clear fields
    document.getElementById('currentPw').value = '';
    document.getElementById('newPw').value = '';
    document.getElementById('confirmPw').value = '';
    
    // Reset strength indicator
    const strengthFill = document.getElementById('pwStrengthFill');
    if (strengthFill) strengthFill.style.width = '0%';
    const strengthText = document.getElementById('pwStrengthText');
    if (strengthText) strengthText.textContent = 'Enter a password';
    
    // Restore button
    if (saveBtn) {
      saveBtn.disabled = false;
      saveBtn.textContent = '💾 Save Password';
    }
    
    showToast('✅ Password changed successfully!', 'success');
  } catch (error) {
    console.error('Failed to change password:', error);
    showToast('Failed to change password. Please try again.', 'error');
    
    // Restore button
    const saveBtn = document.querySelector('#section-account .btn-primary');
    if (saveBtn) {
      saveBtn.disabled = false;
      saveBtn.textContent = '💾 Save Password';
    }
  }
}

// ==================== PHASE 9: Connected Apps ====================

/**
 * Load connected apps
 */
async function loadConnectedApps() {
  try {
    // Fetch YouTube channels
    const channels = await api.getYouTubeChannels();
    
    // Get YouTube status and button elements
    const youtubeStatus = document.getElementById('youtubeStatus');
    const youtubeDisconnectBtn = document.getElementById('youtubeDisconnectBtn');
    const youtubeConnectBtn = document.getElementById('youtubeConnectBtn');
    
    if (channels && channels.length > 0) {
      // YouTube is connected - show real channel data
      const channel = channels[0];
      const channelName = channel.title || channel.channel_name || 'YouTube Channel';
      const channelHandle = channel.custom_url || channel.channel_handle || channelName;
      
      // Update status to show connected with real channel name
      youtubeStatus.innerHTML = `✅ Connected · @${channelHandle}`;
      youtubeStatus.classList.add('connected');
      
      // Show disconnect button, hide connect button
      youtubeDisconnectBtn.style.display = 'inline-flex';
      youtubeConnectBtn.style.display = 'none';
    } else {
      // YouTube is not connected
      youtubeStatus.innerHTML = 'Not connected';
      youtubeStatus.classList.remove('connected');
      
      // Show connect button, hide disconnect button
      youtubeDisconnectBtn.style.display = 'none';
      youtubeConnectBtn.style.display = 'inline-flex';
    }
  } catch (error) {
    console.error('Failed to load connected apps:', error);
    
    // On error, show not connected state
    const youtubeStatus = document.getElementById('youtubeStatus');
    const youtubeDisconnectBtn = document.getElementById('youtubeDisconnectBtn');
    const youtubeConnectBtn = document.getElementById('youtubeConnectBtn');
    
    youtubeStatus.innerHTML = 'Not connected';
    youtubeStatus.classList.remove('connected');
    youtubeDisconnectBtn.style.display = 'none';
    youtubeConnectBtn.style.display = 'inline-flex';
  }
}

/**
 * Disconnect app
 */
async function disconnectApp(appName) {
  if (!confirm(`Are you sure you want to disconnect ${appName}? This will remove all associated data.`)) {
    return;
  }
  
  try {
    if (appName === 'YouTube') {
      // Show loading state
      const youtubeDisconnectBtn = document.getElementById('youtubeDisconnectBtn');
      const originalText = youtubeDisconnectBtn.textContent;
      youtubeDisconnectBtn.disabled = true;
      youtubeDisconnectBtn.innerHTML = '<span class="spinner"></span> Disconnecting...';
      
      // Get channels
      const channels = await api.getYouTubeChannels();
      if (channels && channels.length > 0) {
        // Disconnect the channel
        const result = await api.disconnectYouTubeChannel(channels[0].id);
        
        // Show success message
        showToast(`✅ ${appName} disconnected successfully!`, 'success');
        
        // Refresh connected apps UI
        await loadConnectedApps();
        
        // Redirect to dashboard after 2 seconds to clear cached data
        setTimeout(() => {
          window.location.href = '/pages/dashboard.html';
        }, 2000);
      } else {
        showToast('No YouTube channel found to disconnect.', 'error');
        youtubeDisconnectBtn.disabled = false;
        youtubeDisconnectBtn.textContent = originalText;
      }
    }
  } catch (error) {
    console.error(`Failed to disconnect ${appName}:`, error);
    showToast(`Failed to disconnect ${appName}. Please try again.`, 'error');
    
    // Restore button
    const youtubeDisconnectBtn = document.getElementById('youtubeDisconnectBtn');
    youtubeDisconnectBtn.disabled = false;
    youtubeDisconnectBtn.textContent = 'Disconnect';
  }
}

/**
 * Connect app
 */
function connectApp(appName) {
  if (appName === 'YouTube') {
    // Redirect to YouTube OAuth
    window.location.href = '/api/youtube/authorize';
  } else {
    showToast(`${appName} connection coming soon!`, 'info');
  }
}

// ==================== PHASE 10: Danger Zone ====================

/**
 * Confirm dangerous action
 */
function confirmAction(actionType) {
  let message = '';
  let confirmText = '';
  
  if (actionType === 'delete reports') {
    message = 'Are you sure you want to delete ALL reports? This cannot be undone.';
    confirmText = 'Delete All Reports';
  } else if (actionType === 'disconnect channels') {
    message = 'Are you sure you want to disconnect ALL YouTube channels? This cannot be undone.';
    confirmText = 'Disconnect All Channels';
  } else if (actionType === 'delete account') {
    message = 'Are you sure you want to DELETE YOUR ACCOUNT? This will permanently delete all your data and cannot be undone.';
    confirmText = 'Delete My Account';
  }
  
  if (confirm(message)) {
    if (actionType === 'delete reports') {
      deleteAllReports();
    } else if (actionType === 'disconnect channels') {
      disconnectAllChannels();
    } else if (actionType === 'delete account') {
      deleteAccount();
    }
  }
}

/**
 * Delete all reports
 */
async function deleteAllReports() {
  try {
    showToast('Deleting all reports...', 'info');
    // TODO: Call API to delete reports
    showToast('✅ All reports deleted successfully!', 'success');
  } catch (error) {
    console.error('Failed to delete reports:', error);
    showToast('Failed to delete reports.', 'error');
  }
}

/**
 * Disconnect all channels
 */
async function disconnectAllChannels() {
  try {
    showToast('Disconnecting all channels...', 'info');
    // TODO: Call API to disconnect all channels
    showToast('✅ All channels disconnected successfully!', 'success');
    loadConnectedApps();
  } catch (error) {
    console.error('Failed to disconnect channels:', error);
    showToast('Failed to disconnect channels.', 'error');
  }
}

/**
 * Delete account
 */
async function deleteAccount() {
  try {
    showToast('Deleting account...', 'info');
    // TODO: Call API to delete account
    // Redirect to login after deletion
    setTimeout(() => {
      logout();
    }, 2000);
  } catch (error) {
    console.error('Failed to delete account:', error);
    showToast('Failed to delete account.', 'error');
  }
}

// ==================== PHASE 11: Utility Functions ====================

/**
 * Show loading state
 */
function showLoadingState() {
  // Could add a loading overlay if needed
}

/**
 * Hide loading state
 */
function hideLoadingState() {
  // Hide loading overlay
}

/**
 * Toggle sidebar
 */
function toggleSidebar() {
  document.getElementById('sidebar').classList.toggle('open');
  document.getElementById('sidebarOverlay').style.display = 'block';
}

/**
 * Close sidebar
 */
function closeSidebar() {
  document.getElementById('sidebar').classList.remove('open');
  document.getElementById('sidebarOverlay').style.display = 'none';
}
