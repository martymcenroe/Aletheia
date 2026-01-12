// extensions/chrome/overlay.js
// Museum Label UI - Progressive Disclosure (Issue #125)
// See: docs/1125-museum-label-ui.md
// Refactored: Issue #194 - Replaced innerHTML with DOM methods for XSS safety

// =============================================================================
// CONSTANTS
// =============================================================================

const OVERLAY_Z_INDEX = 2147483647; // Max z-index to beat all host content
const TYPEWRITER_DELAY_MS = 15;

// Issue #310: Poetic resonance detection threshold
const POETIC_THRESHOLD = 0.6;

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
// SHADOW DOM STATE (Issue #197 - ADR 0202 Compliance)
// =============================================================================
// Closed Shadow DOM returns null for element.shadowRoot, even to our own code.
// We capture the reference at creation time to maintain internal access.
// See: docs/1197-shadow-dom-hardening.md

let activeShadowRoot = null;

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

/* Signal text (backward compat fallback) */
.aletheia-signal {
    flex: 1;
    font-weight: 600;
    font-size: 14px;
    color: #F9FAFB;
}

/* Issue #295: Score display list */
.aletheia-scores {
    flex: 1;
    display: flex;
    flex-direction: column;
    gap: 2px;
}

.aletheia-score-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-size: 13px;
}

.aletheia-score-category {
    color: #F9FAFB;
    font-weight: 500;
}

.aletheia-score-value {
    color: #9CA3AF;
    font-weight: 600;
    min-width: 40px;
    text-align: right;
}

