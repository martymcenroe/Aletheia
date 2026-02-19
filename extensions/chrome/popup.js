// extensions/chrome/popup.js
// State management - use window.currentDomain as source of truth (Issue #217)
window.currentDomain = null;
const selectedDomains = new Set();
let currentTabId = null;

// Expose selectedDomains for testing (Issue #217)
window.selectedDomains = selectedDomains;

// Tab State constants (must match service-worker.js)
const TabState = {
    UNKNOWN: 'unknown',
    RESTRICTED: 'restricted',
    ALLOWED: 'allowed'
};

// DOM Elements
const loginView = document.getElementById('login-view');
const mainView = document.getElementById('main-view');
const manageView = document.getElementById('manage-view');
const confirmView = document.getElementById('confirm-view');
const restrictedView = document.getElementById('restricted-view');
const checkingView = document.getElementById('checking-view');

// Auth Elements (Issue #116)
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
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
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
    const result = await chrome.storage.local.get('allowlist');
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
      await chrome.storage.local.set({ allowlist });
    }
  } catch (error) {
    console.error('[Aletheia] Error adding to allowlist:', error);
  }
}

async function removeFromAllowlist(domain) {
  try {
    const allowlist = await getAllowlist();
    const filtered = allowlist.filter(d => d !== domain);
    await chrome.storage.local.set({ allowlist: filtered });
  } catch (error) {
    console.error('[Aletheia] Error removing from allowlist:', error);
  }
}

async function removeManyFromAllowlist(domains) {
  try {
    const allowlist = await getAllowlist();
    const filtered = allowlist.filter(d => !domains.includes(d));
    await chrome.storage.local.set({ allowlist: filtered });
  } catch (error) {
    console.error('[Aletheia] Error removing many from allowlist:', error);
  }
}

async function clearAllData() {
  try {
    await chrome.storage.local.set({ allowlist: [] });
  } catch (error) {
    console.error('[Aletheia] Error clearing all data:', error);
  }
}

// ============================================================================
// VIEW RENDERING
// ============================================================================

