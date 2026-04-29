/* ============================================
   VantageTube AI – Global Utilities
   main.js
   ============================================ */

/* --- Sidebar Toggle (Mobile) --- */
function initSidebar() {
  const toggle = document.querySelector('.sidebar-toggle');
  const sidebar = document.querySelector('.sidebar');
  const overlay = document.getElementById('sidebarOverlay');

  if (!toggle || !sidebar) return;

  toggle.addEventListener('click', () => {
    sidebar.classList.toggle('open');
    if (overlay) overlay.classList.toggle('show');
  });

  if (overlay) {
    overlay.addEventListener('click', () => {
      sidebar.classList.remove('open');
      overlay.classList.remove('show');
    });
  }
}

/* --- Active Nav Item --- */
function setActiveNav() {
  const currentPage = window.location.pathname.split('/').pop() || 'dashboard.html';
  const navItems = document.querySelectorAll('.nav-item');
  navItems.forEach(item => {
    const href = item.getAttribute('href');
    if (href && currentPage.includes(href.replace('../pages/', '').replace('.html', ''))) {
      item.classList.add('active');
    }
  });
}

/* --- Toast Notifications --- */
function showToast(message, type = 'info', duration = 3000) {
  let container = document.querySelector('.toast-container');
  if (!container) {
    container = document.createElement('div');
    container.className = 'toast-container';
    document.body.appendChild(container);
  }

  const icons = { success: '✅', error: '❌', info: 'ℹ️', warning: '⚠️' };
  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  toast.innerHTML = `<span>${icons[type] || icons.info}</span><span>${message}</span>`;
  container.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateX(20px)';
    toast.style.transition = 'all 0.3s ease';
    setTimeout(() => toast.remove(), 300);
  }, duration);
}

/* --- Copy to Clipboard --- */
function copyToClipboard(text, btn) {
  navigator.clipboard.writeText(text).then(() => {
    if (btn) {
      const original = btn.innerHTML;
      btn.innerHTML = '✓ Copied';
      btn.classList.add('copied');
      setTimeout(() => {
        btn.innerHTML = original;
        btn.classList.remove('copied');
      }, 2000);
    }
    showToast('Copied to clipboard!', 'success', 2000);
  }).catch(() => {
    showToast('Failed to copy', 'error');
  });
}

/* --- Number Counter Animation --- */
function animateCounter(el, target, duration = 1500) {
  const isDecimal = target.toString().includes('.');
  const numericTarget = parseFloat(target.toString().replace(/[^0-9.]/g, ''));
  const suffix = target.toString().replace(/[0-9.]/g, '');
  let start = 0;
  const step = numericTarget / (duration / 16);

  const timer = setInterval(() => {
    start += step;
    if (start >= numericTarget) {
      start = numericTarget;
      clearInterval(timer);
    }
    el.textContent = (isDecimal ? start.toFixed(1) : Math.floor(start)) + suffix;
  }, 16);
}

/* --- Intersection Observer for Animations --- */
function initScrollAnimations() {
  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add('animate-fade-in-up');
        observer.unobserve(entry.target);
      }
    });
  }, { threshold: 0.1 });

  document.querySelectorAll('.feature-card, .step-item, .testimonial-card, .trending-card').forEach(el => {
    el.style.opacity = '0';
    observer.observe(el);
  });
}

/* --- Topbar Scroll Effect (Landing) --- */
function initNavbarScroll() {
  const navbar = document.querySelector('.navbar');
  if (!navbar) return;
  window.addEventListener('scroll', () => {
    navbar.classList.toggle('scrolled', window.scrollY > 20);
  });
}

/* --- Mobile Nav Toggle (Landing) --- */
function initMobileNav() {
  const toggle = document.querySelector('.nav-mobile-toggle');
  const menu = document.querySelector('.mobile-menu');
  if (!toggle || !menu) return;

  toggle.addEventListener('click', () => {
    menu.classList.toggle('open');
    toggle.textContent = menu.classList.contains('open') ? '✕' : '☰';
  });

  // Close on link click
  menu.querySelectorAll('a').forEach(link => {
    link.addEventListener('click', () => {
      menu.classList.remove('open');
      toggle.textContent = '☰';
    });
  });
}

/* --- Smooth Scroll for Anchor Links --- */
function initSmoothScroll() {
  document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', (e) => {
      const target = document.querySelector(anchor.getAttribute('href'));
      if (target) {
        e.preventDefault();
        target.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }
    });
  });
}

/* --- Format Numbers --- */
function formatNumber(num) {
  if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M';
  if (num >= 1000) return (num / 1000).toFixed(1) + 'K';
  return num.toString();
}

/* --- Get SEO Score Color --- */
function getSeoColor(score) {
  if (score >= 80) return 'var(--success)';
  if (score >= 60) return 'var(--warning)';
  return 'var(--danger)';
}

function getSeoClass(score) {
  if (score >= 80) return 'high';
  if (score >= 60) return 'medium';
  return 'low';
}

function getSeoGrade(score) {
  if (score >= 90) return { grade: 'Excellent', color: 'var(--success)' };
  if (score >= 75) return { grade: 'Good',      color: 'var(--success)' };
  if (score >= 60) return { grade: 'Average',   color: 'var(--warning)' };
  if (score >= 40) return { grade: 'Poor',      color: 'var(--danger)' };
  return                  { grade: 'Critical',  color: 'var(--danger)' };
}

/* --- Logout Function --- */
async function logout() {
  try {
    // Call logout endpoint
    await api.logout();
    
    // Redirect to login page (use absolute path from root)
    window.location.href = '/auth.html';
  } catch (error) {
    console.error('Logout error:', error);
    // Even if logout fails, clear local data and redirect
    api.clearToken();
    window.location.href = '/auth.html';
  }
}

/* --- Init on DOM Ready --- */
document.addEventListener('DOMContentLoaded', () => {
  initSidebar();
  setActiveNav();
  initNavbarScroll();
  initMobileNav();
  initSmoothScroll();
  initScrollAnimations();
});
