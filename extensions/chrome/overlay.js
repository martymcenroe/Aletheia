// extensions/chrome/overlay.js
// Museum Label UI - Progressive Disclosure (Issue #125)
// See: docs/1125-museum-label-ui.md

// =============================================================================
// CONSTANTS
// =============================================================================

const OVERLAY_Z_INDEX = 2147483647; // Max z-index to beat all host content
const TYPEWRITER_DELAY_MS = 15;

// Badge types for color coding
const BadgeType = {
    WARNING: 'warning',   // Amber - soft block / contextual warning
    BLOCK: 'block',       // Red - hard block
    NEUTRAL: 'neutral',   // Blue - informational
};

// Overlay states
const OverlayState = {
    HARD_BLOCKED: 'hard_blocked',
    GLANCE: 'glance',
    HOVER: 'hover',
    EXPANDED: 'expanded',
};

// =============================================================================
// STYLES (Inline for Shadow DOM isolation)
// =============================================================================

const OVERLAY_STYLES = `
/* Reset */
*, *::before, *::after {
    box-sizing: border-box;
    margin: 0;
    padding: 0;
}

/* Card container */
.aletheia-card {
    position: absolute;
    background: #1F2937;
    color: #F9FAFB;
    border-radius: 8px;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    font-size: 14px;
    box-shadow: 0 4px 16px rgba(0,0,0,0.3);
    z-index: ${OVERLAY_Z_INDEX};
    min-width: 280px;
    max-width: 400px;
    overflow: hidden;
}

.aletheia-card.hard-block {
    cursor: not-allowed;
}

/* Pointer arrow */
.aletheia-card::after {
    content: '';
    position: absolute;
    border-style: solid;
}

.aletheia-card.below::after {
    bottom: 100%;
    left: 24px;
    border-width: 0 8px 8px 8px;
    border-color: transparent transparent #374151 transparent;
}

.aletheia-card.above::after {
    top: 100%;
    left: 24px;
    border-width: 8px 8px 0 8px;
    border-color: #1F2937 transparent transparent transparent;
}

/* Header row */
.aletheia-header {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 12px 14px;
    background: #374151;
    border-bottom: 1px solid #4B5563;
}

/* Badge */
.aletheia-badge {
    width: 24px;
    height: 24px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 700;
    font-size: 14px;
    flex-shrink: 0;
}

.aletheia-badge.warning {
    background: #FBBF24;
    color: #1F2937;
}

.aletheia-badge.block {
    background: #EF4444;
    color: #FFFFFF;
}

.aletheia-badge.neutral {
    background: #3B82F6;
    color: #FFFFFF;
}

/* Signal text */
.aletheia-signal {
    flex: 1;
    font-weight: 600;
    font-size: 14px;
    color: #F9FAFB;
}

/* Close button */
.aletheia-close {
    background: transparent;
    border: none;
    color: #9CA3AF;
    font-size: 20px;
    cursor: pointer;
    padding: 4px 8px;
    line-height: 1;
    border-radius: 4px;
    transition: background 0.15s ease, color 0.15s ease;
}

.aletheia-close:hover {
    background: #4B5563;
    color: #F9FAFB;
}

.aletheia-close:focus {
    outline: 2px solid #3B82F6;
    outline-offset: 2px;
}

/* Gem section (Tier 2) */
.aletheia-gem {
    padding: 12px 14px;
    font-size: 13px;
    line-height: 1.5;
    color: #D1D5DB;
    border-bottom: 1px solid #374151;
    max-height: 0;
    overflow: hidden;
    padding-top: 0;
    padding-bottom: 0;
    transition: max-height 0.2s ease-out, padding 0.2s ease-out;
}

.aletheia-gem.visible {
    max-height: 100px;
    padding: 12px 14px;
}

/* Hard block: gem always hidden */
.aletheia-card.hard-block .aletheia-gem {
    display: none;
}

/* Context section (Tier 3) */
.aletheia-context {
    padding: 0 14px;
    font-size: 13px;
    line-height: 1.6;
    color: #D1D5DB;
    max-height: 0;
    overflow: hidden;
    transition: max-height 0.3s ease-out, padding 0.3s ease-out;
}

.aletheia-context.expanded {
    max-height: 200px;
    padding: 12px 14px;
}

/* Hard block: context always hidden */
.aletheia-card.hard-block .aletheia-context {
    display: none;
}

/* Toggle button */
.aletheia-toggle {
    display: block;
    width: 100%;
    background: transparent;
    border: none;
    color: #9CA3AF;
    font-size: 12px;
    padding: 10px 14px;
    cursor: pointer;
    text-align: left;
    transition: background 0.15s ease, color 0.15s ease;
}

.aletheia-toggle:hover {
    background: #374151;
    color: #F9FAFB;
}

.aletheia-toggle:focus {
    outline: 2px solid #3B82F6;
    outline-offset: -2px;
}

/* Hard block: toggle hidden */
.aletheia-card.hard-block .aletheia-toggle {
    display: none;
}

/* Loading state */
.aletheia-loading {
    padding: 16px 14px;
    color: #9CA3AF;
    font-size: 13px;
    display: flex;
    align-items: center;
    gap: 10px;
}

.aletheia-spinner {
    width: 16px;
    height: 16px;
    border: 2px solid #4B5563;
    border-top-color: #FBBF24;
    border-radius: 50%;
    animation: spin 1s linear infinite;
}

@keyframes spin {
    to { transform: rotate(360deg); }
}

/* Blocked message for hard block */
.aletheia-blocked-message {
    padding: 12px 14px;
    font-size: 13px;
    color: #FCA5A5;
}
`;

