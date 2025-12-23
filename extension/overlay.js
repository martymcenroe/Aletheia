// overlay.js - Selection-anchored feedback overlay
// This function is injected programmatically via chrome.scripting.executeScript()

/**
 * Shows an overlay near the user's text selection
 * @param {string} message - The message to display
 * @param {string} type - One of: 'blocked', 'success', 'error'
 * @param {number} timeout - Auto-dismiss duration in milliseconds
 */
function showOverlay(message, type, timeout) {
  // Get selection position
  const selection = window.getSelection();
  if (!selection.rangeCount) {
    console.warn('[Aletheia] No selection found for overlay positioning');
    return;
  }

  const range = selection.getRangeAt(0);
  const rect = range.getBoundingClientRect();

  // Create host element (light DOM)
  const host = document.createElement('div');
  host.id = 'aletheia-overlay-host';
  host.style.position = 'fixed';
  host.style.left = `${rect.left}px`;
  host.style.top = `${rect.bottom + 8}px`; // 8px gap below selection
  host.style.zIndex = '2147483647'; // Max 32-bit integer
  host.style.pointerEvents = 'none'; // Don't block clicks on underlying content

  // Create Shadow DOM (isolated styling)
  const shadow = host.attachShadow({ mode: 'closed' });

  // Determine border color based on type
  const borderColors = {
    blocked: '#FBBF24',  // amber-400
    success: '#22C55E',  // green-500
    error: '#EF4444'     // red-500
  };
  const borderColor = borderColors[type] || borderColors.error;

  // Determine icon based on type
  const icons = {
    blocked: '⚠',
    success: '✓',
    error: '✗'
  };
  const icon = icons[type] || icons.error;

  // Shadow DOM styles (isolated from host page)
  const styles = `
    .overlay-container {
      /* Explicit font reset - do not rely on inheritance */
      font-family: system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
      font-size: 13px;
      line-height: 1.4;

      /* Layout */
      display: flex;
      align-items: center;
      gap: 8px;

      /* Appearance */
      background: #1F2937;
      color: #F9FAFB;
      padding: 8px 12px;
      border-radius: 6px;
      border-left: 3px solid ${borderColor};
      box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);

      /* Interaction */
      pointer-events: auto;
      cursor: default;

      /* Animation */
      animation: slideIn 0.2s ease-out;
    }

    @keyframes slideIn {
      from {
        opacity: 0;
        transform: translateY(-4px);
      }
      to {
        opacity: 1;
        transform: translateY(0);
      }
    }

    .overlay-icon {
      font-size: 16px;
      line-height: 1;
      color: ${borderColor};
    }

    .overlay-message {
      margin: 0;
      white-space: nowrap;
    }
  `;

  // Build Shadow DOM structure
  shadow.innerHTML = `
    <style>${styles}</style>
    <div class="overlay-container">
      <span class="overlay-icon">${icon}</span>
      <div class="overlay-message"></div>
    </div>
  `;

  // SECURITY: Use textContent to prevent XSS
  const messageEl = shadow.querySelector('.overlay-message');
  messageEl.textContent = message;

  // Append to page
  document.body.appendChild(host);

  // Auto-dismiss after timeout
  setTimeout(() => {
    host.remove();
  }, timeout);
}
