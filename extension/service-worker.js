// extension/service-worker.js

// [CV-7] CONSTANTS - WIRED TO AWS LAMBDA
const API_ENDPOINT = "https://sqrqfnypgswudwtcheeasq5xri0aryfx.lambda-url.us-east-1.on.aws/";

function extractDomain(url) {
  try {
    return new URL(url).hostname.replace(/^www\./, '');
  } catch {
    return null;
  }
}

// === NEW: HELPER FUNCTION ===
async function showFeedback(tabId, message, type) {
    try {
        // 1. Inject Library (Idempotent)
        await chrome.scripting.executeScript({
            target: { tabId },
            files: ['overlay.js']
        });

        // 2. Wait for script to execute (Firefox timing issue)
        await new Promise(resolve => setTimeout(resolve, 50));

        // 3. Call Function
        await chrome.scripting.executeScript({
            target: { tabId },
            func: (m, t) => window.showAletheiaOverlay(m, t),
            args: [message, type]
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
      // === RESTORED FUNCTIONALITY ===
      await showFeedback(tab.id, "Enable Aletheia for this site", "warning");
      return;
    }

    try {
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

        // === FEEDBACK FOR SUCCESS/ERROR ===
        if (response.ok) {
            await showFeedback(tab.id, "Context Saved", "success");
        } else {
            await showFeedback(tab.id, "Error Saving", "error");
        }

    } catch (error) {
        console.error("[CV-6] Error:", error);
        // === FEEDBACK FOR NETWORK ERROR ===
        await showFeedback(tab.id, "Connection Error", "error");
    }
  }
});