/**
 * Settings Page Logic with API Integration
 * Handles user preferences, notifications, and account settings
 */

// Protect this page - require authentication
if (!requireAuth()) {
  // User will be redirected to login
}

// Global state
let hasUnsavedChanges = false;
let currentSettings = {};

// Initialize settings page
document.addEventListener('DOMContentLoaded', () => {
  loadUserSettings();
  setupEventListeners();
});

/**
 * Load user settings from API
 */
async function loadUserSettings() {
  try {
    // Load user settings
    currentSettings = await api.getUserSettings();
    
    // Apply settings to UI
    applySettingsToUI(currentSettings);
    
    // Load user profile for sidebar
    const user = await api.getUserProfile();
    updateSidebarUser(user);
  } catch (error) {
    console.error('Failed to load settings:', error);
    showToast('Failed to load settings. Using defaults.', 'error');
  }
}

/**
 * Apply settings to UI elements
 */
function applySettingsToUI(settings) {
  // Appearance settings
  if (settings.theme) {
    const themeOptions = document.querySelectorAll('.theme-option');
    themeOptions.forEach(option => {
      if (option.querySelector('.theme-preview').classList.contains(`theme-preview-${settings.theme}`)) {
        option.classList.add('selected');
      } else {
        option.classList.remove('selected');
      }
    });
  }
  
  if (settings.dark_mode !== undefined) {
    document.getElementById('darkModeToggle').checked = settings.dark_mode;
  }
  
  // Notification settings
  if (settings.email_notifications !== undefined) {
    const emailToggle = document.querySelector('#section-notifications input[type="checkbox"]');
    if (emailToggle) emailToggle.checked = settings.email_notifications;
  }
  
  if (settings.weekly_report !== undefined) {
    const weeklyToggle = document.querySelectorAll('#section-notifications input[type="checkbox"]')[1];
    if (weeklyToggle) weeklyToggle.checked = settings.weekly_report;
  }
  
  if (settings.trending_alerts !== undefined) {
    const trendingToggle = document.querySelectorAll('#section-notifications input[type="checkbox"]')[2];
    if (trendingToggle) trendingToggle.checked = settings.trending_alerts;
  }
  
  // Privacy settings
  if (settings.profile_visibility !== undefined) {
    const profileToggle = document.querySelector('#section-privacy input[type="checkbox"]');
    if (profileToggle) profileToggle.checked = settings.profile_visibility;
  }
  
  if (settings.analytics_sharing !== undefined) {
    const analyticsToggle = document.querySelectorAll('#section-privacy input[type="checkbox"]')[1];
    if (analyticsToggle) analyticsToggle.checked = settings.analytics_sharing;
  }
}

/**
 * Update sidebar user info
 */
function updateSidebarUser(user) {
  const sidebarName = document.querySelector('.sidebar-user .user-name');
  const sidebarAvatar = document.querySelector('.sidebar-user .avatar');
  
  if (sidebarName) {
    sidebarName.textContent = user.full_name || user.email;
  }
  
  if (sidebarAvatar && user.avatar_url) {
    sidebarAvatar.style.backgroundImage = `url(${user.avatar_url})`;
    sidebarAvatar.style.backgroundSize = 'cover';
    sidebarAvatar.textContent = '';
  } else if (sidebarAvatar) {
    const initials = user.full_name 
      ? user.full_name.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2)
      : user.email[0].toUpperCase();
    sidebarAvatar.textContent = initials;
  }
}

/**
 * Setup event listeners
 */
function setupEventListeners() {
  // Listen for beforeunload to warn about unsaved changes
  window.addEventListener('beforeunload', (e) => {
    if (hasUnsavedChanges) {
      e.preventDefault();
      e.returnValue = '';
    }
  });
}

/**
 * Switch between settings sections
 */
function switchSettingsSection(sectionName, buttonEl) {
  // Update nav items
  document.querySelectorAll('.settings-nav-item').forEach(item => {
    item.classList.remove('active');
  });
  buttonEl.classList.add('active');
  
  // Update sections
  document.querySelectorAll('.settings-section').forEach(section => {
    section.classList.remove('active');
  });
  document.getElementById(`section-${sectionName}`).classList.add('active');
}

/**
 * Mark that changes have been made
 */
function markChanged() {
  hasUnsavedChanges = true;
  document.getElementById('saveBanner').classList.add('show');
}

/**
 * Select theme
 */
function selectTheme(theme, element) {
  document.querySelectorAll('.theme-option').forEach(opt => {
    opt.classList.remove('selected');
  });
  element.classList.add('selected');
  markChanged();
}

/**
 * Select accent color
 */
function selectAccent(element, color) {
  document.querySelectorAll('.accent-swatch').forEach(swatch => {
    swatch.classList.remove('selected');
  });
  element.classList.add('selected');
  
  // Apply accent color to CSS variable (preview)
  document.documentElement.style.setProperty('--primary', color);
  
  markChanged();
}

/**
 * Toggle password visibility
 */
function togglePwVisibility(inputId, buttonEl) {
  const input = document.getElementById(inputId);
  if (input.type === 'password') {
    input.type = 'text';
    buttonEl.textContent = '🙈';
  } else {
    input.type = 'password';
    buttonEl.textContent = '👁️';
  }
}

