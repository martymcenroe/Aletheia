// extensions/firefox/popup.js
// Firefox MV3 - uses browser.* API
// See: docs/1206-firefox-oauth.md

// State management - use window.currentDomain as source of truth (Issue #214)
window.currentDomain = null;
const selectedDomains = new Set();

// Expose selectedDomains for testing (Issue #214)
window.selectedDomains = selectedDomains;

// DOM Elements - Views
const loginView = document.getElementById('login-view');
const mainView = document.getElementById('main-view');
const manageView = document.getElementById('manage-view');
const confirmView = document.getElementById('confirm-view');
const restrictedView = document.getElementById('restricted-view');
const checkingView = document.getElementById('checking-view');

// Auth Elements (Issue #206)
const loginButton = document.getElementById('login-button');
const loginError = document.getElementById('login-error');
const userBar = document.getElementById('user-bar');
const userName = document.getElementById('user-name');
const logoutButton = document.getElementById('logout-button');

const currentDomainEl = document.getElementById('current-domain');
const statusLabel = document.getElementById('status-label');
const statusText = document.querySelector('.status-text');
const powerButton = document.getElementById('power-button');

const manageButton = document.getElementById('manage-button');
const backButton = document.getElementById('back-button');

const siteCount = document.getElementById('site-count');
const allowlistEl = document.getElementById('allowlist');
const emptyState = document.getElementById('empty-state');
const removeButton = document.getElementById('remove-button');
const clearAllButton = document.getElementById('clear-all-button');

const cancelButton = document.getElementById('cancel-button');
const confirmClearButton = document.getElementById('confirm-clear-button');

// ============================================================================
// STORAGE FUNCTIONS
// ============================================================================

async function getCurrentDomain() {
  try {
    const [tab] = await browser.tabs.query({ active: true, currentWindow: true });
    if (!tab || !tab.url) return null;

    const url = new URL(tab.url);
    // Strip www. prefix for normalization
    return url.hostname.replace(/^www\./, '');
  } catch (error) {
    console.error('[Aletheia] Error getting current domain:', error);
    return null;
  }
}

async function getAllowlist() {
  try {
    const result = await browser.storage.local.get('allowlist');
    return result.allowlist || [];
  } catch (error) {
    console.error('[Aletheia] Error getting allowlist:', error);
    return [];
  }
}

async function isAllowlisted(domain) {
  const allowlist = await getAllowlist();
  return allowlist.includes(domain);
}

async function addToAllowlist(domain) {
  try {
    const allowlist = await getAllowlist();
    if (!allowlist.includes(domain)) {
      allowlist.push(domain);
      await browser.storage.local.set({ allowlist });
    }
  } catch (error) {
    console.error('[Aletheia] Error adding to allowlist:', error);
  }
}

async function removeFromAllowlist(domain) {
  try {
    const allowlist = await getAllowlist();
    const filtered = allowlist.filter(d => d !== domain);
    await browser.storage.local.set({ allowlist: filtered });
  } catch (error) {
    console.error('[Aletheia] Error removing from allowlist:', error);
  }
}

async function removeManyFromAllowlist(domains) {
  try {
    const allowlist = await getAllowlist();
    const filtered = allowlist.filter(d => !domains.includes(d));
    await browser.storage.local.set({ allowlist: filtered });
  } catch (error) {
    console.error('[Aletheia] Error removing many from allowlist:', error);
  }
}

async function clearAllData() {
  try {
    await browser.storage.local.set({ allowlist: [] });
  } catch (error) {
    console.error('[Aletheia] Error clearing all data:', error);
  }
}

// ============================================================================
// VIEW RENDERING
// ============================================================================

