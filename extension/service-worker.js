// [CV-7] CONSTANTS - WIRED TO AWS LAMBDA
const API_ENDPOINT = "https://i2moviunzmb4v3srunkklleyg40xsfdg.lambda-url.us-east-1.on.aws/";

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

    } catch (error) {
        console.error("[CV-6] Error:", error);
    }
  }
});
