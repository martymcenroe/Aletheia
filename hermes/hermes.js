/**
 * Hermes — Aletheia Admin Dashboard
 * Issue #400
 *
 * Fetches /admin/status and /metrics, renders protection state + business metrics.
 */

const AUTH_API = 'https://sk33bz56yi5qlbrrwzqnprmeuy0xwhzn.lambda-url.us-east-1.on.aws';
const REFRESH_MS = 60 * 1000;   // 1 minute for status
const RETRY_MS = 15 * 1000;     // 15 seconds on error
const JWT_KEY = 'hermes_admin_jwt';

let charts = {};
let refreshTimer = null;

// Mode detection
const params = new URLSearchParams(window.location.search);
const isMockMode = params.get('mock') === 'true';

// ---- Auth ----

function getToken() {
    return localStorage.getItem(JWT_KEY);
}

function setToken(token) {
    localStorage.setItem(JWT_KEY, token);
}

function clearToken() {
    localStorage.removeItem(JWT_KEY);
}

function showAuthGate() {
    document.getElementById('auth-gate').classList.remove('hidden');
}

function hideAuthGate() {
    document.getElementById('auth-gate').classList.add('hidden');
}

document.getElementById('jwt-submit').addEventListener('click', () => {
    const token = document.getElementById('jwt-input').value.trim();
    if (token) {
        setToken(token);
        hideAuthGate();
        loadDashboard();
    }
});

document.getElementById('jwt-input').addEventListener('keydown', (e) => {
    if (e.key === 'Enter') document.getElementById('jwt-submit').click();
});

// ---- Data fetching ----

async function fetchStatus() {
    if (isMockMode) {
        const resp = await fetch('mock-status.json');
        return resp.json();
    }

    const token = getToken();
    if (!token) {
        showAuthGate();
        return null;
    }

    const resp = await fetch(`${AUTH_API}/admin/status`, {
        headers: { 'Authorization': `Bearer ${token}` }
    });

    if (resp.status === 401) {
        clearToken();
        showAuthGate();
        return null;
    }
    if (resp.status === 403) {
        showError('Admin access required. Your JWT must have tier=admin.');
        return null;
    }
    if (!resp.ok) throw new Error(`Status API: ${resp.status}`);
    return resp.json();
}

async function fetchMetrics() {
    if (isMockMode) {
        try {
            const resp = await fetch('../static/admin/mock-metrics.json');
            if (resp.ok) return await resp.json();
        } catch (_ignored) { /* ignore */ }
        return null;
    }

    const token = getToken();
    if (!token) return null;

    try {
        const resp = await fetch(`${AUTH_API}/metrics`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        if (resp.ok) return await resp.json();
    } catch (_ignored) { /* metrics are optional */ }
    return null;
}

// ---- UI helpers ----

function showError(msg) {
    const banner = document.getElementById('error-banner');
    banner.classList.remove('hidden');
    document.getElementById('error-message').textContent = msg;
}

function hideError() {
    document.getElementById('error-banner').classList.add('hidden');
}

function updateStatusBanner(data) {
    const header = document.getElementById('status-header');
    const badge = document.getElementById('overall-status');
    const status = data.overall_status || 'healthy';

    header.className = `status-${status}`;
    badge.textContent = status.toUpperCase();
    badge.className = `status-badge ${status}`;

    // Timestamp
    const ts = data.generated_at || new Date().toISOString();
    document.getElementById('last-updated').textContent = new Date(ts).toLocaleTimeString();

    // Indicators
    if (isMockMode) document.getElementById('mock-indicator').classList.remove('hidden');
    if (data.cached) {
        document.getElementById('cached-indicator').classList.remove('hidden');
    } else {
        document.getElementById('cached-indicator').classList.add('hidden');
    }

    // Issues
    const issues = data.issues || [];
    const issuesBanner = document.getElementById('issues-banner');
    const issuesList = document.getElementById('issues-list');
    issuesList.textContent = '';  // Clear safely
    if (issues.length > 0) {
        for (const issue of issues) {
            const li = document.createElement('li');
            li.textContent = issue;
            issuesList.appendChild(li);
        }
        issuesBanner.classList.remove('hidden');
    } else {
        issuesBanner.classList.add('hidden');
    }
}

// ---- Protection state rendering ----

function renderProtection(protection) {
    // Deny policy
    const denyAttached = protection.deny_policy_attached;
    setIndicator('deny-policy', !denyAttached, denyAttached ? 'ATTACHED' : 'Detached');

    // Kill switch
    const killActive = protection.kill_switch_active;
    setIndicator('kill-switch', !killActive, killActive ? 'ACTIVE' : 'Inactive');

    // Auth
    const authOn = protection.auth_enabled;
    setIndicator('auth', authOn, authOn ? 'Enabled' : 'Disabled');

    // Budget
    const budget = protection.budget || {};
    renderBudget(budget);
}

function setIndicator(id, isOk, label) {
    const icon = document.getElementById(`icon-${id}`);
    const val = document.getElementById(`val-${id}`);

    icon.className = `indicator-icon ${isOk ? 'ok' : 'danger'}`;
    icon.textContent = isOk ? '\u2713' : '\u2717';
    val.textContent = label;
    val.style.color = isOk ? 'var(--green)' : 'var(--red)';
}

function renderBudget(budget) {
    const pct = budget.percent_used || 0;
    const bar = document.getElementById('budget-bar');
    bar.style.width = `${Math.min(pct, 100)}%`;

    if (pct >= 80) bar.style.background = 'var(--red)';
    else if (pct >= 50) bar.style.background = 'var(--amber)';
    else bar.style.background = 'var(--green)';

    document.getElementById('budget-actual').textContent = `$${budget.actual || 0}`;
    document.getElementById('budget-limit').textContent = `/ $${budget.limit || 0}`;
    document.getElementById('budget-forecast').textContent =
        `Forecast: $${budget.forecasted || 0} (${pct}% used)`;
}

// ---- Alarm state rendering ----

function renderAlarms(alarmStates) {
    const grid = document.getElementById('alarms-grid');
    // Clear safely
    while (grid.firstChild) grid.removeChild(grid.firstChild);

    const entries = Object.entries(alarmStates).sort(([, a], [, b]) => {
        const order = { ALARM: 0, INSUFFICIENT_DATA: 1, OK: 2, NOT_FOUND: 3, ERROR: 4 };
        return (order[a] ?? 5) - (order[b] ?? 5);
    });

    for (const [name, state] of entries) {
        const card = document.createElement('div');
        card.className = 'card card-alarm';

        const dotClass = state === 'OK' ? 'ok' : state === 'ALARM' ? 'alarm' : 'unknown';
        const shortName = name
            .replace('AletheiaAgent-', '')
            .replace('Aletheia-', '')
            .replace('AletheiaKillSwitch-', 'KS-');

        const dot = document.createElement('div');
        dot.className = `alarm-dot ${dotClass}`;

        const nameEl = document.createElement('div');
        nameEl.className = 'alarm-name';
        nameEl.title = name;
        nameEl.textContent = shortName;

        const stateEl = document.createElement('div');
        stateEl.className = 'alarm-state';
        const colorVar = dotClass === 'ok' ? '--green' : dotClass === 'alarm' ? '--red' : '--text-muted';
        stateEl.style.color = `var(${colorVar})`;
        stateEl.textContent = state;

        card.appendChild(dot);
        card.appendChild(nameEl);
        card.appendChild(stateEl);
        grid.appendChild(card);
    }
}

// ---- Business metrics charts ----

const chartDefaults = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
        legend: { labels: { color: '#8888aa', font: { size: 11 } } }
    },
    scales: {
        x: { ticks: { color: '#8888aa', font: { size: 10 } }, grid: { color: '#2a2a4a' } },
        y: { ticks: { color: '#8888aa', font: { size: 10 } }, grid: { color: '#2a2a4a' } }
    }
};