function showView(viewName) {
  // Hide all views
  if (loginView) loginView.style.display = 'none';
  if (mainView) mainView.style.display = 'none';
  if (manageView) manageView.style.display = 'none';
  if (confirmView) confirmView.style.display = 'none';
  if (restrictedView) restrictedView.style.display = 'none';
  if (checkingView) checkingView.style.display = 'none';

  // Show requested view
  if (viewName === 'login' && loginView) {
    loginView.style.display = 'block';
  } else if (viewName === 'main' && mainView) {
    mainView.style.display = 'block';
  } else if (viewName === 'manage' && manageView) {
    manageView.style.display = 'block';
  } else if (viewName === 'confirm' && confirmView) {
    confirmView.style.display = 'block';
  } else if (viewName === 'restricted' && restrictedView) {
    restrictedView.style.display = 'block';
  } else if (viewName === 'checking' && checkingView) {
    checkingView.style.display = 'block';
  }
}

async function renderMainView() {
  const domain = await getCurrentDomain();
  window.currentDomain = domain;

  if (!domain) {
    currentDomainEl.textContent = 'Unknown';
    powerButton.disabled = true;
    return;
  }

  currentDomainEl.textContent = domain;
  const isActive = await isAllowlisted(domain);

  // Update power button state
  if (isActive) {
    powerButton.classList.add('active');
    statusLabel.textContent = 'ACTIVE';
    statusText.classList.add('active');
  } else {
    powerButton.classList.remove('active');
    statusLabel.textContent = 'INACTIVE';
    statusText.classList.remove('active');
  }
}

async function renderManagementView() {
  const allowlist = await getAllowlist();

  // Update count
  const count = allowlist.length;
  siteCount.textContent = `${count} ${count === 1 ? 'site' : 'sites'}`;

  // Show/hide empty state
  if (allowlist.length === 0) {
    emptyState.style.display = 'block';
    allowlistEl.classList.remove('has-items');
  } else {
    emptyState.style.display = 'none';
    allowlistEl.classList.add('has-items');

    // Render list items - clear safely without innerHTML (XSS hardening)
    while (allowlistEl.firstChild) {
      allowlistEl.removeChild(allowlistEl.firstChild);
    }
    allowlist.forEach(domain => {
      const item = createAllowlistItem(domain);
      allowlistEl.appendChild(item);
    });
  }

  // Reset selection and button state
  selectedDomains.clear();
  updateRemoveButton();
}

function createAllowlistItem(domain) {
  const label = document.createElement('label');
  label.className = 'allowlist-item';

  const checkbox = document.createElement('input');
  checkbox.type = 'checkbox';
  checkbox.dataset.domain = domain;
  checkbox.addEventListener('change', handleCheckboxChange);

  const domainSpan = document.createElement('span');
  domainSpan.className = 'allowlist-item-domain';
  domainSpan.textContent = domain;

  label.appendChild(checkbox);
  label.appendChild(domainSpan);

  // Add "current" badge if this is the current domain
  if (domain === window.currentDomain) {
    const badge = document.createElement('span');
    badge.className = 'current-badge';
    badge.textContent = 'current';
    label.appendChild(badge);
  }

  return label;
}

function updateRemoveButton() {
  if (selectedDomains.size > 0) {
    removeButton.disabled = false;
    removeButton.textContent = `Remove Selected (${selectedDomains.size})`;
  } else {
    removeButton.disabled = true;
    removeButton.textContent = 'Remove Selected';
  }
}

// ============================================================================
// EVENT HANDLERS
// ============================================================================

async function handlePowerToggle() {
  if (!window.currentDomain) return;

  const isActive = await isAllowlisted(window.currentDomain);

  if (isActive) {
    await removeFromAllowlist(window.currentDomain);
  } else {
    await addToAllowlist(window.currentDomain);
  }

  await renderMainView();
}

function handleCheckboxChange(event) {
  const domain = event.target.dataset.domain;
  const item = event.target.closest('.allowlist-item');

  if (event.target.checked) {
    selectedDomains.add(domain);
    item.classList.add('selected');
  } else {
    selectedDomains.delete(domain);
    item.classList.remove('selected');
  }

  updateRemoveButton();
}