/**
 * Check password strength
 */
function checkNewPwStrength(password) {
  const strengthFill = document.getElementById('pwStrengthFill');
  const strengthText = document.getElementById('pwStrengthText');
  
  if (!password) {
    strengthFill.style.width = '0%';
    strengthFill.className = 'pw-strength-fill';
    strengthText.textContent = 'Enter a password';
    return;
  }
  
  let strength = 0;
  
  // Length check
  if (password.length >= 8) strength += 25;
  if (password.length >= 12) strength += 15;
  
  // Character variety checks
  if (/[a-z]/.test(password)) strength += 15;
  if (/[A-Z]/.test(password)) strength += 15;
  if (/[0-9]/.test(password)) strength += 15;
  if (/[^a-zA-Z0-9]/.test(password)) strength += 15;
  
  // Update UI
  strengthFill.style.width = `${strength}%`;
  
  if (strength < 40) {
    strengthFill.className = 'pw-strength-fill weak';
    strengthText.textContent = 'Weak password';
  } else if (strength < 70) {
    strengthFill.className = 'pw-strength-fill medium';
    strengthText.textContent = 'Medium strength';
  } else {
    strengthFill.className = 'pw-strength-fill strong';
    strengthText.textContent = 'Strong password';
  }
}

/**
 * Save password
 */
async function savePassword() {
  const currentPw = document.getElementById('currentPw').value;
  const newPw = document.getElementById('newPw').value;
  const confirmPw = document.getElementById('confirmPw').value;
  
  // Validation
  if (!currentPw || !newPw || !confirmPw) {
    showToast('Please fill in all password fields', 'error');
    return;
  }
  
  if (newPw !== confirmPw) {
    showToast('New passwords do not match', 'error');
    return;
  }
  
  if (newPw.length < 8) {
    showToast('Password must be at least 8 characters', 'error');
    return;
  }
  
  try {
    showToast('Changing password...', 'info');
    
    await api.changePassword(currentPw, newPw);
    
    // Clear fields
    document.getElementById('currentPw').value = '';
    document.getElementById('newPw').value = '';
    document.getElementById('confirmPw').value = '';
    
    // Reset strength indicator
    document.getElementById('pwStrengthFill').style.width = '0%';
    document.getElementById('pwStrengthText').textContent = 'Enter a password';
    
    showToast('✅ Password changed successfully!', 'success');
  } catch (error) {
    console.error('Failed to change password:', error);
    showToast(error.message || 'Failed to change password', 'error');
  }
}

/**
 * Save all settings
 */
async function saveAllSettings() {
  try {
    // Collect settings from UI
    const settings = {
      // Appearance
      dark_mode: document.getElementById('darkModeToggle').checked,
      theme: document.querySelector('.theme-option.selected') 
        ? (document.querySelector('.theme-option.selected .theme-preview-dark') ? 'dark' : 'light')
        : 'dark',
      
      // Notifications
      email_notifications: document.querySelector('#section-notifications input[type="checkbox"]')?.checked || false,
      weekly_report: document.querySelectorAll('#section-notifications input[type="checkbox"]')[1]?.checked || false,
      trending_alerts: document.querySelectorAll('#section-notifications input[type="checkbox"]')[2]?.checked || false,
      new_features: document.querySelectorAll('#section-notifications input[type="checkbox"]')[3]?.checked || false,
      milestone_alerts: document.querySelectorAll('#section-notifications input[type="checkbox"]')[4]?.checked || false,
      
      // Privacy
      profile_visibility: document.querySelector('#section-privacy input[type="checkbox"]')?.checked || false,
      analytics_sharing: document.querySelectorAll('#section-privacy input[type="checkbox"]')[1]?.checked || false
    };
    
    showToast('Saving settings...', 'info');
    
    // Save to API
    const updatedSettings = await api.updateUserSettings(settings);
    
    // Update current settings
    currentSettings = updatedSettings;
    
    // Clear unsaved changes flag
    hasUnsavedChanges = false;
    document.getElementById('saveBanner').classList.remove('show');
    
    showToast('✅ Settings saved successfully!', 'success');
  } catch (error) {
    console.error('Failed to save settings:', error);
    showToast('Failed to save settings. Please try again.', 'error');
  }
}

/**
 * Discard changes
 */
function discardChanges() {
  if (confirm('Are you sure you want to discard all unsaved changes?')) {
    // Reload settings from current state
    applySettingsToUI(currentSettings);
    
    hasUnsavedChanges = false;
    document.getElementById('saveBanner').classList.remove('show');
    
    showToast('Changes discarded', 'info');
  }
}

/**
 * Confirm dangerous actions
 */
function confirmAction(action) {
  const messages = {
    'delete reports': 'Are you sure you want to delete all your SEO reports? This action cannot be undone.',
    'disconnect channels': 'Are you sure you want to disconnect all YouTube channels? This will remove all synced videos.',
    'delete account': 'Are you sure you want to permanently delete your account? This action cannot be undone and all your data will be lost.'
  };
  
  if (confirm(messages[action])) {
    showToast(`${action} feature will be implemented in a future update`, 'info');
  }
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