.aletheia-score-item.warning .aletheia-score-category {
    color: #FBBF24;
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

/* Issue #310: Poetic Resonance Detection Styles */

/* "Explore Deeper Meaning" button */
.aletheia-deep-button {
    display: block;
    width: 100%;
    background: linear-gradient(135deg, #6366F1 0%, #8B5CF6 100%);
    border: none;
    color: #FFFFFF;
    font-size: 13px;
    font-weight: 600;
    padding: 12px 14px;
    cursor: pointer;
    text-align: center;
    transition: opacity 0.15s ease, transform 0.1s ease;
    border-radius: 0 0 8px 8px;
}

.aletheia-deep-button:hover {
    opacity: 0.9;
}

.aletheia-deep-button:active {
    transform: scale(0.98);
}

.aletheia-deep-button:focus {
    outline: 2px solid #A78BFA;
    outline-offset: -2px;
}

.aletheia-deep-button:disabled {
    background: #4B5563;
    cursor: not-allowed;
    opacity: 0.7;
}

.aletheia-deep-button.loading {
    background: #4B5563;
}

/* Poetic analysis section */
.aletheia-poetic-section {
    padding: 12px 14px;
    border-top: 1px solid #4B5563;
    background: #1F2937;
}

.aletheia-poetic-synthesis {
    font-size: 13px;
    line-height: 1.6;
    color: #D1D5DB;
    margin-bottom: 12px;
}

/* Dimension chips */
.aletheia-dimensions {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    margin-bottom: 12px;
}

.aletheia-dimension-chip {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    padding: 4px 10px;
    border-radius: 16px;
    font-size: 12px;
    font-weight: 500;
}

/* Dimension colors (with text labels for accessibility) */
.aletheia-dimension-chip.religious {
    background: #7C3AED;
    color: #FFFFFF;
}

.aletheia-dimension-chip.literary {
    background: #F97316;
    color: #FFFFFF;
}

.aletheia-dimension-chip.architectural {
    background: #22C55E;
    color: #FFFFFF;
}

.aletheia-dimension-chip.artistic {
    background: #3B82F6;
    color: #FFFFFF;
}

.aletheia-dimension-chip.political {
    background: #EF4444;
    color: #FFFFFF;
}

.aletheia-dimension-chip.scientific {
    background: #06B6D4;
    color: #FFFFFF;
}

.aletheia-dimension-chip.novel {
    background: #6B7280;
    color: #FFFFFF;
}

/* Resonance strength indicator */
.aletheia-resonance {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 12px;
    color: #9CA3AF;
}

.aletheia-resonance-bar {
    flex: 1;
    height: 4px;
    background: #374151;
    border-radius: 2px;
    overflow: hidden;
}

.aletheia-resonance-fill {
    height: 100%;
    background: linear-gradient(90deg, #6366F1 0%, #A78BFA 100%);
    border-radius: 2px;
    transition: width 0.3s ease;
}

/* Error state */
.aletheia-poetic-error {
    padding: 12px 14px;
    font-size: 13px;
    color: #FCA5A5;
    text-align: center;
}

.aletheia-retry-button {
    display: inline-block;
    margin-top: 8px;
    background: #374151;
    border: none;
    color: #F9FAFB;
    font-size: 12px;
    padding: 6px 12px;
    border-radius: 4px;
    cursor: pointer;
}

.aletheia-retry-button:hover {
    background: #4B5563;
}
`;

// =============================================================================
// DOM HELPER FUNCTIONS (Issue #194 - XSS-safe element creation)
// =============================================================================

/**
 * Create an element with attributes.
 * @param {string} tag - Element tag name
 * @param {Object} attrs - Attributes to set (className, id, role, aria-*, style, etc.)
 * @param {string} [textContent] - Optional text content (safe - uses textContent)
 * @returns {HTMLElement}
 */
function createElement(tag, attrs = {}, textContent = null) {
    const el = document.createElement(tag);
    for (const [key, value] of Object.entries(attrs)) {
        if (key === 'className') {
            el.className = value;
        } else if (key === 'style' && typeof value === 'object') {
            Object.assign(el.style, value);
        } else if (key.startsWith('data-')) {
            el.dataset[key.slice(5)] = value;
        } else {
            el.setAttribute(key, value);
        }
    }
    if (textContent !== null) {
        el.textContent = textContent;
    }
    return el;
}

/**
 * Create a style element with CSS text.
 * @param {string} cssText - CSS content
 * @returns {HTMLStyleElement}
 */
function createStyleElement(cssText) {
    const style = document.createElement('style');
    style.textContent = cssText;
    return style;
}

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

        // eslint-disable-next-line security/detect-object-injection -- index is internal loop counter, not user input
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

// Security: ADR 0213 - Store direct reference to our overlay host element
// This prevents DOM clobbering attacks where a hostile page creates an element
// with id="aletheia-overlay-host" that could be returned by getElementById
let overlayHostRef = null;

/**
 * Remove existing overlay from DOM.
 * Security: Uses stored reference instead of getElementById to prevent DOM clobbering
 */
function removeOverlay() {
    stopTypewriter();
    // Use stored reference (safe from DOM clobbering)
    if (overlayHostRef && overlayHostRef.isConnected) {
        overlayHostRef.remove();
    }
    overlayHostRef = null;
    activeShadowRoot = null;  // Issue #197: Clear closed shadow reference
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
 * Refactored: Issue #194 - Uses DOM methods instead of innerHTML
 */
function showLoadingOverlay() {
    removeOverlay();

    const pos = calculatePosition();
    if (!pos) return;

    const host = document.createElement('div');
    host.id = 'aletheia-overlay-host';
    const shadow = host.attachShadow({ mode: 'closed' });  // Issue #197: ADR 0202
    activeShadowRoot = shadow;  // Capture reference for internal access

    // Style element (safe - static CSS)
    shadow.appendChild(createStyleElement(OVERLAY_STYLES));

    // Card container
    const card = createElement('div', {
        className: `aletheia-card ${pos.position}`,
        role: 'status',
        'aria-label': 'Aletheia loading'
    });
    card.style.top = `${pos.top}px`;
    card.style.left = `${pos.left}px`;

    // Loading content
    const loading = createElement('div', { className: 'aletheia-loading' });
    const spinner = createElement('div', { className: 'aletheia-spinner' });
    const text = createElement('span', {}, 'Analyzing...');

    loading.appendChild(spinner);
    loading.appendChild(text);
    card.appendChild(loading);
    shadow.appendChild(card);

    document.body.appendChild(host);
    overlayHostRef = host;  // Security: Store reference to prevent DOM clobbering
}

/**
 * Show result overlay with Museum Label UI.
 * Refactored: Issue #194 - Uses DOM methods instead of innerHTML
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
    const shadow = host.attachShadow({ mode: 'closed' });  // Issue #197: ADR 0202
    activeShadowRoot = shadow;  // Capture reference for internal access

    // Style element (safe - static CSS)
    shadow.appendChild(createStyleElement(OVERLAY_STYLES));

    // Extract data (will be set via textContent for XSS safety)
    const signal = response?.signal || 'Analysis';
    const gem = response?.gem || '';
    const blockedReason = response?.blocked || 'Content blocked by safety filter';

    // Card container
    const cardClass = `aletheia-card ${pos.position}${hardBlock ? ' hard-block' : ''}`;
    const card = createElement('div', {
        className: cardClass,
        role: 'dialog',
        'aria-label': 'Aletheia word context'
    });
    card.style.top = `${pos.top}px`;
    card.style.left = `${pos.left}px`;

    // Header
    const header = createElement('div', { className: 'aletheia-header' });

    const badge = createElement('span', { className: `aletheia-badge ${badgeType}` }, badgeIcon);

    // Issue #295: Render scores_display if available, otherwise fall back to signal
    const scoresDisplay = response?.scores_display;
    let headerContent;

    if (scoresDisplay && Array.isArray(scoresDisplay) && scoresDisplay.length > 0) {
        // New: Render score breakdown
        headerContent = createElement('div', { className: 'aletheia-scores' });
        for (const item of scoresDisplay) {
            const scoreItem = createElement('div', {
                className: item.category === 'Provocative' ? 'aletheia-score-item warning' : 'aletheia-score-item'
            });
            const categorySpan = createElement('span', { className: 'aletheia-score-category' });
            categorySpan.textContent = item.category;
            const valueSpan = createElement('span', { className: 'aletheia-score-value' });
            valueSpan.textContent = `${item.score}%`;
            scoreItem.appendChild(categorySpan);
            scoreItem.appendChild(valueSpan);
            headerContent.appendChild(scoreItem);
        }
    } else {
        // Backward compat: Fall back to signal text
        headerContent = createElement('span', { className: 'aletheia-signal' });
        // XSS-safe: signal text set via textContent
        headerContent.textContent = signal;
    }

    const closeBtn = createElement('button', {
        className: 'aletheia-close',
        'aria-label': 'Close',
        tabindex: '0'
    }, '×');

    header.appendChild(badge);
    header.appendChild(headerContent);
    header.appendChild(closeBtn);
    card.appendChild(header);

    // Body content
    if (hardBlock) {
        const blockedEl = createElement('div', { className: 'aletheia-blocked-message' });
        // XSS-safe: blocked reason set via textContent
        blockedEl.textContent = blockedReason;
        card.appendChild(blockedEl);
    } else {
        // Gem section
        const gemEl = createElement('div', {
            className: 'aletheia-gem',
            id: 'aletheia-gem-section',
            role: 'region',
            'aria-label': 'Quick summary'
        });
        // XSS-safe: gem text set via textContent
        gemEl.textContent = gem;

        // Context section
        const contextEl = createElement('div', {
            className: 'aletheia-context',
            id: 'aletheia-context-section',
            role: 'region',
            'aria-label': 'Full context',
            'aria-expanded': 'false'
        });

        // Toggle button
        const toggleBtn = createElement('button', {
            className: 'aletheia-toggle',
            tabindex: '0',
            'aria-expanded': 'false',
            'aria-controls': 'aletheia-gem-section aletheia-context-section'
        }, 'Show More');

        card.appendChild(gemEl);
        card.appendChild(contextEl);
        card.appendChild(toggleBtn);

        // Issue #310: "Explore Deeper Meaning" button for poetic resonance
        const poeticPotential = response?.poetic_potential || 0;
        const potentialDimensions = response?.potential_dimensions || [];

        // Store for later use in deep analysis
        overlayData.poetic_potential = poeticPotential;
        overlayData.potential_dimensions = potentialDimensions;

        if (poeticPotential >= POETIC_THRESHOLD) {
            const deepButton = createElement('button', {
                className: 'aletheia-deep-button',
                'aria-label': 'Explore deeper meaning of this word'
            }, 'Explore Deeper Meaning');
            card.appendChild(deepButton);
        }
    }

    shadow.appendChild(card);

    // Attach event listeners
    closeBtn.addEventListener('click', handleCloseClick);

    if (!hardBlock) {
        const gemEl = shadow.querySelector('.aletheia-gem');
        const toggleBtn = shadow.querySelector('.aletheia-toggle');

        // Hover behavior for gem
        if (gemEl) {
            card.addEventListener('mouseenter', () => handleMouseEnter(shadow));
            card.addEventListener('mouseleave', () => handleMouseLeave(shadow));
        }

        // Toggle button for context
        if (toggleBtn) {
            toggleBtn.addEventListener('click', () => handleToggleClick(shadow));
        }

        // Issue #310: Deep analysis button
        const deepButton = shadow.querySelector('.aletheia-deep-button');
        if (deepButton) {
            deepButton.addEventListener('click', () => handleDeepAnalysisClick(shadow, card));
        }
    }

    // Global keyboard handler
    document.addEventListener('keydown', handleKeydown);

    document.body.appendChild(host);
    overlayHostRef = host;  // Security: Store reference to prevent DOM clobbering

    // Focus close button for accessibility
    closeBtn.focus();
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

/**
 * Issue #310: Handle "Explore Deeper Meaning" button click.
 * Sends request to Lambda for Opus analysis and displays results.
 */
async function handleDeepAnalysisClick(shadow, card) {
    const deepButton = shadow.querySelector('.aletheia-deep-button');
    if (!deepButton) return;

    // Show loading state
    deepButton.disabled = true;
    deepButton.classList.add('loading');
    deepButton.textContent = 'Analyzing...';

    try {
        // Build payload for deep analysis
        const payload = {
            action: 'deep_poetic_analysis',
            text: overlayData?.selectedText || '',
            etymology: {
                signal: overlayData?.signal || '',
                gem: overlayData?.gem || '',
                context: overlayData?.context || ''
            },
            domContext: overlayData?.domContext || '',
            dimensions: overlayData?.potential_dimensions || []
        };

        // Send request via chrome.runtime.sendMessage to service worker
        const result = await new Promise((resolve, reject) => {
            chrome.runtime.sendMessage(
                { type: 'DEEP_POETIC_ANALYSIS', payload },
                (response) => {
                    if (chrome.runtime.lastError) {
                        reject(new Error(chrome.runtime.lastError.message));
                    } else {
                        resolve(response);
                    }
                }
            );
        });

        if (result?.status === 'success') {
            // Render poetic analysis results
            renderPoeticAnalysis(shadow, card, result);
        } else {
            // Show error state
            renderPoeticError(shadow, card, result?.error || 'Analysis failed');
        }

    } catch (error) {
        console.error('[Aletheia] Deep analysis error:', error);
        renderPoeticError(shadow, card, error.message || 'Analysis unavailable');
    }
}

/**
 * Issue #310: Render poetic analysis results.
 */
function renderPoeticAnalysis(shadow, card, result) {
    // Remove the button
    const deepButton = shadow.querySelector('.aletheia-deep-button');
    if (deepButton) {
        deepButton.remove();
    }

    // Create poetic section
    const poeticSection = createElement('div', { className: 'aletheia-poetic-section' });

    // Synthesis paragraph
    const synthesisEl = createElement('p', { className: 'aletheia-poetic-synthesis' });
    synthesisEl.textContent = result.synthesis || '';
    poeticSection.appendChild(synthesisEl);

    // Dimension chips
    if (result.dimensions && result.dimensions.length > 0) {
        const dimensionsContainer = createElement('div', { className: 'aletheia-dimensions' });
        for (const dim of result.dimensions) {
            const dimName = dim.dimension || 'unknown';
            // Handle novel dimensions (novel:description format)
            const isNovel = dimName.startsWith('novel:');
            const chipClass = isNovel ? 'novel' : dimName.toLowerCase();
            const displayName = isNovel ? dimName.substring(6) : dimName;

            const chip = createElement('span', {
                className: `aletheia-dimension-chip ${chipClass}`,
                title: dim.explanation || ''
            }, displayName);
            dimensionsContainer.appendChild(chip);
        }
        poeticSection.appendChild(dimensionsContainer);
    }

    // Resonance strength indicator
    const resonanceStrength = result.resonance_strength || 0;
    const resonanceEl = createElement('div', { className: 'aletheia-resonance' });

    const resonanceLabel = createElement('span', {}, 'Resonance');
    const resonanceBar = createElement('div', { className: 'aletheia-resonance-bar' });
    const resonanceFill = createElement('div', { className: 'aletheia-resonance-fill' });
    resonanceFill.style.width = `${Math.round(resonanceStrength * 100)}%`;
    resonanceBar.appendChild(resonanceFill);

    const resonanceValue = createElement('span', {}, `${Math.round(resonanceStrength * 100)}%`);

    resonanceEl.appendChild(resonanceLabel);
    resonanceEl.appendChild(resonanceBar);
    resonanceEl.appendChild(resonanceValue);
    poeticSection.appendChild(resonanceEl);

    card.appendChild(poeticSection);
}

/**
 * Issue #310: Render error state with retry button.
 */
function renderPoeticError(shadow, card, errorMessage) {
    // Remove the button
    const deepButton = shadow.querySelector('.aletheia-deep-button');
    if (deepButton) {
        deepButton.remove();
    }

    // Create error section
    const errorSection = createElement('div', { className: 'aletheia-poetic-error' });

    const errorText = createElement('span', {}, errorMessage || 'Analysis unavailable');
    errorSection.appendChild(errorText);

    // Retry button
    const retryButton = createElement('button', {
        className: 'aletheia-retry-button',
        'aria-label': 'Retry analysis'
    }, 'Retry');

    retryButton.addEventListener('click', () => {
        // Remove error section
        errorSection.remove();

        // Re-add the deep button
        const newDeepButton = createElement('button', {
            className: 'aletheia-deep-button',
            'aria-label': 'Explore deeper meaning of this word'
        }, 'Explore Deeper Meaning');
        newDeepButton.addEventListener('click', () => handleDeepAnalysisClick(shadow, card));
        card.appendChild(newDeepButton);
    });

    errorSection.appendChild(retryButton);
    card.appendChild(errorSection);
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
            updateAriaExpanded(contextEl, false);
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
            updateAriaExpanded(contextEl, true);
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
// Refactored: Issue #194 - Uses DOM methods instead of innerHTML
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
        const shadow = host.attachShadow({ mode: 'closed' });  // Issue #197: ADR 0202
        activeShadowRoot = shadow;  // Capture reference for internal access

        const colors = {
            'warning': '#FBBF24',
            'success': '#22C55E',
            'error': '#EF4444'
        };
        // eslint-disable-next-line security/detect-object-injection -- type is internal enum ('warning'|'success'|'error'), not user input
        const borderColor = colors[type] || colors['warning'];

        // Legacy overlay styles (inline for this simple overlay)
        const legacyStyles = `
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
        `;

        // Style element (safe - static CSS with interpolated color)
        shadow.appendChild(createStyleElement(legacyStyles));

        // Overlay div
        const overlay = createElement('div', {
            className: `overlay ${pos.position}`
        });
        overlay.style.top = `${pos.top}px`;
        overlay.style.left = `${pos.left}px`;
        // XSS-safe: message set via textContent
        overlay.textContent = message;

        shadow.appendChild(overlay);
        document.body.appendChild(host);
        overlayHostRef = host;  // Security: Store reference to prevent DOM clobbering

        host._dismissTimer = setTimeout(() => {
            if (host.isConnected) host.remove();
            if (overlayHostRef === host) overlayHostRef = null;
        }, timeout);
    };
}

if (!window.updateAletheiaOverlay) {
    window.updateAletheiaOverlay = function(message, type, timeout = 4000) {
        // Security: Use stored reference instead of getElementById to prevent DOM clobbering
        const host = overlayHostRef;
        // Issue #197: Use activeShadowRoot (closed mode returns null for host.shadowRoot)
        if (!host || !host.isConnected || !activeShadowRoot) {
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
        // eslint-disable-next-line security/detect-object-injection -- type is internal enum ('warning'|'success'|'error'), not user input
        const borderColor = colors[type] || colors['warning'];

        const overlay = activeShadowRoot.querySelector('.overlay');  // Issue #197: Use stored reference
        if (overlay) {
            // XSS-safe: message set via textContent
            overlay.textContent = message;
            overlay.style.borderLeftColor = borderColor;
        }

        host._dismissTimer = setTimeout(() => {
            if (host.isConnected) host.remove();
            if (overlayHostRef === host) overlayHostRef = null;
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