async function handleRemoveSelected() {
  if (selectedDomains.size === 0) return;

  const domainsToRemove = Array.from(selectedDomains);
  await removeManyFromAllowlist(domainsToRemove);

  // Clear selection
  selectedDomains.clear();

  // Re-render management view
  await renderManagementView();

  // If current domain was removed, update main view
  if (domainsToRemove.includes(window.currentDomain)) {
    await renderMainView();
  }
}

async function handleClearAll() {
  await clearAllData();
  selectedDomains.clear();
  showView('main');
  await renderMainView();
}

function handleManageClick() {
  showView('manage');
  renderManagementView();
}

function handleBackClick() {
  showView('main');
  renderMainView();
}

function handleClearAllClick() {
  showView('confirm');
}

function handleCancelClick() {
  showView('manage');
}

function handleConfirmClearClick() {
  handleClearAll();
}

// ============================================================================
// AUTH HANDLERS (Issue #206)
// ============================================================================

async function handleLoginClick() {
  try {
    loginButton.disabled = true;
    loginButton.textContent = 'Signing in...';
    loginError.style.display = 'none';

    const user = await window.AletheiaAuth.initiateLogin();

    // Update user bar and proceed to main view
    userName.textContent = user.name;
    showView('main');
    await renderMainView();

  } catch (error) {
    console.error('[Aletheia] Login failed:', error);
    loginError.textContent = error.message || 'Login failed. Please try again.';
    loginError.style.display = 'block';
    loginButton.disabled = false;
    // Reset button content safely without innerHTML (XSS hardening)
    while (loginButton.firstChild) {
      loginButton.removeChild(loginButton.firstChild);
    }
    const iconSpan = document.createElement('span');
    iconSpan.className = 'linkedin-icon';
    iconSpan.textContent = 'in';
    loginButton.appendChild(iconSpan);
    loginButton.appendChild(document.createTextNode(' Sign in with LinkedIn'));
  }
}

async function handleLogoutClick() {
  await window.AletheiaAuth.logout();
  showView('login');
}

async function updateUserBar() {
  const authState = await window.AletheiaAuth.getAuthState();
  if (authState) {
    userName.textContent = authState.displayName;
    userBar.style.display = 'flex';
  } else {
    userBar.style.display = 'none';
  }
}

// ============================================================================
// INITIALIZATION
// ============================================================================

async function init() {
  // Auth event listeners (Issue #206)
  if (loginButton) {
    loginButton.addEventListener('click', handleLoginClick);
  }
  if (logoutButton) {
    logoutButton.addEventListener('click', handleLogoutClick);
  }

  // Main view event listeners
  powerButton.addEventListener('click', handlePowerToggle);
  manageButton.addEventListener('click', handleManageClick);

  // Management view event listeners
  backButton.addEventListener('click', handleBackClick);
  removeButton.addEventListener('click', handleRemoveSelected);
  clearAllButton.addEventListener('click', handleClearAllClick);

  // Confirm view event listeners
  cancelButton.addEventListener('click', handleCancelClick);
  confirmClearButton.addEventListener('click', handleConfirmClearClick);

  // Check auth state first (Issue #206)
  let isAuthed = false;
  try {
    isAuthed = await window.AletheiaAuth.isAuthenticated();
    console.log('[Aletheia] Auth check result:', isAuthed);
  } catch (e) {
    console.error('[Aletheia] Auth check failed:', e);
  }

  if (!isAuthed) {
    // Not logged in - show login view
    console.log('[Aletheia] Showing login view');
    showView('login');
    return;
  }

  // Update user bar with name
  console.log('[Aletheia] User authenticated, updating user bar');
  await updateUserBar();

  // Show main view and render
  showView('main');
  await renderMainView();
}

// Start the popup
document.addEventListener('DOMContentLoaded', init);
