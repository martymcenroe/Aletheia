// [CV-6] CONSTANTS
const API_ENDPOINT = "https://webhook.site/1a0e08a8-a013-480f-8e03-ee34930a1d26";

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
    try {
        // 1. INJECT SCRIPT TO GET FULL CONTEXT
        // We use executeScript to grab the text from the DOM directly
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
            context: fullPageText // [Feature #11] New field
        };
        
        console.log("[CAV-3] Sending payload with context size:", fullPageText.length);

        // 3. SEND THE POST REQUEST
        const response = await fetch(API_ENDPOINT, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(payload)
        });

        // 4. LOG RESULT
        console.log("[CV-6] Response received:", response.status);

    } catch (error) {
        console.error("[CV-6] Error capturing context or sending:", error);
    }
  }
});