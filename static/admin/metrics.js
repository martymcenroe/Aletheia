/**
 * Aletheia Business Metrics Dashboard
 * Issue #368, #433
 *
 * Fetches /metrics API (or mock data) and renders 6 Chart.js charts.
 * Issue #433: GitHub OAuth login flow for admin access.
 */
/* exported loginWithGitHub, logout */

const API_BASE = 'https://api.aletheia.study';
const REFRESH_INTERVAL_MS = 5 * 60 * 1000; // 5 minutes
const RETRY_INTERVAL_MS = 30 * 1000; // 30 seconds

let charts = {};
let refreshTimer = null;

// Check for mock mode
const params = new URLSearchParams(window.location.search);
const isMockMode = params.get('mock') === 'true';

// Issue #433: Handle OAuth callback JWT
function handleOAuthCallback() {
    const jwtParam = params.get('jwt');
    if (jwtParam) {
        localStorage.setItem('aletheia_jwt', jwtParam);
        // Strip JWT from URL to avoid leaking in referer/bookmarks
        const url = new URL(window.location);
        url.searchParams.delete('jwt');
        window.history.replaceState({}, '', url.toString());
    }
}

function showLoginScreen() {
    document.getElementById('login-screen').classList.remove('hidden');
    document.getElementById('dashboard').classList.add('hidden');
    document.getElementById('logout-btn').classList.add('hidden');
}

function showDashboard() {
    document.getElementById('login-screen').classList.add('hidden');
    document.getElementById('dashboard').classList.remove('hidden');
    document.getElementById('logout-btn').classList.remove('hidden');
}

function loginWithGitHub() {
    window.location.href = `${API_BASE}/auth/github/authorize`;
}

function logout() {
    localStorage.removeItem('aletheia_jwt');
    if (refreshTimer) clearTimeout(refreshTimer);
    showLoginScreen();
    hideError();
}

function isAuthenticated() {
    return isMockMode || !!localStorage.getItem('aletheia_jwt');
}

async function fetchMetrics() {
    if (isMockMode) {
        const resp = await fetch('mock-metrics.json');
        return resp.json();
    }

    const token = localStorage.getItem('aletheia_jwt');
    if (!token) {
        showLoginScreen();
        return null;
    }

    const resp = await fetch(`${API_BASE}/metrics`, {
        headers: { 'Authorization': `Bearer ${token}` }
    });

    if (resp.status === 401 || resp.status === 403) {
        localStorage.removeItem('aletheia_jwt');
        showLoginScreen();
        showError(resp.status === 401 ? 'Session expired. Please sign in again.' : 'Admin access required.');
        return null;
    }

    if (!resp.ok) {
        throw new Error(`API error: ${resp.status}`);
    }

    return resp.json();
}

function showError(message) {
    document.getElementById('error-banner').classList.remove('hidden');
    document.getElementById('error-message').textContent = message;
}

function hideError() {
    document.getElementById('error-banner').classList.add('hidden');
}

function updateStatus(data) {
    const ts = data.generated_at || new Date().toISOString();
    document.getElementById('last-updated').textContent = `Updated: ${new Date(ts).toLocaleString()}`;

    if (isMockMode) {
        document.getElementById('mock-indicator').classList.remove('hidden');
    }
    if (data.cached) {
        document.getElementById('cached-indicator').classList.remove('hidden');
    } else {
        document.getElementById('cached-indicator').classList.add('hidden');
    }
}

function renderAdoption(data) {
    const ctx = document.getElementById('chart-adoption');
    if (charts.adoption) charts.adoption.destroy();
    charts.adoption = new Chart(ctx, {
        type: 'line',
        data: {
            labels: data.adoption.map(d => d.date),
            datasets: [{
                label: 'New Users',
                data: data.adoption.map(d => d.count),
                borderColor: '#4ecdc4',
                backgroundColor: 'rgba(78, 205, 196, 0.1)',
                fill: true,
                tension: 0.3
            }]
        },
        options: { responsive: true, plugins: { legend: { display: false } } }
    });
}

function renderTiers(data) {
    const ctx = document.getElementById('chart-tiers');
    if (charts.tiers) charts.tiers.destroy();
    charts.tiers = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['Free', 'Subscriber', 'Admin'],
            datasets: [{
                data: [data.tiers.free, data.tiers.subscriber, data.tiers.admin],
                backgroundColor: ['#95a5a6', '#4ecdc4', '#1a1a2e']
            }]
        },
        options: { responsive: true }
    });
}

function renderConversion(data) {
    const ctx = document.getElementById('chart-conversion');
    if (charts.conversion) charts.conversion.destroy();
    charts.conversion = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: ['Converted', 'Free'],
            datasets: [{
                data: [data.conversion.converted_count, data.conversion.eligible_count - data.conversion.converted_count],
                backgroundColor: ['#4ecdc4', '#ddd']
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: { display: false },
                title: { display: true, text: `${data.conversion.rate}% conversion rate` }
            }
        }
    });
}

function renderRevenue(data) {
    const ctx = document.getElementById('chart-revenue');
    if (charts.revenue) charts.revenue.destroy();
    charts.revenue = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: ['Projected Monthly'],
            datasets: [{
                label: 'Revenue ($)',
                data: [data.revenue.projected_monthly],
                backgroundColor: ['#2ecc71']
            }]
        },
        options: {
            responsive: true,
            plugins: {
                title: {
                    display: true,
                    text: `$${data.revenue.projected_monthly}/mo (${data.revenue.subscriber_count} subscribers)`
                }
            },
            scales: { y: { beginAtZero: true } }
        }
    });
}

function renderRetention(data) {
    const ctx = document.getElementById('chart-retention');
    if (charts.retention) charts.retention.destroy();
    charts.retention = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['Returning', 'Single Session'],
            datasets: [{
                data: [data.retention.returning_users, data.retention.single_session_users],
                backgroundColor: ['#4ecdc4', '#e74c3c']
            }]
        },
        options: {
            responsive: true,
            plugins: {
                title: { display: true, text: `${data.retention.retention_rate}% retention` }
            }
        }
    });
}

function renderGeography(data) {
    const ctx = document.getElementById('chart-geography');
    if (charts.geography) charts.geography.destroy();
    const geo = data.geography || {};
    const sorted = Object.entries(geo).sort((a, b) => b[1] - a[1]).slice(0, 10);
    charts.geography = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: sorted.map(([code]) => code),
            datasets: [{
                label: 'Requests',
                data: sorted.map(([, count]) => count),
                backgroundColor: '#1a1a2e'
            }]
        },
        options: {
            responsive: true,
            indexAxis: 'y',
            plugins: { legend: { display: false } }
        }
    });
}

function renderAll(data) {
    renderAdoption(data);
    renderTiers(data);
    renderConversion(data);
    renderRevenue(data);
    renderRetention(data);
    renderGeography(data);
    updateStatus(data);
}

async function loadDashboard() {
    try {
        hideError();
        const data = await fetchMetrics();
        if (data) {
            showDashboard();
            renderAll(data);
            // Schedule next refresh
            if (refreshTimer) clearTimeout(refreshTimer);
            refreshTimer = setTimeout(loadDashboard, REFRESH_INTERVAL_MS);
        }
    } catch (_err) {
        showError('Unable to load metrics. Retrying in 30 seconds...');
        if (refreshTimer) clearTimeout(refreshTimer);
        refreshTimer = setTimeout(loadDashboard, RETRY_INTERVAL_MS);
    }
}

// Initialize
handleOAuthCallback();
if (isAuthenticated()) {
    loadDashboard();
} else {
    showLoginScreen();
}
