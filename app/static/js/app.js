// Configuration
const API_BASE_URL = window.location.origin;
const API_KEY = localStorage.getItem('xrp_api_key') || promptForApiKey();

let flowChart = null;

// Initialize app
document.addEventListener('DOMContentLoaded', () => {
    initializeTheme();
    initializeEventListeners();
    loadDashboard();

    // Auto-refresh every 30 seconds
    setInterval(loadDashboard, 30000);
});

// Theme Management
function initializeTheme() {
    const savedTheme = localStorage.getItem('theme') || 'light';
    if (savedTheme === 'dark') {
        document.body.classList.add('dark-theme');
    }
}

function toggleTheme() {
    document.body.classList.toggle('dark-theme');
    const theme = document.body.classList.contains('dark-theme') ? 'dark' : 'light';
    localStorage.setItem('theme', theme);

    // Update chart colors
    if (flowChart) {
        loadDashboard();
    }
}

// Event Listeners
function initializeEventListeners() {
    document.getElementById('themeToggle').addEventListener('click', toggleTheme);
    document.getElementById('refreshBtn').addEventListener('click', () => {
        loadDashboard();
        showToast('Dashboard refreshed');
    });
    document.getElementById('createAlertBtn').addEventListener('click', openAlertModal);
    document.getElementById('closeModal').addEventListener('click', closeAlertModal);
    document.getElementById('cancelAlert').addEventListener('click', closeAlertModal);
    document.getElementById('alertForm').addEventListener('submit', handleAlertSubmit);

    // Close modal on outside click
    document.getElementById('alertModal').addEventListener('click', (e) => {
        if (e.target.id === 'alertModal') {
            closeAlertModal();
        }
    });
}

// API Key Management
function promptForApiKey() {
    const apiKey = prompt('Please enter your API key:');
    if (apiKey) {
        localStorage.setItem('xrp_api_key', apiKey);
        return apiKey;
    }
    return '';
}

// API Helper
async function apiCall(endpoint, options = {}) {
    const headers = {
        'X-API-Key': API_KEY,
        'Content-Type': 'application/json',
        ...options.headers
    };

    try {
        const response = await fetch(`${API_BASE_URL}${endpoint}`, {
            ...options,
            headers
        });

        if (response.status === 401 || response.status === 403) {
            localStorage.removeItem('xrp_api_key');
            promptForApiKey();
            throw new Error('Authentication failed. Please refresh the page.');
        }

        if (!response.ok) {
            throw new Error(`API error: ${response.statusText}`);
        }

        return await response.json();
    } catch (error) {
        console.error('API call failed:', error);
        showToast('Failed to fetch data', 'error');
        throw error;
    }
}

// Dashboard Loading
async function loadDashboard() {
    try {
        const data = await apiCall('/dashboard');
        updateStats(data.summary);
        updateChart(data.charts.net_flow);
        updateTransactionsTable(data.transactions);
        updateAlertsList(data.alerts);
    } catch (error) {
        console.error('Failed to load dashboard:', error);
    }
}

// Update Stats
function updateStats(summary) {
    animateValue('totalBalance', summary.total_balance_xrp);
    animateValue('inflow24h', summary.inflow_24h);
    animateValue('outflow24h', summary.outflow_24h);
    document.getElementById('alertCount').textContent = summary.alert_count;
}

function animateValue(elementId, value) {
    const element = document.getElementById(elementId);
    const current = parseFloat(element.textContent) || 0;
    const target = value;
    const duration = 1000;
    const steps = 60;
    const increment = (target - current) / steps;

    let step = 0;
    const timer = setInterval(() => {
        step++;
        const newValue = current + (increment * step);
        element.textContent = formatNumber(newValue);

        if (step >= steps) {
            clearInterval(timer);
            element.textContent = formatNumber(target);
        }
    }, duration / steps);
}

function formatNumber(num) {
    return new Intl.NumberFormat('en-US', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    }).format(num);
}

// Update Chart
function updateChart(chartData) {
    const ctx = document.getElementById('flowChart').getContext('2d');
    const isDark = document.body.classList.contains('dark-theme');

    const labels = chartData.map(point => {
        const date = new Date(point.timestamp);
        return date.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });
    });

    const values = chartData.map(point => point.balance);

    if (flowChart) {
        flowChart.destroy();
    }

    flowChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'Balance Change',
                data: values,
                borderColor: '#667eea',
                backgroundColor: (context) => {
                    const ctx = context.chart.ctx;
                    const gradient = ctx.createLinearGradient(0, 0, 0, 300);
                    gradient.addColorStop(0, 'rgba(102, 126, 234, 0.3)');
                    gradient.addColorStop(1, 'rgba(102, 126, 234, 0.0)');
                    return gradient;
                },
                borderWidth: 3,
                fill: true,
                tension: 0.4,
                pointRadius: 4,
                pointBackgroundColor: '#667eea',
                pointBorderColor: '#fff',
                pointBorderWidth: 2,
                pointHoverRadius: 6
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    backgroundColor: isDark ? '#1a1f2e' : '#ffffff',
                    titleColor: isDark ? '#e4e6eb' : '#212529',
                    bodyColor: isDark ? '#b0b3b8' : '#6c757d',
                    borderColor: isDark ? '#2d3748' : '#dee2e6',
                    borderWidth: 1,
                    padding: 12,
                    displayColors: false,
                    callbacks: {
                        label: function(context) {
                            return `${context.parsed.y > 0 ? '+' : ''}${formatNumber(context.parsed.y)} XRP`;
                        }
                    }
                }
            },
            scales: {
                y: {
                    grid: {
                        color: isDark ? 'rgba(255, 255, 255, 0.05)' : 'rgba(0, 0, 0, 0.05)',
                        drawBorder: false
                    },
                    ticks: {
                        color: isDark ? '#8a8d91' : '#6c757d',
                        callback: function(value) {
                            return value > 0 ? `+${value}` : value;
                        }
                    }
                },
                x: {
                    grid: {
                        display: false,
                        drawBorder: false
                    },
                    ticks: {
                        color: isDark ? '#8a8d91' : '#6c757d',
                        maxRotation: 0
                    }
                }
            },
            interaction: {
                intersect: false,
                mode: 'index'
            }
        }
    });

    // Set chart height
    ctx.canvas.parentNode.style.height = '300px';
}

