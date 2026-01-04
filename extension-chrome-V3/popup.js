// extension-chrome-V3/popup.js
// State management
let currentDomain = null;
const selectedDomains = new Set();

// DOM Elements
const mainView = document.getElementById('main-view');
const manageView = document.getElementById('manage-view');
const confirmView = document.getElementById('confirm-view');

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
  mainView.style.display = 'none';
  manageView.style.display = 'none';
  confirmView.style.display = 'none';

  if (viewName === 'main') {
    mainView.style.display = 'block';
  } else if (viewName === 'manage') {
    manageView.style.display = 'block';
  } else if (viewName === 'confirm') {
    confirmView.style.display = 'block';
  }
}

async function renderMainView() {
  const domain = await getCurrentDomain();
  currentDomain = domain;

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

    // Render list items
    allowlistEl.innerHTML = '';
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
  if (domain === currentDomain) {
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
  if (!currentDomain) return;

  const isActive = await isAllowlisted(currentDomain);

  if (isActive) {
    await removeFromAllowlist(currentDomain);
  } else {
    await addToAllowlist(currentDomain);
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
  if (domainsToRemove.includes(currentDomain)) {
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
// INITIALIZATION
// ============================================================================

function init() {
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

  // Initial render
  renderMainView();
}

// Start the popup
document.addEventListener('DOMContentLoaded', init);
