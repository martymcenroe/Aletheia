// [CV-6] CONSTANTS
const API_ENDPOINT = "https://webhook.site/1a0e08a8-a013-480f-8e03-ee34930a1d26";
const LINKEDIN_COOKIE_DOMAIN = ".linkedin.com";

// Check whether the user appears to be logged into LinkedIn
function isLinkedInAuthenticated() {
  return new Promise((resolve) => {
    chrome.cookies.getAll({ domain: LINKEDIN_COOKIE_DOMAIN }, (cookies) => {
      if (chrome.runtime.lastError) {
        console.error("[CV-6] Error checking LinkedIn cookies:", chrome.runtime.lastError);
        resolve(false);
        return;
      }

      const hasCookies = Array.isArray(cookies) && cookies.length > 0;
      resolve(hasCookies);
    });
  });
}

// User-visible failure message when LinkedIn auth is missing
function showNotAuthenticatedMessage() {
  const message = "Not authenticated with LinkedIn.";

  if (chrome.notifications && chrome.notifications.create) {
    chrome.notifications.create({
      type: "basic",
      iconUrl: "icon128.png", // adjust if your icon filename is different
      title: "Explain with AI",
      message,
    });
  } else {
    console.warn("[CV-6]", message);
  }
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
  if (info.menuItemId !== "explain-with-ai") return;

  // 0. Require LinkedIn authentication
  const authenticated = await isLinkedInAuthenticated();
  if (!authenticated) {
    console.log("[CV-6] LinkedIn not authenticated – aborting request.");
    showNotAuthenticatedMessage();
    return;
  }

  try {
    // 1. INJECT SCRIPT TO GET FULL CONTEXT
    const injectionResults = await chrome.scripting.executeScript({
      target: { tabId: tab.id },
      func: () => document.body.innerText,
    });

    // The result is an array of objects; we want the first one
    const fullPageText = injectionResults[0].result;

    // 2. PREPARE PAYLOAD
    const payload = {
      word: info.selectionText,
      url: info.pageUrl,
      title: tab.title,
      context: fullPageText, // [Feature #11] New field
    };

    console.log("[CV-6] Sending payload with context size:", fullPageText.length);

    // 3. SEND THE POST REQUEST
    const response = await fetch(API_ENDPOINT, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    });

    // 4. LOG RESULT
    console.log("[CV-6] Response received:", response.status);
  } catch (error) {
    console.error("[CV-6] Error capturing context or sending:", error);
  }
});