// =============================================================================
// TYPEWRITER ANIMATION
// =============================================================================

let typewriterAbort = null;

function typewriterRender(element, text, delayMs = TYPEWRITER_DELAY_MS) {
    // Cancel any existing animation
    if (typewriterAbort) {
        typewriterAbort.abort = true;
    }

    const controller = { abort: false };
    typewriterAbort = controller;

    element.textContent = '';
    let index = 0;

    function renderNext() {
        if (controller.abort || index >= text.length) {
            typewriterAbort = null;
            return;
        }

        element.textContent += text[index];
        index++;

        setTimeout(() => {
            requestAnimationFrame(renderNext);
        }, delayMs);
    }

    requestAnimationFrame(renderNext);
}

function stopTypewriter() {
    if (typewriterAbort) {
        typewriterAbort.abort = true;
        typewriterAbort = null;
    }
}

// =============================================================================
// HELPER FUNCTIONS
// =============================================================================

/**
 * Determine if response indicates a hard block.
 * Hard blocks occur on HTTP 403 or signal containing "block".
 */
function isHardBlock(response, httpStatus) {
    if (httpStatus === 403) return true;
    if (!response || !response.signal) return false;
    const signalLower = response.signal.toLowerCase();
    return signalLower.includes('hard block') ||
           signalLower === 'blocked' ||
           signalLower.includes('hate speech') ||
           signalLower.includes('severe');
}

/**
 * Determine badge type based on response signal.
 */
function getBadgeType(response) {
    if (!response || !response.signal) return BadgeType.NEUTRAL;

    const signalLower = response.signal.toLowerCase();

    // Block indicators (red)
    if (signalLower.includes('block') ||
        signalLower.includes('hate') ||
        signalLower.includes('severe') ||
        signalLower.includes('slur')) {
        return BadgeType.BLOCK;
    }

    // Warning indicators (amber)
    if (signalLower.includes('pejorative') ||
        signalLower.includes('archaic') ||
        signalLower.includes('offensive') ||
        signalLower.includes('dated') ||
        signalLower.includes('derogatory') ||
        signalLower.includes('slang')) {
        return BadgeType.WARNING;
    }

    // Default to neutral (blue)
    return BadgeType.NEUTRAL;
}

/**
 * Get badge icon character.
 */
