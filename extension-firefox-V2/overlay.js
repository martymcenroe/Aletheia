// extension-firefox-V2/overlay.js
// MV2 Implementation with Firefox timing fixes

console.log("[Aletheia] overlay.js injected");

// Store reference to shadow (since mode:'closed' hides shadowRoot)
window._aletheiaShadow = window._aletheiaShadow || null;

if (!window.updateAletheiaOverlay) {
    // Update existing overlay in place (no flicker)
    window.updateAletheiaOverlay = function(message, type) {
        console.log("[Aletheia] updateAletheiaOverlay called:", message, type);

        if (!window._aletheiaShadow) {
            console.log("[Aletheia] No existing overlay to update, creating new one");
            window.showAletheiaOverlay(message, type);
            return;
        }

        const colors = {
            'warning': '#FBBF24',
            'success': '#22C55E',
            'error':   '#EF4444'
        };
        const borderColor = colors[type] || colors['warning'];

        const overlay = window._aletheiaShadow.querySelector('.overlay');
        if (overlay) {
            overlay.textContent = message;
            overlay.style.borderLeftColor = borderColor;
            console.log("[Aletheia] Overlay updated in place");
        }
    };
}

if (!window.showAletheiaOverlay) {
    console.log("[Aletheia] Defining showAletheiaOverlay function");

    window.showAletheiaOverlay = function(message, type) {
        console.log("[Aletheia] showAletheiaOverlay called:", message, type);

        // 1. Cleanup existing overlay
        const existing = document.getElementById('aletheia-overlay-host');
        if (existing) {
            console.log("[Aletheia] Removing existing overlay");
            existing.remove();
        }

        // 2. Get Selection Geometry (with fallback for Firefox timing)
        const selection = window.getSelection();
        let rect;

        console.log("[Aletheia] Selection range count:", selection.rangeCount);

        if (selection.rangeCount > 0) {
            rect = selection.getRangeAt(0).getBoundingClientRect();
            console.log("[Aletheia] Got selection rect:", rect.top, rect.left, rect.width, rect.height);

            // Check if rect is valid (not zero-sized)
            if (rect.width === 0 && rect.height === 0) {
                console.log("[Aletheia] Selection rect is zero-sized, using fallback");
                rect = null;
            }
        }

        if (!rect) {
            // Fallback: top-right corner if selection lost (Firefox issue)
            console.log("[Aletheia] Using fallback position (top-right)");
            rect = {
                top: 20,
                bottom: 60,
                left: window.innerWidth - 250,
                right: window.innerWidth - 50,
                width: 200,
                height: 40
            };
        }

        // 3. Create Shadow DOM (Isolation)
        const host = document.createElement('div');
        host.id = 'aletheia-overlay-host';
        const shadow = host.attachShadow({ mode: 'closed' });

        // Store reference for updateAletheiaOverlay
        window._aletheiaShadow = shadow;

        // 4. Constants
        const OVERLAY_HEIGHT = 40;
        const MARGIN_ABOVE = 4;
        const MARGIN_BELOW = 11;

        // Colors
        const colors = {
            'warning': '#FBBF24', // Amber
            'success': '#22C55E', // Green
            'error':   '#EF4444'  // Red
        };
        const borderColor = colors[type] || colors['warning'];

        // 5. Styles
        const style = `
            .overlay {
                position: absolute;
                background: #1F2937;
                color: #F9FAFB;
                padding: 8px 12px;
                border-radius: 6px;
                font-family: system-ui, sans-serif;
                font-size: 13px;
                box-shadow: 0 4px 12px rgba(0,0,0,0.3);
                z-index: 2147483647;
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

        // 6. Viewport Logic (The Flip)
        const spaceBelow = window.innerHeight - rect.bottom;
        const spaceNeeded = OVERLAY_HEIGHT + MARGIN_BELOW;

        let top = 0;
        let className = 'overlay';

        if (spaceBelow < spaceNeeded) {
            // FLIP ABOVE
            top = window.scrollY + rect.top - OVERLAY_HEIGHT - MARGIN_ABOVE;
            className += ' above';
        } else {
            // NORMAL BELOW
            top = window.scrollY + rect.bottom + MARGIN_BELOW;
            className += ' below';
        }

        const left = window.scrollX + rect.left;

        console.log("[Aletheia] Positioning overlay at:", top, left);

        // 7. Render
        shadow.innerHTML = `<style>${style}</style><div class="${className}" style="top:${top}px; left:${left}px"></div>`;
        shadow.querySelector('.overlay').textContent = message;

        document.body.appendChild(host);
        console.log("[Aletheia] Overlay appended to DOM");

        // 8. Auto-Dismiss
        setTimeout(() => {
            if (host.isConnected) {
                console.log("[Aletheia] Auto-dismissing overlay");
                host.remove();
            }
        }, 4000);
    };

    console.log("[Aletheia] showAletheiaOverlay function defined");
} else {
    console.log("[Aletheia] showAletheiaOverlay already exists, skipping definition");
}
