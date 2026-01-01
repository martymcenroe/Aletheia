// extension/service-worker.js
// MV2 version for Firefox

// [CV-7] CONSTANTS - WIRED TO AWS LAMBDA
const API_ENDPOINT = "https://sqrqfnypgswudwtcheeasq5xri0aryfx.lambda-url.us-east-1.on.aws/";

function extractDomain(url) {
  try {
    return new URL(url).hostname.replace(/^www\./, '');
  } catch {
    return null;
  }
}

// === HELPER FUNCTION (MV2 API) ===
async function showFeedback(tabId, message, type) {
    try {
        // 1. Inject Library
        await browser.tabs.executeScript(tabId, { file: 'overlay.js' });

        // 2. Call Function (MV2 uses code string, not func)
        const code = `window.showAletheiaOverlay(${JSON.stringify(message)}, ${JSON.stringify(type)});`;
        await browser.tabs.executeScript(tabId, { code });

        // 3. Set Toolbar Badge (MV2: browserAction, not action)
        const badgeText = type === 'success' ? '✓' : (type === 'error' ? '✗' : '!');
        const badgeColor = type === 'success' ? '#22C55E' : (type === 'error' ? '#EF4444' : '#FBBF24');

        browser.browserAction.setBadgeText({ tabId, text: badgeText });
        browser.browserAction.setBadgeBackgroundColor({ tabId, color: badgeColor });

        setTimeout(() => browser.browserAction.setBadgeText({ tabId, text: '' }), 3000);

    } catch (e) {
        console.error("Overlay Injection Failed:", e);
    }
}

browser.runtime.onInstalled.addListener(() => {
  browser.contextMenus.create({
    id: "explain-with-ai",
    title: "Explain with AI",
    contexts: ["selection"],
  });
});

browser.contextMenus.onClicked.addListener(async (info, tab) => {
  if (info.menuItemId === "explain-with-ai") {

    // ALLOWLIST GATE
    const domain = extractDomain(info.pageUrl);
    const result = await browser.storage.local.get('allowlist');
    const allowlist = result.allowlist || [];

    if (!allowlist.includes(domain)) {
      console.log(`[Aletheia] Blocked: ${domain}`);
      await showFeedback(tab.id, "Enable Aletheia for this site", "warning");
      return;
    }

    try {
        // MV2: executeScript returns array of results
        const results = await browser.tabs.executeScript(tab.id, {
            code: 'document.body.innerText'
        });

        const fullPageText = results[0];

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
        await showFeedback(tab.id, "Connection Error", "error");
    }
  }
});