function getBadgeIcon(badgeType) {
    switch (badgeType) {
        case BadgeType.BLOCK: return '⊘';
        case BadgeType.WARNING: return '!';
        case BadgeType.NEUTRAL: return 'i';
        default: return '?';
    }
}

/**
 * Calculate overlay position relative to selection.
 */
function calculatePosition() {
    const selection = window.getSelection();
    if (selection.rangeCount === 0) return null;

    const rect = selection.getRangeAt(0).getBoundingClientRect();

    const OVERLAY_HEIGHT = 150; // Approximate
    const MARGIN_ABOVE = 8;
    const MARGIN_BELOW = 12;

    const spaceBelow = window.innerHeight - rect.bottom;
    const spaceNeeded = OVERLAY_HEIGHT + MARGIN_BELOW;

    let top, position;

    if (spaceBelow < spaceNeeded) {
        // Flip above
        top = window.scrollY + rect.top - OVERLAY_HEIGHT - MARGIN_ABOVE;
        position = 'above';
    } else {
        // Normal below
        top = window.scrollY + rect.bottom + MARGIN_BELOW;
        position = 'below';
    }

    const left = Math.max(10, window.scrollX + rect.left);

    return { top, left, position };
}

// =============================================================================
// OVERLAY MANAGEMENT
// =============================================================================

let currentOverlayState = null;
let overlayData = null;

/**
 * Remove existing overlay from DOM.
 */
function removeOverlay() {
    stopTypewriter();
    const existing = document.getElementById('aletheia-overlay-host');
    if (existing) existing.remove();
    currentOverlayState = null;
    overlayData = null;
}

/**
 * Update ARIA expanded attribute.
 */
function updateAriaExpanded(element, expanded) {
    if (element) {
        element.setAttribute('aria-expanded', expanded ? 'true' : 'false');
    }
}

/**
 * Show loading state overlay.
 */
function showLoadingOverlay() {
    removeOverlay();

    const pos = calculatePosition();
    if (!pos) return;

    const host = document.createElement('div');
    host.id = 'aletheia-overlay-host';
    const shadow = host.attachShadow({ mode: 'open' });

    shadow.innerHTML = `
        <style>${OVERLAY_STYLES}</style>
        <div class="aletheia-card ${pos.position}"
             style="top: ${pos.top}px; left: ${pos.left}px;"
             role="status"
             aria-label="Aletheia loading">
            <div class="aletheia-loading">
                <div class="aletheia-spinner"></div>
                <span>Analyzing...</span>
            </div>
        </div>
    `;

    document.body.appendChild(host);
}

/**
 * Show result overlay with Museum Label UI.
 */