function renderMetrics(data) {
    if (!data) return;
    renderAdoption(data);
    renderTiers(data);
    renderRevenue(data);
    renderRetention(data);
}

function renderAdoption(data) {
    if (!data.adoption || !data.adoption.length) return;
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
        options: { ...chartDefaults, plugins: { ...chartDefaults.plugins, legend: { display: false } } }
    });
}

function renderTiers(data) {
    if (!data.tiers) return;
    const ctx = document.getElementById('chart-tiers');
    if (charts.tiers) charts.tiers.destroy();
    charts.tiers = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['Free', 'Subscriber', 'Admin'],
            datasets: [{
                data: [data.tiers.free, data.tiers.subscriber, data.tiers.admin],
                backgroundColor: ['#95a5a6', '#4ecdc4', '#1a1a2e'],
                borderColor: '#2a2a4a'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { labels: { color: '#8888aa' } } }
        }
    });
}

function renderRevenue(data) {
    if (!data.revenue) return;
    const ctx = document.getElementById('chart-revenue');
    if (charts.revenue) charts.revenue.destroy();
    charts.revenue = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: ['Projected Monthly'],
            datasets: [{
                label: 'Revenue ($)',
                data: [data.revenue.projected_monthly],
                backgroundColor: ['#2ecc71'],
                borderRadius: 4
            }]
        },
        options: {
            ...chartDefaults,
            plugins: {
                ...chartDefaults.plugins,
                title: {
                    display: true,
                    text: `$${data.revenue.projected_monthly}/mo (${data.revenue.subscriber_count} subs)`,
                    color: '#e0e0e0'
                }
            }
        }
    });
}

function renderRetention(data) {
    if (!data.retention) return;
    const ctx = document.getElementById('chart-retention');
    if (charts.retention) charts.retention.destroy();
    charts.retention = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['Returning', 'Single Session'],
            datasets: [{
                data: [data.retention.returning_users, data.retention.single_session_users],
                backgroundColor: ['#4ecdc4', '#e74c3c'],
                borderColor: '#2a2a4a'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { labels: { color: '#8888aa' } },
                title: { display: true, text: `${data.retention.retention_rate}% retention`, color: '#e0e0e0' }
            }
        }
    });
}

// ---- Main load ----

async function loadDashboard() {
    try {
        hideError();

        // Fetch status (required) and metrics (optional) in parallel
        const [statusData, metricsData] = await Promise.all([
            fetchStatus(),
            fetchMetrics()
        ]);

        if (!statusData) return;

        updateStatusBanner(statusData);
        renderProtection(statusData.protection);
        renderAlarms(statusData.protection.alarm_states || {});
        renderMetrics(metricsData);

        // Schedule refresh
        if (refreshTimer) clearTimeout(refreshTimer);
        refreshTimer = setTimeout(loadDashboard, REFRESH_MS);

    } catch (err) {
        console.error('Dashboard load failed:', err);
        showError(`Load failed: ${err.message}. Retrying...`);
        if (refreshTimer) clearTimeout(refreshTimer);
        refreshTimer = setTimeout(loadDashboard, RETRY_MS);
    }
}

// ---- Init ----

if (!isMockMode && !getToken()) {
    showAuthGate();
} else {
    loadDashboard();
}