// Update Transactions Table
function updateTransactionsTable(transactions) {
    const tbody = document.getElementById('transactionsTable');

    if (transactions.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="5" class="empty-state">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
                        <circle cx="12" cy="12" r="10" stroke-width="2"/>
                        <line x1="12" y1="8" x2="12" y2="12" stroke-width="2" stroke-linecap="round"/>
                        <line x1="12" y1="16" x2="12.01" y2="16" stroke-width="2" stroke-linecap="round"/>
                    </svg>
                    <p>No transactions yet</p>
                </td>
            </tr>
        `;
        return;
    }

    tbody.innerHTML = transactions.map(tx => {
        const date = new Date(tx.timestamp);
        const timeStr = date.toLocaleString('en-US', {
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });

        const direction = tx.direction.toLowerCase();
        const counterparty = tx.counterparty
            ? `${tx.counterparty.substring(0, 8)}...${tx.counterparty.substring(tx.counterparty.length - 6)}`
            : 'N/A';
        const hash = `${tx.hash.substring(0, 8)}...${tx.hash.substring(tx.hash.length - 6)}`;

        return `
            <tr>
                <td>${timeStr}</td>
                <td>
                    <span class="direction-badge direction-${direction}">
                        ${direction}
                    </span>
                </td>
                <td style="font-weight: 600; color: ${direction === 'inbound' ? 'var(--success)' : 'var(--danger)'}">
                    ${direction === 'inbound' ? '+' : '-'}${formatNumber(tx.amount_xrp)}
                </td>
                <td class="hash-cell">${counterparty}</td>
                <td class="hash-cell" title="${tx.hash}">${hash}</td>
            </tr>
        `;
    }).join('');
}

// Update Alerts List
function updateAlertsList(alerts) {
    const alertsList = document.getElementById('alertsList');

    if (alerts.length === 0) {
        alertsList.innerHTML = `
            <div class="empty-state">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
                    <path d="M9 12L11 14L15 10M21 12C21 16.9706 16.9706 21 12 21C7.02944 21 3 16.9706 3 12C3 7.02944 7.02944 3 12 3C16.9706 3 21 7.02944 21 12Z" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
                <p>No active alerts</p>
            </div>
        `;
        return;
    }

    alertsList.innerHTML = alerts.map(alert => {
        const date = new Date(alert.created_at);
        const timeStr = date.toLocaleString('en-US', {
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });

        return `
            <div class="alert-item">
                <div class="alert-message">${alert.message}</div>
                <div class="alert-time">${timeStr}</div>
                <div class="alert-actions">
                    <button class="btn-ack" onclick="acknowledgeAlert(${alert.id})">
                        Acknowledge
                    </button>
                </div>
            </div>
        `;
    }).join('');
}

// Alert Management
function openAlertModal() {
    document.getElementById('alertModal').classList.add('active');
}

function closeAlertModal() {
    document.getElementById('alertModal').classList.remove('active');
    document.getElementById('alertForm').reset();
}

async function handleAlertSubmit(e) {
    e.preventDefault();

    const formData = new FormData(e.target);
    const alertRule = {
        name: formData.get('name'),
        min_amount_xrp: formData.get('min_amount_xrp') ? parseFloat(formData.get('min_amount_xrp')) : null,
        direction: formData.get('direction') || null,
        counterparty: formData.get('counterparty') || null,
        memo_keyword: formData.get('memo_keyword') || null
    };

    try {
        await apiCall('/alerts', {
            method: 'POST',
            body: JSON.stringify(alertRule)
        });

        showToast('Alert rule created successfully');
        closeAlertModal();
        loadDashboard();
    } catch (error) {
        showToast('Failed to create alert rule', 'error');
    }
}

async function acknowledgeAlert(alertId) {
    try {
        await apiCall(`/alerts/${alertId}/ack`, {
            method: 'POST'
        });

        showToast('Alert acknowledged');
        loadDashboard();
    } catch (error) {
        showToast('Failed to acknowledge alert', 'error');
    }
}

// Toast Notifications
function showToast(message, type = 'success') {
    // Create toast element
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.textContent = message;

    // Add styles
    Object.assign(toast.style, {
        position: 'fixed',
        top: '20px',
        right: '20px',
        background: type === 'error' ? 'var(--danger)' : 'var(--success)',
        color: 'white',
        padding: '1rem 1.5rem',
        borderRadius: '10px',
        boxShadow: 'var(--shadow-lg)',
        zIndex: '10000',
        animation: 'slideInRight 0.3s ease',
        fontWeight: '500'
    });

    document.body.appendChild(toast);

    // Remove after 3 seconds
    setTimeout(() => {
        toast.style.animation = 'fadeOut 0.3s ease';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// Rotate refresh icon on click
document.getElementById('refreshBtn').addEventListener('click', function() {
    const svg = this.querySelector('svg');
    svg.style.animation = 'spin 0.6s ease';
    setTimeout(() => {
        svg.style.animation = '';
    }, 600);
});
