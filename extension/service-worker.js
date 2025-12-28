// [CV-7] CONSTANTS - WIRED TO AWS LAMBDA
const API_ENDPOINT = "https://sqrqfnypgswudwtcheeasq5xri0aryfx.lambda-url.us-east-1.on.aws/";

// Extract domain from URL (strips www. prefix)
function extractDomain(url) {
  try {
    return new URL(url).hostname.replace(/^www\./, '');
  } catch {
    return null;
  }
}

// Badge helper functions
function setBadge(text, color) {
  chrome.action.setBadgeText({ text });
  chrome.action.setBadgeBackgroundColor({ color });
}

function clearBadge() {
  chrome.action.setBadgeText({ text: '' });
}

function flashBadge(text, color, duration) {
  setBadge(text, color);
  setTimeout(clearBadge, duration);
}

// Overlay injection function (gets injected into page context)
// This function must be self-contained (no external dependencies)
function showOverlay(message, type, timeout) {
  const selection = window.getSelection();
  if (!selection.rangeCount) {
    console.warn('[Aletheia] No selection found for overlay positioning');
    return;
  }

  const range = selection.getRangeAt(0);
  const rect = range.getBoundingClientRect();

  const host = document.createElement('div');
  host.id = 'aletheia-overlay-host';
  host.style.position = 'fixed';
  host.style.left = `${rect.left}px`;
  host.style.top = `${rect.bottom + 8}px`;
  host.style.zIndex = '2147483647';
  host.style.pointerEvents = 'none';

  const shadow = host.attachShadow({ mode: 'closed' });

  const borderColors = {
    blocked: '#FBBF24',
    success: '#22C55E',
    error: '#EF4444'
  };
  const borderColor = borderColors[type] || borderColors.error;

  const icons = {
    blocked: '⚠',
    success: '✓',
    error: '✗'
  };
  const icon = icons[type] || icons.error;

  const styles = `
    .overlay-container {
      font-family: system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
      font-size: 13px;
      line-height: 1.4;
      display: flex;
      align-items: center;
      gap: 8px;
      background: #1F2937;
      color: #F9FAFB;
      padding: 8px 12px;
      border-radius: 6px;
      border-left: 3px solid ${borderColor};
      box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
      pointer-events: auto;
      cursor: default;
      animation: slideIn 0.2s ease-out;
    }
    @keyframes slideIn {
      from { opacity: 0; transform: translateY(-4px); }
      to { opacity: 1; transform: translateY(0); }
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

  shadow.innerHTML = `
    <style>${styles}</style>
    <div class="overlay-container">
      <span class="overlay-icon">${icon}</span>
      <div class="overlay-message"></div>
    </div>
  `;

  shadow.querySelector('.overlay-message').textContent = message;
  document.body.appendChild(host);

  setTimeout(() => {
    host.remove();
  }, timeout);
}

// 1. Create the menu item when installed
chrome.runtime.onInstalled.addListener(() => {
  chrome.contextMenus.create({
    id: "explain-with-ai",
    title: "Explain with AI",
    contexts: ["selection"],
  });
});

// 2. Listen for the click
chrome.contextMenus.onClicked.addListener(async (info, tab) => {
  if (info.menuItemId === "explain-with-ai") {
    // ALLOWLIST GATE: Check if domain is allowlisted before processing
    const domain = extractDomain(info.pageUrl);
    const { allowlist = [] } = await chrome.storage.local.get('allowlist');

    if (!allowlist.includes(domain)) {
      console.log(`[Aletheia] Blocked: ${domain} not allowlisted`);

      // Show blocked state feedback
      setBadge('!', '#FBBF24');

      chrome.scripting.executeScript({
        target: { tabId: tab.id },
        func: showOverlay,
        args: ['Enable Aletheia for this domain first', 'blocked', 5000]
      });

      return;
    }

    try {
        // 1. INJECT SCRIPT TO GET FULL CONTEXT
        const injectionResults = await chrome.scripting.executeScript({
            target: { tabId: tab.id },
            func: () => document.body.innerText,
        });

        const fullPageText = injectionResults[0].result;

        // 2. PREPARE PAYLOAD
        const payload = {
            word: info.selectionText,
            url: info.pageUrl,
            title: tab.title,
            context: fullPageText
        };
        
        console.log("[CAV-3] Sending payload to AWS:", payload.word);

        // 3. SEND THE POST REQUEST
        const response = await fetch(API_ENDPOINT, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        console.log("[CV-6] Response status:", response.status);

        // Show success state feedback
        flashBadge('✓', '#22C55E', 3000);

        chrome.scripting.executeScript({
            target: { tabId: tab.id },
            func: showOverlay,
            args: [`Saved: ${info.selectionText}`, 'success', 3000]
        });

    } catch (error) {
        console.error("[CV-6] Error:", error);

        // Show error state feedback
        flashBadge('✗', '#EF4444', 3000);

        chrome.scripting.executeScript({
            target: { tabId: tab.id },
            func: showOverlay,
            args: ['Could not save. Try again.', 'error', 3000]
        });
    }
  }
});
