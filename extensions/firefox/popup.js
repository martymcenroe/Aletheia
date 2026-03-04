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

// Full Page Elements (Issue #106)
const fullPageButton = document.getElementById('full-page-button');
const fullPageText = document.getElementById('full-page-text');
const fullPageStatus = document.getElementById('full-page-status');

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

    // Issue #396: initiateLogin delegates to service worker.
    // If the popup closes while LinkedIn tab is open, the service worker
    // continues the flow. When popup reopens, init() will find stored tokens.
    const user = await window.AletheiaAuth.initiateLogin();

    // If we get here, popup stayed open and flow completed
    userName.textContent = user.name;
    showView('main');
    await renderMainView();

  } catch (error) {
    // If the error is about the message channel closing (popup closing),
    // that's fine — the service worker will finish the flow
    if (error.message && (error.message.includes('disconnected') || error.message.includes('message port closed'))) {
      console.log('[Aletheia] Popup closing — service worker will complete OAuth');
      return;
    }

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
// FULL PAGE ANALYSIS (Issue #106)
// ============================================================================

// API endpoint (same as service-worker.js)
const API_ENDPOINT = "https://api.aletheia.study/";
const CLIENT_VERSION = "1.0";

/**
 * Check if current tab has noarchive signal.
 * Uses service worker to get cached noarchive status.
 */
async function checkNoarchive() {
  try {
    const [tab] = await browser.tabs.query({ active: true, currentWindow: true });
    if (!tab) return false;

    // Trigger a recheck to ensure we have the latest noarchive status
    await browser.runtime.sendMessage({
      type: 'RECHECK_TAB',
      tabId: tab.id
    });

    // Get the noarchive status from service worker
    const response = await browser.runtime.sendMessage({
      type: 'GET_NOARCHIVE_STATUS',
      tabId: tab.id
    });

    return response?.noarchive || false;
  } catch (error) {
    console.error('[Aletheia] Error checking noarchive:', error);
    return false;
  }
}

/**
 * Update full page button state based on noarchive signal.
 */
async function updateFullPageButton() {
  if (!fullPageButton) return;

  try {
    const hasNoarchive = await checkNoarchive();

    if (hasNoarchive) {
      // Hard Stop - button disabled
      fullPageButton.disabled = true;
      fullPageButton.classList.add('protected');
      fullPageText.textContent = 'Content Protected';
      fullPageButton.title = 'This page is marked noarchive - full retrieval disabled';

      // Show status message
      fullPageStatus.textContent = 'Publisher has restricted content archiving';
      fullPageStatus.classList.add('protected');
      fullPageStatus.style.display = 'block';
    } else {
      // Allow full page analysis
      fullPageButton.disabled = false;
      fullPageButton.classList.remove('protected');
      fullPageText.textContent = 'Analyze Full Page';
      fullPageButton.title = 'Analyze the full article content with AI';
      fullPageStatus.style.display = 'none';
    }
  } catch (error) {
    console.error('[Aletheia] Error updating full page button:', error);
    // Fail safe - disable button on error
    fullPageButton.disabled = true;
    fullPageText.textContent = 'Analyze Full Page';
  }
}

/**
 * Handle full page button click.
 * Extracts article content, scrubs PII, truncates, and sends to Lambda.
 */
async function handleFullPageClick() {
  if (!fullPageButton || fullPageButton.disabled) return;

  try {
    // Set loading state
    fullPageButton.disabled = true;
    fullPageButton.classList.add('loading');
    fullPageText.textContent = 'Analyzing...';
    fullPageStatus.textContent = 'Extracting article content...';
    fullPageStatus.classList.remove('error', 'protected');
    fullPageStatus.style.display = 'block';

    const [tab] = await browser.tabs.query({ active: true, currentWindow: true });
    if (!tab) {
      throw new Error('No active tab found');
    }

    // Inject article extractor script and get result
    fullPageStatus.textContent = 'Extracting article content...';

    const extractionResults = await browser.scripting.executeScript({
      target: { tabId: tab.id },
      files: ['article-extractor.js']
    });

    const extraction = extractionResults?.[0]?.result;
    if (!extraction || !extraction.text) {
      throw new Error('Failed to extract article content');
    }

    // Show extraction status
    const truncatedMsg = extraction.truncated ? ' (truncated)' : '';
    fullPageStatus.textContent = `Extracted ${extraction.text.length} chars${truncatedMsg}. Sending to AI...`;

    // Build payload with full_article field
    const payload = {
      text: '', // Empty selection - full article mode
      url: tab.url,
      title: tab.title,
      full_article: extraction.text,
      signals: {
        noarchive: false // Already checked, would be blocked if true
      }
    };

    // Send to Lambda (Issue #402: include JWT if authenticated)
    const jwt = await window.AletheiaAuth.getJwt();
    const fullPageHeaders = {
      'Content-Type': 'application/json',
      'X-Aletheia-Client-Version': CLIENT_VERSION
    };
    if (jwt) fullPageHeaders['Authorization'] = `Bearer ${jwt}`;

    const response = await fetch(API_ENDPOINT, {
      method: 'POST',
      headers: fullPageHeaders,
      body: JSON.stringify(payload)
    });

    const responseData = await response.json();

    if (!response.ok) {
      throw new Error(responseData.error || `Server error: ${response.status}`);
    }

    // Inject overlay.js if not already present
    await browser.scripting.executeScript({
      target: { tabId: tab.id },
      files: ['overlay.js']
    });

    // Show result in overlay
    await browser.scripting.executeScript({
      target: { tabId: tab.id },
      func: (data, status) => window.showAletheiaResult(data, status),
      args: [responseData, response.status]
    });

    // Success state
    fullPageStatus.textContent = 'Analysis complete!';
    fullPageText.textContent = 'Analyze Full Page';
    fullPageButton.disabled = false;
    fullPageButton.classList.remove('loading');

    // Close popup after showing result
    setTimeout(() => window.close(), 500);

  } catch (error) {
    console.error('[Aletheia] Full page analysis failed:', error);

    // Error state
    fullPageStatus.textContent = error.message || 'Analysis failed';
    fullPageStatus.classList.add('error');
    fullPageStatus.style.display = 'block';
    fullPageText.textContent = 'Analyze Full Page';
    fullPageButton.disabled = false;
    fullPageButton.classList.remove('loading');
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

  // Full page button (Issue #106)
  if (fullPageButton) {
    fullPageButton.addEventListener('click', handleFullPageClick);
  }

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
  await updateFullPageButton();  // Issue #106
}

// Start the popup
document.addEventListener('DOMContentLoaded', init);
