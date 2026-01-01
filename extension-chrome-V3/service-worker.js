// extension-chrome-V3/service-worker.js
// Chrome Manifest V3 version

// [CV-7] CONSTANTS - WIRED TO AWS LAMBDA
const API_ENDPOINT = "https://sqrqfnypgswudwtcheeasq5xri0aryfx.lambda-url.us-east-1.on.aws/";

function extractDomain(url) {
  try {
    return new URL(url).hostname.replace(/^www\./, '');
  } catch {
    return null;
  }
}

// === HELPER FUNCTION ===
async function showFeedback(tabId, message, type) {
    try {
        // 1. Inject Library (Idempotent)
        await chrome.scripting.executeScript({
            target: { tabId },
            files: ['overlay.js'],
            world: 'MAIN'
        });

        // 2. Call Function
        await chrome.scripting.executeScript({
            target: { tabId },
            func: (m, t) => window.showAletheiaOverlay(m, t),
            args: [message, type],
            world: 'MAIN'
        });

        // 3. Set Toolbar Badge
        const badgeText = type === 'success' ? '✓' : (type === 'error' ? '✗' : '!');
        const badgeColor = type === 'success' ? '#22C55E' : (type === 'error' ? '#EF4444' : '#FBBF24');

        chrome.action.setBadgeText({ tabId, text: badgeText });
        chrome.action.setBadgeBackgroundColor({ tabId, color: badgeColor });

        setTimeout(() => chrome.action.setBadgeText({ tabId, text: '' }), 3000);

    } catch (e) {
        console.error("Overlay Injection Failed:", e);
    }
}

chrome.runtime.onInstalled.addListener(() => {
  chrome.contextMenus.create({
    id: "explain-with-ai",
    title: "Explain with AI",
    contexts: ["selection"],
  });
});

chrome.contextMenus.onClicked.addListener(async (info, tab) => {
  if (info.menuItemId === "explain-with-ai") {

    // ALLOWLIST GATE
    const domain = extractDomain(info.pageUrl);
    const { allowlist = [] } = await chrome.storage.local.get('allowlist');

    if (!allowlist.includes(domain)) {
      console.log(`[Aletheia] Blocked: ${domain}`);
      await showFeedback(tab.id, "Enable Aletheia for this site", "warning");
      return;
    }

    try {
        // IMMEDIATE FEEDBACK - show "Saving..." right away
        console.log("[Aletheia] Showing immediate 'Saving...' feedback");
        await chrome.scripting.executeScript({
            target: { tabId: tab.id },
            files: ['overlay.js'],
            world: 'MAIN'
        });
        await chrome.scripting.executeScript({
            target: { tabId: tab.id },
            func: () => window.showAletheiaOverlay("Saving...", "warning"),
            world: 'MAIN'
        });

        const injectionResults = await chrome.scripting.executeScript({
            target: { tabId: tab.id },
            func: () => document.body.innerText,
        });

        const fullPageText = injectionResults[0].result;

        const payload = {
            text: info.selectionText,
            url: info.pageUrl,
            title: tab.title,
            domContext: fullPageText
        };

        console.log("[CAV-3] Sending payload to AWS:", payload.text);

        const response = await fetch(API_ENDPOINT, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        // === UPDATE OVERLAY IN PLACE (no flicker) ===
        if (response.ok) {
            await chrome.scripting.executeScript({
                target: { tabId: tab.id },
                func: () => window.updateAletheiaOverlay("Context Saved", "success"),
                world: 'MAIN'
            });
        } else {
            await chrome.scripting.executeScript({
                target: { tabId: tab.id },
                func: () => window.updateAletheiaOverlay("Error Saving", "error"),
                world: 'MAIN'
            });
        }

        // Set badge
        const badgeText = response.ok ? '✓' : '✗';
        const badgeColor = response.ok ? '#22C55E' : '#EF4444';
        chrome.action.setBadgeText({ tabId: tab.id, text: badgeText });
        chrome.action.setBadgeBackgroundColor({ tabId: tab.id, color: badgeColor });
        setTimeout(() => chrome.action.setBadgeText({ tabId: tab.id, text: '' }), 3000);

    } catch (error) {
        console.error("[CV-6] Error:", error);
        await chrome.scripting.executeScript({
            target: { tabId: tab.id },
            func: () => window.updateAletheiaOverlay("Connection Error", "error"),
            world: 'MAIN'
        });
        chrome.action.setBadgeText({ tabId: tab.id, text: '✗' });
        chrome.action.setBadgeBackgroundColor({ tabId: tab.id, color: '#EF4444' });
        setTimeout(() => chrome.action.setBadgeText({ tabId: tab.id, text: '' }), 3000);
    }
  }
});
