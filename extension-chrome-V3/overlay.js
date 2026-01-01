// extension-chrome-V3/overlay.js
// V3 Implementation

if (!window.updateAletheiaOverlay) {
    // Update existing overlay in place (no flicker)
    window.updateAletheiaOverlay = function(message, type) {
        const host = document.getElementById('aletheia-overlay-host');
        if (!host || !host.shadowRoot) {
            window.showAletheiaOverlay(message, type);
            return;
        }

        const colors = {
            'warning': '#FBBF24',
            'success': '#22C55E',
            'error':   '#EF4444'
        };
        const borderColor = colors[type] || colors['warning'];

        const overlay = host.shadowRoot.querySelector('.overlay');
        if (overlay) {
            overlay.textContent = message;
            overlay.style.borderLeftColor = borderColor;
        }
    };
}

if (!window.showAletheiaOverlay) {

    window.showAletheiaOverlay = function(message, type) {
        // 1. Cleanup existing overlay
        const existing = document.getElementById('aletheia-overlay-host');
        if (existing) existing.remove();

        // 2. Get Selection Geometry
        const selection = window.getSelection();
        if (selection.rangeCount === 0) return;
        const rect = selection.getRangeAt(0).getBoundingClientRect();

        // 3. Create Shadow DOM (mode:'open' so updateAletheiaOverlay can find it)
        const host = document.createElement('div');
        host.id = 'aletheia-overlay-host';
        const shadow = host.attachShadow({ mode: 'open' });

        // 4. Constants (Verified in manual_overlay_math.html)
        const OVERLAY_HEIGHT = 40;
        const MARGIN_ABOVE = 4; // Flush with top of text
        const MARGIN_BELOW = 11; // Flush with bottom of text

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

        // 7. Render
        shadow.innerHTML = `<style>${style}</style><div class="${className}" style="top:${top}px; left:${left}px"></div>`;
        shadow.querySelector('.overlay').textContent = message;

        document.body.appendChild(host);

        // 8. Auto-Dismiss
        setTimeout(() => {
            if (host.isConnected) host.remove();
        }, 4000);
    };
}
