/**
 * main.js - Project Hub Global JavaScript
 * Dark mode toggle, dynamic forms, UI helpers
 */

// ─────────────────────────────────────────────
// DARK MODE
// ─────────────────────────────────────────────
const THEME_KEY = 'ph-theme';

function applyTheme(theme) {
  document.documentElement.setAttribute('data-theme', theme);
  document.body.setAttribute('data-theme', theme);
  const icon = document.getElementById('theme-icon');
  if (icon) {
    icon.className = theme === 'dark' ? 'bi bi-sun-fill' : 'bi bi-moon-fill';
  }
}

function toggleTheme() {
  const current = localStorage.getItem(THEME_KEY) || 'light';
  const next = current === 'dark' ? 'light' : 'dark';
  localStorage.setItem(THEME_KEY, next);
  applyTheme(next);
}

// Apply saved theme on load
(function () {
  const saved = localStorage.getItem(THEME_KEY) || 'light';
  applyTheme(saved);
})();

// ─────────────────────────────────────────────
// ADD PROJECT - DYNAMIC TEAM FIELDS
// ─────────────────────────────────────────────
function initAddProjectForm() {
  const typeSelect = document.getElementById('project_type');
  const teamSection = document.getElementById('team-section');

  if (typeSelect && teamSection) {
    typeSelect.addEventListener('change', function () {
      if (this.value === 'team') {
        teamSection.style.display = 'block';
        teamSection.classList.add('fade-in-up');
      } else {
        teamSection.style.display = 'none';
      }
    });
    // Trigger on load
    if (typeSelect.value === 'team') teamSection.style.display = 'block';
  }
}

// Add team member row dynamically
function addMemberRow() {
  const container = document.getElementById('members-container');
  if (!container) return;
  const row = document.createElement('div');
  row.className = 'row g-2 mb-2 member-row fade-in-up';
  row.innerHTML = `
    <div class="col-md-4">
      <input type="text" name="member_name[]" class="form-control" placeholder="Member Name" required>
    </div>
    <div class="col-md-4">
      <input type="text" name="member_role[]" class="form-control" placeholder="Role (e.g. Developer)">
    </div>
    <div class="col-md-3">
      <input type="email" name="member_email[]" class="form-control" placeholder="Email">
    </div>
    <div class="col-md-1">
      <button type="button" class="btn btn-sm btn-outline-danger w-100" onclick="removeMemberRow(this)">
        <i class="bi bi-trash"></i>
      </button>
    </div>`;
  container.appendChild(row);
}

function removeMemberRow(btn) {
  btn.closest('.member-row').remove();
}

// ─────────────────────────────────────────────
// AUTO-DISMISS ALERTS
// ─────────────────────────────────────────────
function initAlerts() {
  document.querySelectorAll('.alert:not(.alert-permanent)').forEach(function (alert) {
    setTimeout(function () {
      const bsAlert = new bootstrap.Alert(alert);
      if (bsAlert) bsAlert.close();
    }, 5000);
  });
}

// ─────────────────────────────────────────────
// FILE INPUT LABEL UPDATE
// ─────────────────────────────────────────────
function initFileInputs() {
  document.querySelectorAll('.custom-file-input, input[type="file"]').forEach(function (input) {
    input.addEventListener('change', function () {
      const label = this.nextElementSibling;
      if (label && label.tagName === 'LABEL') {
        label.textContent = this.files[0] ? this.files[0].name : 'Choose file';
      }
      // Show file size warning
      if (this.files[0] && this.files[0].size > 16 * 1024 * 1024) {
        showToast('File size must be under 16MB.', 'warning');
        this.value = '';
      }
    });
  });
}

// ─────────────────────────────────────────────
// TOAST NOTIFICATIONS
// ─────────────────────────────────────────────
function showToast(message, type = 'info') {
  const container = document.getElementById('toast-container');
  if (!container) return;
  const id = 'toast-' + Date.now();
  const colorMap = { success: 'bg-success', danger: 'bg-danger', warning: 'bg-warning text-dark', info: 'bg-info text-dark' };
  const html = `
    <div id="${id}" class="toast align-items-center ${colorMap[type] || 'bg-info'} text-white border-0" role="alert" aria-live="assertive">
      <div class="d-flex">
        <div class="toast-body">${message}</div>
        <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
      </div>
    </div>`;
  container.insertAdjacentHTML('beforeend', html);
  const toastEl = document.getElementById(id);
  const bsToast = new bootstrap.Toast(toastEl, { delay: 4000 });
  bsToast.show();
  toastEl.addEventListener('hidden.bs.toast', () => toastEl.remove());
}

// ─────────────────────────────────────────────
// CONFIRM ACTIONS
// ─────────────────────────────────────────────
function confirmAction(message, formId) {
  if (confirm(message)) {
    document.getElementById(formId).submit();
  }
}

// ─────────────────────────────────────────────
// MOBILE SIDEBAR TOGGLE
// ─────────────────────────────────────────────
function toggleSidebar() {
  const sidebar = document.querySelector('.sidebar');
  if (sidebar) sidebar.classList.toggle('open');
}

// ─────────────────────────────────────────────
// INITIALIZE ON DOM READY
// ─────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', function () {
  initAlerts();
  initAddProjectForm();
  initFileInputs();
  // Tooltips
  document.querySelectorAll('[data-bs-toggle="tooltip"]').forEach(function (el) {
    new bootstrap.Tooltip(el);
  });
  // Popovers
  document.querySelectorAll('[data-bs-toggle="popover"]').forEach(function (el) {
    new bootstrap.Popover(el);
  });
});