function showView(viewName) {
  loginView.style.display = 'none';
  mainView.style.display = 'none';
  manageView.style.display = 'none';
  confirmView.style.display = 'none';
  restrictedView.style.display = 'none';
  checkingView.style.display = 'none';

  if (viewName === 'login') {
    loginView.style.display = 'block';
  } else if (viewName === 'main') {
    mainView.style.display = 'block';
  } else if (viewName === 'manage') {
    manageView.style.display = 'block';
  } else if (viewName === 'confirm') {
    confirmView.style.display = 'block';
  } else if (viewName === 'restricted') {
    restrictedView.style.display = 'block';
  } else if (viewName === 'checking') {
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
    // Deactivating - stay open so user sees the change
    await removeFromAllowlist(window.currentDomain);
    await renderMainView();
  } else {
    // Activating - add to allowlist and close popup
    await addToAllowlist(window.currentDomain);
    window.close();
  }
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
// AGE GATE FUNCTIONS (Issue #104)
// ============================================================================

async function getTabState(tabId) {
  try {
    const response = await chrome.runtime.sendMessage({
      type: 'GET_TAB_STATE',
      tabId: tabId
    });
    return response?.state || TabState.UNKNOWN;
  } catch (error) {
    console.error('[Aletheia] Error getting tab state:', error);
    return TabState.UNKNOWN;
  }
}

async function recheckTab(tabId) {
  try {
    await chrome.runtime.sendMessage({
      type: 'RECHECK_TAB',
      tabId: tabId
    });
  } catch (error) {
    console.error('[Aletheia] Error requesting recheck:', error);
  }
}

async function checkAgeGate() {
  try {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    if (!tab) {
      showView('main');
      return;
    }

    currentTabId = tab.id;
    const state = await getTabState(currentTabId);

    if (state === TabState.UNKNOWN) {
      // Show checking view while we wait
      showView('checking');
      // Request a recheck and poll for result
      await recheckTab(currentTabId);
      // Poll for state change (max 3 seconds)
      let attempts = 0;
      const maxAttempts = 15;
      const pollInterval = 200;

      const pollState = async () => {
        const newState = await getTabState(currentTabId);
        if (newState !== TabState.UNKNOWN || attempts >= maxAttempts) {
          if (newState === TabState.RESTRICTED) {
            showView('restricted');
          } else {
            showView('main');
            await renderMainView();
            await updateFullPageButton();  // Issue #106
          }
        } else {
          attempts++;
          setTimeout(pollState, pollInterval);
        }
      };
      await pollState();
    } else if (state === TabState.RESTRICTED) {
      showView('restricted');
    } else {
      showView('main');
      await renderMainView();
      await updateFullPageButton();  // Issue #106
    }
  } catch (error) {
    console.error('[Aletheia] Age gate check failed:', error);
    // Fail open - show main view
    showView('main');
    await renderMainView();
    await updateFullPageButton();  // Issue #106
  }
}

// ============================================================================
// AUTH HANDLERS (Issue #116)
// ============================================================================

async function handleLoginClick() {
  try {
    loginButton.disabled = true;
    loginButton.textContent = 'Signing in...';
    loginError.style.display = 'none';

    const user = await window.AletheiaAuth.initiateLogin();

    // Update user bar and proceed to main flow
    userName.textContent = user.name;
    await checkAgeGate();

  } catch (error) {
    console.error('[Aletheia] Login failed:', error);
    loginError.textContent = error.message || 'Login failed. Please try again.';
    loginError.style.display = 'block';
    loginButton.disabled = false;
    // Reset button content safely without innerHTML (XSS hardening)
    // Matches popup.html structure: <span class="linkedin-icon">in</span> Sign in with LinkedIn
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
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    if (!tab) return false;

    // Trigger a recheck to ensure we have the latest noarchive status
    await chrome.runtime.sendMessage({
      type: 'RECHECK_TAB',
      tabId: tab.id
    });

    // Get the noarchive status from service worker
    // The service worker stores this in tabNoArchive Map
    const response = await chrome.runtime.sendMessage({
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

    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    if (!tab) {
      throw new Error('No active tab found');
    }

    // Inject article extractor script and get result
    fullPageStatus.textContent = 'Extracting article content...';

    const extractionResults = await chrome.scripting.executeScript({
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

    // Send to Lambda
    const response = await fetch(API_ENDPOINT, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Aletheia-Client-Version': CLIENT_VERSION
      },
      body: JSON.stringify(payload)
    });

    const responseData = await response.json();

    if (!response.ok) {
      throw new Error(responseData.error || `Server error: ${response.status}`);
    }

    // Inject overlay.js if not already present
    await chrome.scripting.executeScript({
      target: { tabId: tab.id },
      files: ['overlay.js']
    });

    // Show result in overlay
    await chrome.scripting.executeScript({
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
// COUPON REDEMPTION (Issue #367)
// ============================================================================

// Auth API endpoint (same host as analysis API)
const AUTH_API_ENDPOINT = "https://api.aletheia.study/redeem-coupon";

const couponToggle = document.getElementById('coupon-toggle');
const couponArrow = document.getElementById('coupon-arrow');
const couponForm = document.getElementById('coupon-form');
const couponInput = document.getElementById('coupon-input');
const couponEmail = document.getElementById('coupon-email');
const couponSubmit = document.getElementById('coupon-submit');
const couponStatus = document.getElementById('coupon-status');

/**
 * Toggle coupon form visibility.
 */
function handleCouponToggle() {
  if (!couponForm) return;
  const isVisible = couponForm.style.display !== 'none';
  couponForm.style.display = isVisible ? 'none' : 'block';
  if (couponArrow) {
    couponArrow.textContent = isVisible ? '\u2192' : '\u2193';
  }
}

/**
 * Validate coupon input and enable/disable submit button.
 */
function handleCouponInput() {
  if (!couponInput || !couponSubmit) return;
  const code = couponInput.value.trim().toUpperCase();
  const isValid = /^[A-Z0-9]{16}$/.test(code);
  couponSubmit.disabled = !isValid;
}

/**
 * Submit coupon code for redemption.
 */
async function handleCouponSubmit() {
  if (!couponInput || !couponSubmit || couponSubmit.disabled) return;

  const code = couponInput.value.trim().toUpperCase();
  const email = couponEmail ? couponEmail.value.trim() : '';

  // Validate email if provided
  if (email && !/^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/.test(email)) {
    showCouponStatus('Invalid email format', 'error');
    return;
  }

  // Set loading state
  couponSubmit.disabled = true;
  couponSubmit.textContent = 'Redeeming...';
  showCouponStatus('Validating coupon...', 'info');

  try {
    // Get JWT from auth state
    const authState = await window.AletheiaAuth.getAuthState();
    if (!authState || !authState.jwt) {
      showCouponStatus('Please sign in first', 'error');
      return;
    }

    const payload = { code };
    if (email) {
      payload.email = email;
    }

    const response = await fetch(AUTH_API_ENDPOINT, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${authState.jwt}`
      },
      body: JSON.stringify(payload)
    });

    const data = await response.json();

    if (response.ok && data.status === 'success') {
      showCouponStatus(`Upgraded to ${data.tier}!`, 'success');
      couponInput.value = '';
      if (couponEmail) couponEmail.value = '';
      couponSubmit.disabled = true;
    } else {
      const errorMessages = {
        'invalid_code': 'Invalid or expired coupon code',
        'code_expired': 'This coupon has expired',
        'code_exhausted': 'This coupon has already been used',
        'internal_error': 'Something went wrong. Please try again.',
        'Invalid coupon code format': 'Invalid coupon code format',
        'Invalid email format': 'Invalid email format'
      };
      const msg = errorMessages[data.error] || data.error || 'Redemption failed';
      showCouponStatus(msg, 'error');
    }
  } catch (_err) {
    showCouponStatus('Network error. Please try again.', 'error');
  } finally {
    couponSubmit.textContent = 'Redeem Coupon';
    handleCouponInput(); // Re-evaluate button state
  }
}

/**
 * Show coupon status message.
 */
function showCouponStatus(message, type) {
  if (!couponStatus) return;
  couponStatus.textContent = message;
  couponStatus.className = 'coupon-status ' + type;
  couponStatus.style.display = 'block';
}

// ============================================================================
// SUBSCRIPTION STATUS (Issue #366)
// ============================================================================

const SUBSCRIPTION_STATUS_URL = "https://api.aletheia.study/subscription-status";
const CHECKOUT_URL = "https://api.aletheia.study/create-checkout-session";

const subscriptionSection = document.getElementById('subscription-section');
const subscriptionStatusEl = document.getElementById('subscription-status');
const upgradeButton = document.getElementById('upgrade-button');
const tierBadge = document.getElementById('user-tier-badge');

/**
 * Check and display subscription status.
 */
async function checkSubscriptionStatus() {
  if (!subscriptionSection) return;

  try {
    const authState = await window.AletheiaAuth.getAuthState();
    if (!authState || !authState.jwt) return;

    const response = await fetch(SUBSCRIPTION_STATUS_URL, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${authState.jwt}`
      }
    });

    if (!response.ok) return;

    const data = await response.json();
    subscriptionSection.style.display = 'block';

    // Update tier badge
    if (tierBadge && data.tier !== 'free') {
      tierBadge.textContent = data.tier;
      tierBadge.style.display = 'inline-block';
    }

    if (data.status === 'active') {
      subscriptionStatusEl.textContent = 'Premium subscription active';
      subscriptionStatusEl.className = 'subscription-status active';
      if (upgradeButton) upgradeButton.style.display = 'none';
    } else if (data.status === 'grace_period') {
      const days = data.grace_period_days_remaining || 0;
      subscriptionStatusEl.textContent = `Payment issue - ${days} day${days !== 1 ? 's' : ''} to resolve`;
      subscriptionStatusEl.className = 'subscription-status grace';
      if (upgradeButton) upgradeButton.style.display = 'none';
    } else {
      subscriptionStatusEl.textContent = 'Free tier';
      subscriptionStatusEl.className = 'subscription-status free';
      if (upgradeButton) upgradeButton.style.display = 'block';
    }
  } catch (_err) {
    // Subscription status is non-critical, fail silently
  }
}

/**
 * Handle upgrade button click — redirect to Stripe Checkout.
 */
async function handleUpgradeClick() {
  if (!upgradeButton) return;

  upgradeButton.disabled = true;
  upgradeButton.textContent = 'Redirecting...';

  try {
    const authState = await window.AletheiaAuth.getAuthState();
    if (!authState || !authState.jwt) {
      upgradeButton.textContent = 'Please sign in first';
      return;
    }

    const response = await fetch(CHECKOUT_URL, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${authState.jwt}`
      }
    });

    const data = await response.json();

    if (response.ok && data.checkout_url) {
      // Open Stripe Checkout in a new tab
      chrome.tabs.create({ url: data.checkout_url });
      window.close();
    } else {
      upgradeButton.textContent = 'Upgrade failed';
      setTimeout(() => {
        upgradeButton.textContent = 'Upgrade to Premium';
        upgradeButton.disabled = false;
      }, 3000);
    }
  } catch (_err) {
    upgradeButton.textContent = 'Network error';
    setTimeout(() => {
      upgradeButton.textContent = 'Upgrade to Premium';
      upgradeButton.disabled = false;
    }, 3000);
  }
}

// ============================================================================
// INITIALIZATION
// ============================================================================

async function init() {
  // Auth event listeners (Issue #116)
  loginButton.addEventListener('click', handleLoginClick);
  logoutButton.addEventListener('click', handleLogoutClick);

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

  // Coupon redemption (Issue #367)
  if (couponToggle) {
    couponToggle.addEventListener('click', handleCouponToggle);
  }
  if (couponInput) {
    couponInput.addEventListener('input', handleCouponInput);
  }
  if (couponSubmit) {
    couponSubmit.addEventListener('click', handleCouponSubmit);
  }

  // Subscription upgrade (Issue #366)
  if (upgradeButton) {
    upgradeButton.addEventListener('click', handleUpgradeClick);
  }

  // Check auth state first (Issue #116)
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

  // Check subscription status (Issue #366) — non-blocking
  checkSubscriptionStatus();

  // Issue #391 Phase 4: Load diagnostics — non-blocking
  loadDiagnostics();

  // Age gate check, then render appropriate view
  await checkAgeGate();
}

// ============================================================================
// DIAGNOSTICS (Issue #391 Phase 4)
// ============================================================================

/**
 * Load last request diagnostics from chrome.storage.session and display in popup.
 */
async function loadDiagnostics() {
  const section = document.getElementById('diagnostics-section');
  if (!section) return;

  try {
    const result = await chrome.storage.session.get('aletheiaLastRequest');
    const diag = result?.aletheiaLastRequest;
    if (!diag) return;

    section.style.display = 'block';

    const statusEl = document.getElementById('diagnostics-status');
    const latencyEl = document.getElementById('diagnostics-latency');
    const timeEl = document.getElementById('diagnostics-time');
    const errorEl = document.getElementById('diagnostics-error');

    if (statusEl) statusEl.textContent = `Status: ${diag.lastRequestStatus}`;
    if (latencyEl) latencyEl.textContent = `Latency: ${diag.lastRequestLatency}ms`;
    if (timeEl && diag.lastRequestTimestamp) {
      const date = new Date(diag.lastRequestTimestamp);
      timeEl.textContent = `Time: ${date.toLocaleTimeString()}`;
    }
    if (errorEl && diag.lastError) {
      errorEl.textContent = diag.lastError;
      errorEl.style.display = 'block';
    }
  } catch (e) {
    console.warn('[Aletheia] Failed to load diagnostics:', e);
  }
}

// Start the popup
document.addEventListener('DOMContentLoaded', init);