function showResultOverlay(response, httpStatus = 200) {
    removeOverlay();

    const pos = calculatePosition();
    if (!pos) return;

    // Store for state management
    overlayData = response;
    const hardBlock = isHardBlock(response, httpStatus);
    const badgeType = hardBlock ? BadgeType.BLOCK : getBadgeType(response);
    const badgeIcon = getBadgeIcon(badgeType);

    currentOverlayState = hardBlock ? OverlayState.HARD_BLOCKED : OverlayState.GLANCE;

    // Create host and shadow DOM
    const host = document.createElement('div');
    host.id = 'aletheia-overlay-host';
    const shadow = host.attachShadow({ mode: 'open' });

    // Build HTML structure
    const signal = response?.signal || 'Analysis';
    const gem = response?.gem || '';
    const blockedReason = response?.blocked || 'Content blocked by safety filter';

    const cardClass = `aletheia-card ${pos.position}${hardBlock ? ' hard-block' : ''}`;

    let bodyContent;
    if (hardBlock) {
        bodyContent = `
            <div class="aletheia-blocked-message"></div>
        `;
    } else {
        // Use role="region" for expandable sections (supports aria-expanded)
        // Toggle button controls both regions via aria-controls
        bodyContent = `
            <div class="aletheia-gem" id="aletheia-gem-section" role="region" aria-label="Quick summary"></div>
            <div class="aletheia-context" id="aletheia-context-section" role="region" aria-label="Full context"></div>
            <button class="aletheia-toggle" tabindex="0" aria-expanded="false" aria-controls="aletheia-gem-section aletheia-context-section">Show More</button>
        `;
    }

    shadow.innerHTML = `
        <style>${OVERLAY_STYLES}</style>
        <div class="${cardClass}"
             style="top: ${pos.top}px; left: ${pos.left}px;"
             role="dialog"
             aria-label="Aletheia word context">
            <div class="aletheia-header">
                <span class="aletheia-badge ${badgeType}">${badgeIcon}</span>
                <span class="aletheia-signal"></span>
                <button class="aletheia-close" aria-label="Close" tabindex="0">×</button>
            </div>
            ${bodyContent}
        </div>
    `;

    // Set text content safely (XSS prevention)
    const signalEl = shadow.querySelector('.aletheia-signal');
    if (signalEl) signalEl.textContent = signal;

    if (hardBlock) {
        const blockedEl = shadow.querySelector('.aletheia-blocked-message');
        if (blockedEl) blockedEl.textContent = blockedReason;
    } else {
        const gemEl = shadow.querySelector('.aletheia-gem');
        if (gemEl) gemEl.textContent = gem;
    }

    // Attach event listeners
    const closeBtn = shadow.querySelector('.aletheia-close');
    if (closeBtn) {
        closeBtn.addEventListener('click', handleCloseClick);
    }

    if (!hardBlock) {
        const card = shadow.querySelector('.aletheia-card');
        const toggleBtn = shadow.querySelector('.aletheia-toggle');
        const gemEl = shadow.querySelector('.aletheia-gem');

        // Hover behavior for gem
        if (card && gemEl) {
            card.addEventListener('mouseenter', () => handleMouseEnter(shadow));
            card.addEventListener('mouseleave', () => handleMouseLeave(shadow));
        }

        // Toggle button for context
        if (toggleBtn) {
            toggleBtn.addEventListener('click', () => handleToggleClick(shadow));
        }
    }

    // Global keyboard handler
    document.addEventListener('keydown', handleKeydown);

    document.body.appendChild(host);

    // Focus close button for accessibility
    if (closeBtn) {
        closeBtn.focus();
    }
}

// =============================================================================
// EVENT HANDLERS
// =============================================================================

function handleCloseClick() {
    removeOverlay();
    document.removeEventListener('keydown', handleKeydown);
}

function handleMouseEnter(shadow) {
    if (currentOverlayState === OverlayState.HARD_BLOCKED) return;
    if (currentOverlayState === OverlayState.EXPANDED) return;

    const gemEl = shadow.querySelector('.aletheia-gem');
    if (gemEl) {
        gemEl.classList.add('visible');
    }
    currentOverlayState = OverlayState.HOVER;
}

function handleMouseLeave(shadow) {
    if (currentOverlayState === OverlayState.HARD_BLOCKED) return;
    if (currentOverlayState === OverlayState.EXPANDED) return;

    const gemEl = shadow.querySelector('.aletheia-gem');
    if (gemEl) {
        gemEl.classList.remove('visible');
    }
    currentOverlayState = OverlayState.GLANCE;
}

function handleToggleClick(shadow) {
    if (currentOverlayState === OverlayState.HARD_BLOCKED) return;

    const contextEl = shadow.querySelector('.aletheia-context');
    const gemEl = shadow.querySelector('.aletheia-gem');
    const toggleBtn = shadow.querySelector('.aletheia-toggle');

    if (currentOverlayState === OverlayState.EXPANDED) {
        // Collapse
        stopTypewriter();
        if (contextEl) {
            contextEl.classList.remove('expanded');
        }
        if (gemEl) {
            gemEl.classList.remove('visible');
        }
        if (toggleBtn) {
            toggleBtn.textContent = 'Show More';
            updateAriaExpanded(toggleBtn, false);
        }
        currentOverlayState = OverlayState.GLANCE;
    } else {
        // Expand
        if (gemEl) {
            gemEl.classList.add('visible');
        }
        if (contextEl) {
            contextEl.classList.add('expanded');
            // Start typewriter animation
            const contextText = overlayData?.context || '';
            typewriterRender(contextEl, contextText);
        }
        if (toggleBtn) {
            toggleBtn.textContent = 'Show Less';
            updateAriaExpanded(toggleBtn, true);
        }
        currentOverlayState = OverlayState.EXPANDED;
    }
}

function handleKeydown(event) {
    if (event.key === 'Escape') {
        handleCloseClick();
    }
}

// =============================================================================
// LEGACY API COMPATIBILITY
// =============================================================================

// Keep legacy API for backwards compatibility during transition
if (!window.showAletheiaOverlay) {
    window.showAletheiaOverlay = function(message, type, timeout = 4000) {
        // Legacy: simple message overlay
        removeOverlay();

        const pos = calculatePosition();
        if (!pos) return;

        const host = document.createElement('div');
        host.id = 'aletheia-overlay-host';
        const shadow = host.attachShadow({ mode: 'open' });

        const colors = {
            'warning': '#FBBF24',
            'success': '#22C55E',
            'error': '#EF4444'
        };
        const borderColor = colors[type] || colors['warning'];

        shadow.innerHTML = `
            <style>
                .overlay {
                    position: absolute;
                    background: #1F2937;
                    color: #F9FAFB;
                    padding: 8px 12px;
                    border-radius: 6px;
                    font-family: system-ui, sans-serif;
                    font-size: 13px;
                    box-shadow: 0 4px 12px rgba(0,0,0,0.3);
                    z-index: ${OVERLAY_Z_INDEX};
                    border-left: 3px solid ${borderColor};
                    white-space: nowrap;
                    pointer-events: none;
                }
                .overlay::after {
                    content: '';
                    position: absolute;
                    border-style: solid;
                }
                .overlay.below::after {
                    bottom: 100%;
                    left: 20px;
                    border-width: 0 6px 6px 6px;
                    border-color: transparent transparent #1F2937 transparent;
                }
                .overlay.above::after {
                    top: 100%;
                    left: 20px;
                    border-width: 6px 6px 0 6px;
                    border-color: #1F2937 transparent transparent transparent;
                }
            </style>
            <div class="overlay ${pos.position}" style="top:${pos.top}px; left:${pos.left}px"></div>
        `;
        shadow.querySelector('.overlay').textContent = message;

        document.body.appendChild(host);

        host._dismissTimer = setTimeout(() => {
            if (host.isConnected) host.remove();
        }, timeout);
    };
}

if (!window.updateAletheiaOverlay) {
    window.updateAletheiaOverlay = function(message, type, timeout = 4000) {
        const host = document.getElementById('aletheia-overlay-host');
        if (!host || !host.shadowRoot) {
            window.showAletheiaOverlay(message, type, timeout);
            return;
        }

        if (host._dismissTimer) {
            clearTimeout(host._dismissTimer);
        }

        const colors = {
            'warning': '#FBBF24',
            'success': '#22C55E',
            'error': '#EF4444'
        };
        const borderColor = colors[type] || colors['warning'];

        const overlay = host.shadowRoot.querySelector('.overlay');
        if (overlay) {
            overlay.textContent = message;
            overlay.style.borderLeftColor = borderColor;
        }

        host._dismissTimer = setTimeout(() => {
            if (host.isConnected) host.remove();
        }, timeout);
    };
}

// =============================================================================
// NEW MUSEUM LABEL API
// =============================================================================

/**
 * Show loading state.
 */
window.showAletheiaLoading = function() {
    showLoadingOverlay();
};

/**
 * Show etymology result with Museum Label UI.
 * @param {Object} response - Etymology response with signal, gem, context
 * @param {number} httpStatus - HTTP status code (200 or 403)
 */
window.showAletheiaResult = function(response, httpStatus = 200) {
    showResultOverlay(response, httpStatus);
};

/**
 * Hide/remove the overlay.
 */
window.hideAletheiaOverlay = function() {
    removeOverlay();
};
