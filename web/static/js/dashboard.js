// SolBot Dashboard JavaScript

const API_BASE_URL = window.location.origin;
let socket = null;
let reconnectAttempts = 0;
const MAX_RECONNECT_ATTEMPTS = 5;
let reconnectTimeout = null;

// Chart instances
let priceChart = null;
let equityChart = null;
let drawdownChart = null;
let solTVChart = null;
let btcTVChart = null;

// Initialize on DOM ready
document.addEventListener('DOMContentLoaded', () => {
    initializeWebSocket();
    initializeEventListeners();
    loadProfiles();
    fetchStatus(); // Initial load via HTTP
});

// ==================== WebSocket Management ====================

function initializeWebSocket() {
    try {
        socket = io(API_BASE_URL, {
            transports: ['websocket', 'polling'],
            reconnection: true,
            reconnectionDelay: 1000,
            reconnectionDelayMax: 5000,
            reconnectionAttempts: MAX_RECONNECT_ATTEMPTS
        });

        socket.on('connect', () => {
            console.log('WebSocket connected');
            updateConnectionStatus('connected');
            reconnectAttempts = 0;
            if (reconnectTimeout) {
                clearTimeout(reconnectTimeout);
                reconnectTimeout = null;
            }
        });

        socket.on('disconnect', () => {
            console.log('WebSocket disconnected');
            updateConnectionStatus('disconnected');
            attemptReconnect();
        });

        socket.on('connect_error', (error) => {
            console.error('WebSocket connection error:', error);
            updateConnectionStatus('disconnected');
        });

        socket.on('status_update', (data) => {
            console.log('Status update received');
            updateDisplay(data);
        });

        socket.on('log_update', (data) => {
            console.log('Log update received');
            appendLog(data.message);
        });
    } catch (error) {
        console.error('Failed to initialize WebSocket:', error);
        updateConnectionStatus('disconnected');
    }
}

function attemptReconnect() {
    if (reconnectAttempts < MAX_RECONNECT_ATTEMPTS) {
        reconnectAttempts++;
        const delay = Math.min(1000 * Math.pow(2, reconnectAttempts), 30000);
        updateConnectionStatus('connecting');
        reconnectTimeout = setTimeout(() => {
            if (socket && !socket.connected) {
                socket.connect();
            }
        }, delay);
    } else {
        showMessage('WebSocket connection failed. Using HTTP polling fallback.', 'error');
        // Fallback to HTTP polling
        startPolling();
    }
}

function updateConnectionStatus(status) {
    const indicator = document.getElementById('connection-indicator');
    if (indicator) {
        indicator.className = `status-badge ${status}`;
        indicator.textContent = status.charAt(0).toUpperCase() + status.slice(1);
    }
}

function startPolling() {
    // Fallback polling if WebSocket fails
    if (window.pollInterval) {
        clearInterval(window.pollInterval);
    }
    window.pollInterval = setInterval(() => {
        fetchStatus();
    }, 5000);
}

// ==================== API Functions ====================

async function fetchStatus() {
    try {
        const response = await fetch(`${API_BASE_URL}/get_status`);
        if (response.ok) {
            const data = await response.json();
            updateDisplay(data);
        } else {
            console.error('Failed to fetch status:', response.statusText);
        }
    } catch (error) {
        console.error('Error fetching status:', error);
    }
}

async function loadProfiles() {
    try {
        const response = await fetch(`${API_BASE_URL}/profiles`);
        if (response.ok) {
            const profiles = await response.json();
            populateProfileSelect(profiles);
        }
    } catch (error) {
        console.error('Error loading profiles:', error);
    }
}

async function saveProfile(profileData) {
    try {
        const response = await fetch(`${API_BASE_URL}/save_profile`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(profileData)
        });
        
        if (response.ok) {
            showMessage('Profile saved successfully!', 'success');
            loadProfiles();
            document.getElementById('profile-form').reset();
        } else {
            const error = await response.json();
            showMessage(`Failed to save profile: ${error.error || response.statusText}`, 'error');
        }
    } catch (error) {
        showMessage(`Error saving profile: ${error.message}`, 'error');
    }
}

async function applyProfile(profileName) {
    try {
        const response = await fetch(`${API_BASE_URL}/apply_profile`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ name: profileName })
        });
        
        if (response.ok) {
            showMessage('Profile applied successfully!', 'success');
        } else {
            const error = await response.json();
            showMessage(`Failed to apply profile: ${error.error || response.statusText}`, 'error');
        }
    } catch (error) {
        showMessage(`Error applying profile: ${error.message}`, 'error');
    }
}

async function startSimulation(initialUsdt, initialSol) {
    try {
        const response = await fetch(`${API_BASE_URL}/start_simulation`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                initial_usdt: initialUsdt,
                initial_sol: initialSol
            })
        });
        
        if (response.ok) {
            showMessage('Simulation started!', 'success');
        } else {
            const error = await response.json();
            showMessage(`Failed to start simulation: ${error.error || response.statusText}`, 'error');
        }
    } catch (error) {
        showMessage(`Error starting simulation: ${error.message}`, 'error');
    }
}

async function startLive() {
    try {
        const response = await fetch(`${API_BASE_URL}/start_live`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        if (response.ok) {
            showMessage('Live trading started!', 'success');
        } else {
            const error = await response.json();
            showMessage(`Failed to start live trading: ${error.error || response.statusText}`, 'error');
        }
    } catch (error) {
        showMessage(`Error starting live trading: ${error.message}`, 'error');
    }
}

async function stopBot() {
    try {
        const response = await fetch(`${API_BASE_URL}/stop`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        if (response.ok) {
            showMessage('Bot stopped!', 'info');
        } else {
            const error = await response.json();
            showMessage(`Failed to stop: ${error.error || response.statusText}`, 'error');
        }
    } catch (error) {
        showMessage(`Error stopping bot: ${error.message}`, 'error');
    }
}

// ==================== Display Updates ====================

function updateDisplay(statusData) {
    updateStatusDisplay(statusData);
    updateBalanceDisplay(statusData.balance || {});
    updateIndicatorsDisplay(statusData.indicators || {});
    updateLogsDisplay(statusData.logs || []);
    updateCharts(statusData);
}

function updateStatusDisplay(status) {
    const display = document.getElementById('status-display');
    if (display) {
        const running = status.running || false;
        const mode = status.mode || 'None';
        display.textContent = `Running: ${running}\nMode: ${mode}`;
    }
}

function updateBalanceDisplay(balance) {
    const display = document.getElementById('balance-display');
    if (display) {
        const usdt = balance.usdt || 0;
        const sol = balance.sol || 0;
        const solPrice = balance.sol_price || 0;
        display.textContent = `USDT: ${formatNumber(usdt, 2)}\nSOL: ${formatNumber(sol, 4)}\nSOL Price: ${formatNumber(solPrice, 2)}`;
    }
}

function updateIndicatorsDisplay(indicators) {
    updateBTCIndicators(indicators.btc || {});
    updateSOLIndicators(indicators.sol || {});
}

function updateBTCIndicators(indicators) {
    const display = document.getElementById('btc-indicators-display');
    if (display) {
        if (Object.keys(indicators).length === 0) {
            display.textContent = 'BTC indicators loading or not available yet.';
        } else {
            display.textContent = formatIndicators(indicators);
        }
    }
}

function updateSOLIndicators(indicators) {
    const display = document.getElementById('sol-indicators-display');
    if (display) {
        if (Object.keys(indicators).length === 0) {
            display.textContent = 'SOL indicators loading or not available yet.';
        } else {
            display.textContent = formatIndicators(indicators);
        }
    }
}

function formatIndicators(indicators) {
    const lines = [];
    for (const [key, value] of Object.entries(indicators)) {
        if (Array.isArray(value)) {
            const formatted = value.map(v => typeof v === 'number' ? formatNumber(v, 4) : String(v)).join(', ');
            lines.push(`${key}: ${formatted}`);
        } else if (typeof value === 'number') {
            lines.push(`${key}: ${formatNumber(value, 4)}`);
        } else {
            lines.push(`${key}: ${value}`);
        }
    }
    return lines.join('\n');
}

function updateLogsDisplay(logs) {
    const display = document.getElementById('logs-display');
    if (display) {
        if (logs.length === 0) {
            display.textContent = 'No logs yet. Start simulation to generate data.';
        } else {
            const recentLogs = logs.slice(-20);
            const formatted = recentLogs.map(log => `• ${log.replace(/\n/g, ' | ')}`).join('\n');
            display.textContent = formatted;
        }
    }
}

function appendLog(message) {
    const display = document.getElementById('logs-display');
    if (display) {
        const currentText = display.textContent;
        const newText = currentText === 'No logs yet. Start simulation to generate data.' 
            ? `• ${message.replace(/\n/g, ' | ')}`
            : `${currentText}\n• ${message.replace(/\n/g, ' | ')}`;
        display.textContent = newText;
        
        // Scroll to bottom
        display.scrollTop = display.scrollHeight;
        
        // Keep only last 20 logs
        const lines = newText.split('\n');
        if (lines.length > 20) {
            display.textContent = lines.slice(-20).join('\n');
        }
    }
}

// ==================== Charts ====================

function updateCharts(statusData) {
    updatePriceChart(statusData.price_history || []);
    updateEquityChart(statusData.equity_history || []);
    updateDrawdownChart(statusData.drawdown_history || []);
    updateTradingViewCharts(statusData);
}

function updatePriceChart(priceHistory) {
    const container = document.getElementById('price-chart');
    if (!container) return;
    
    if (priceHistory.length === 0) {
        container.innerHTML = '<p>Price history not available yet.</p>';
        return;
    }
    
    const data = [{
        x: priceHistory.map(item => item.time),
        y: priceHistory.map(item => item.price),
        type: 'scatter',
        mode: 'lines',
        name: 'SOL Price',
        line: { color: '#1f77b4' }
    }];
    
    const layout = {
        title: 'SOL Price',
        xaxis: { title: 'Time' },
        yaxis: { title: 'Price (USD)' },
        margin: { l: 50, r: 20, t: 40, b: 50 }
    };
    
    Plotly.newPlot('price-chart', data, layout, {responsive: true});
}

function updateEquityChart(equityHistory) {
    const container = document.getElementById('equity-chart');
    if (!container) return;
    
    if (equityHistory.length === 0) {
        container.innerHTML = '<p>Equity history not available yet.</p>';
        return;
    }
    
    const data = [{
        x: equityHistory.map(item => item.time),
        y: equityHistory.map(item => item.equity),
        type: 'scatter',
        mode: 'lines',
        name: 'Total Equity',
        line: { color: '#28a745' }
    }];
    
    const layout = {
        title: 'Total Equity (USD)',
        xaxis: { title: 'Time' },
        yaxis: { title: 'Equity (USD)' },
        margin: { l: 50, r: 20, t: 40, b: 50 }
    };
    
    Plotly.newPlot('equity-chart', data, layout, {responsive: true});
}

function updateDrawdownChart(drawdownHistory) {
    const container = document.getElementById('drawdown-chart');
    if (!container) return;
    
    if (drawdownHistory.length === 0) {
        container.innerHTML = '<p>Drawdown history not available yet.</p>';
        return;
    }
    
    const data = [{
        x: drawdownHistory.map(item => item.time),
        y: drawdownHistory.map(item => item.drawdown_pct),
        type: 'scatter',
        mode: 'lines',
        name: 'Drawdown %',
        line: { color: '#dc3545' },
        fill: 'tozeroy'
    }];
    
    const layout = {
        title: 'Drawdown (%)',
        xaxis: { title: 'Time' },
        yaxis: { title: 'Drawdown (%)' },
        margin: { l: 50, r: 20, t: 40, b: 50 }
    };
    
    Plotly.newPlot('drawdown-chart', data, layout, {responsive: true});
}

function updateTradingViewCharts(statusData) {
    const solHistory = statusData.indicator_history?.sol || [];
    const btcHistory = statusData.indicator_history?.btc || [];
    const solPriceHistory = statusData.price_history || [];
    const btcPriceHistory = statusData.btc_price_history || [];
    
    if (solHistory.length > 0) {
        renderTradingViewChart('sol', solHistory, solPriceHistory);
    }
    
    if (btcHistory.length > 0) {
        renderTradingViewChart('btc', btcHistory, btcPriceHistory);
    }
}

function renderTradingViewChart(asset, indicatorHistory, priceHistory) {
    const containerId = `${asset}-tv-chart`;
    const container = document.getElementById(containerId);
    if (!container) return;
    
    if (indicatorHistory.length === 0) {
        container.innerHTML = `<p>No indicator history for ${asset.toUpperCase()} yet.</p>`;
        return;
    }
    
    // Prepare data arrays
    const times = indicatorHistory.map(item => item.time);
    const prices = priceHistory.length > 0 
        ? priceHistory.map(item => item.price)
        : indicatorHistory.map(item => item.price || 0);
    
    const traces = [];
    const hasPrice = priceHistory.length > 0 || indicatorHistory.some(item => item.price);
    const hasRSI = indicatorHistory.some(item => item.rsi !== undefined);
    const hasMACD = indicatorHistory.some(item => item.macd !== undefined || item.macd_signal !== undefined);
    const hasStoch = indicatorHistory.some(item => item.stoch !== undefined);
    
    // Determine number of rows
    let rowCount = 0;
    if (hasPrice) rowCount++;
    if (hasRSI) rowCount++;
    if (hasMACD) rowCount++;
    if (hasStoch) rowCount++;
    
    let currentRow = 1;
    
    // Row 1: Price + MA + Bollinger Bands
    if (hasPrice) {
        traces.push({
            x: times,
            y: prices,
            type: 'scatter',
            mode: 'lines',
            name: `${asset.toUpperCase()} Price`,
            line: { color: '#1f77b4' },
            xaxis: `x${currentRow}`,
            yaxis: `y${currentRow}`
        });
        
        if (indicatorHistory.some(item => item.moving_avg)) {
            traces.push({
                x: times,
                y: indicatorHistory.map(item => item.moving_avg || null),
                type: 'scatter',
                mode: 'lines',
                name: 'MA',
                line: { color: '#ff7f0e' },
                xaxis: `x${currentRow}`,
                yaxis: `y${currentRow}`
            });
        }
        
        if (indicatorHistory.some(item => item.bb_upper)) {
            traces.push({
                x: times,
                y: indicatorHistory.map(item => item.bb_upper || null),
                type: 'scatter',
                mode: 'lines',
                name: 'BB Upper',
                line: { color: '#2ca02c', width: 1 },
                opacity: 0.6,
                xaxis: `x${currentRow}`,
                yaxis: `y${currentRow}`
            });
            
            traces.push({
                x: times,
                y: indicatorHistory.map(item => item.bb_lower || null),
                type: 'scatter',
                mode: 'lines',
                name: 'BB Lower',
                line: { color: '#d62728', width: 1 },
                opacity: 0.6,
                xaxis: `x${currentRow}`,
                yaxis: `y${currentRow}`
            });
        }
        currentRow++;
    }
    
    // Row 2: RSI
    if (hasRSI) {
        traces.push({
            x: times,
            y: indicatorHistory.map(item => item.rsi || null),
            type: 'scatter',
            mode: 'lines',
            name: 'RSI',
            line: { color: '#9467bd' },
            xaxis: `x${currentRow}`,
            yaxis: `y${currentRow}`
        });
        currentRow++;
    }
    
    // Row 3: MACD
    if (hasMACD) {
        if (indicatorHistory.some(item => item.macd !== undefined)) {
            traces.push({
                x: times,
                y: indicatorHistory.map(item => Array.isArray(item.macd) ? item.macd[0] : item.macd || null),
                type: 'scatter',
                mode: 'lines',
                name: 'MACD',
                line: { color: '#8c564b' },
                xaxis: `x${currentRow}`,
                yaxis: `y${currentRow}`
            });
        }
        if (indicatorHistory.some(item => item.macd_signal !== undefined)) {
            traces.push({
                x: times,
                y: indicatorHistory.map(item => Array.isArray(item.macd_signal) ? item.macd_signal[0] : item.macd_signal || null),
                type: 'scatter',
                mode: 'lines',
                name: 'Signal',
                line: { color: '#7f7f7f' },
                xaxis: `x${currentRow}`,
                yaxis: `y${currentRow}`
            });
        }
        currentRow++;
    }
    
    // Row 4: Stochastic
    if (hasStoch) {
        traces.push({
            x: times,
            y: indicatorHistory.map(item => item.stoch || null),
            type: 'scatter',
            mode: 'lines',
            name: '%K',
            line: { color: '#17becf' },
            xaxis: `x${currentRow}`,
            yaxis: `y${currentRow}`
        });
    }
    
    // Build layout with proper subplot configuration
    const layout = {
        title: `${asset.toUpperCase()} TradingView-style Indicators`,
        height: 800,
        showlegend: true,
        margin: { l: 50, r: 20, t: 50, b: 50 }
    };
    
    // Configure subplot axes
    currentRow = 1;
    const rowHeights = [];
    
    if (hasPrice) {
        layout[`xaxis${currentRow > 1 ? currentRow : ''}`] = { 
            title: currentRow === rowCount ? 'Time' : '',
            domain: [0, 1],
            anchor: `y${currentRow}`
        };
        layout[`yaxis${currentRow > 1 ? currentRow : ''}`] = { 
            title: 'Price',
            domain: getDomain(currentRow, rowCount, 0.45),
            anchor: `x${currentRow}`
        };
        rowHeights.push(0.45);
        currentRow++;
    }
    
    if (hasRSI) {
        layout[`xaxis${currentRow > 1 ? currentRow : ''}`] = { 
            title: currentRow === rowCount ? 'Time' : '',
            domain: [0, 1],
            anchor: `y${currentRow}`
        };
        layout[`yaxis${currentRow > 1 ? currentRow : ''}`] = { 
            title: 'RSI',
            domain: getDomain(currentRow, rowCount, 0.2, hasPrice ? 0.45 : 0),
            anchor: `x${currentRow}`,
            range: [0, 100]
        };
        rowHeights.push(0.2);
        currentRow++;
    }
    
    if (hasMACD) {
        layout[`xaxis${currentRow > 1 ? currentRow : ''}`] = { 
            title: currentRow === rowCount ? 'Time' : '',
            domain: [0, 1],
            anchor: `y${currentRow}`
        };
        layout[`yaxis${currentRow > 1 ? currentRow : ''}`] = { 
            title: 'MACD',
            domain: getDomain(currentRow, rowCount, 0.2, 
                (hasPrice ? 0.45 : 0) + (hasRSI ? 0.2 : 0)),
            anchor: `x${currentRow}`
        };
        rowHeights.push(0.2);
        currentRow++;
    }
    
    if (hasStoch) {
        layout[`xaxis${currentRow > 1 ? currentRow : ''}`] = { 
            title: 'Time',
            domain: [0, 1],
            anchor: `y${currentRow}`
        };
        layout[`yaxis${currentRow > 1 ? currentRow : ''}`] = { 
            title: 'Stochastic',
            domain: getDomain(currentRow, rowCount, 0.15,
                (hasPrice ? 0.45 : 0) + (hasRSI ? 0.2 : 0) + (hasMACD ? 0.2 : 0)),
            anchor: `x${currentRow}`,
            range: [0, 100]
        };
        rowHeights.push(0.15);
    }
    
    Plotly.newPlot(containerId, traces, layout, {responsive: true});
}

function getDomain(row, totalRows, rowHeight, previousHeight = 0) {
    const start = 1 - previousHeight - rowHeight;
    const end = 1 - previousHeight;
    return [start, end];
}

// ==================== Utility Functions ====================

function formatNumber(num, decimals = 2) {
    if (num === null || num === undefined || isNaN(num)) return '0.00';
    return Number(num).toFixed(decimals);
}

function showMessage(message, type = 'info') {
    const display = document.getElementById('message-display');
    if (display) {
        display.textContent = message;
        display.className = `message-display ${type} show`;
        
        setTimeout(() => {
            display.classList.remove('show');
            setTimeout(() => {
                display.textContent = '';
                display.className = 'message-display';
            }, 300);
        }, 3000);
    }
}

function populateProfileSelect(profiles) {
    const select = document.getElementById('profile-select');
    if (!select) return;
    
    // Clear existing options except the first one
    while (select.options.length > 1) {
        select.remove(1);
    }
    
    const profileNames = Object.keys(profiles).sort();
    profileNames.forEach(name => {
        const option = document.createElement('option');
        option.value = name;
        option.textContent = name;
        select.appendChild(option);
    });
}

// ==================== Event Listeners ====================

function initializeEventListeners() {
    // Profile form
    const profileForm = document.getElementById('profile-form');
    if (profileForm) {
        profileForm.addEventListener('submit', (e) => {
            e.preventDefault();
            const formData = {
                name: document.getElementById('profile-name').value,
                api_key: document.getElementById('api-key').value || null,
                api_secret: document.getElementById('api-secret').value || null,
                slack_webhook_url: document.getElementById('slack-webhook').value || null,
                telegram_bot_token: document.getElementById('telegram-token').value || null,
                telegram_chat_id: document.getElementById('telegram-chat-id').value || null
            };
            
            if (!formData.name) {
                showMessage('Please provide a profile name.', 'error');
                return;
            }
            
            saveProfile(formData);
        });
    }
    
    // Profile select
    const profileSelect = document.getElementById('profile-select');
    const profileDisplay = document.getElementById('profile-display');
    const applyProfileBtn = document.getElementById('apply-profile-btn');
    
    if (profileSelect) {
        profileSelect.addEventListener('change', () => {
            const selectedName = profileSelect.value;
            if (selectedName) {
                loadProfiles().then(() => {
                    fetch(`${API_BASE_URL}/profiles`)
                        .then(r => r.json())
                        .then(profiles => {
                            if (profileDisplay) {
                                profileDisplay.textContent = JSON.stringify(profiles[selectedName] || {}, null, 2);
                            }
                            if (applyProfileBtn) {
                                applyProfileBtn.disabled = false;
                            }
                        });
                });
            } else {
                if (profileDisplay) {
                    profileDisplay.textContent = '';
                }
                if (applyProfileBtn) {
                    applyProfileBtn.disabled = true;
                }
            }
        });
    }
    
    if (applyProfileBtn) {
        applyProfileBtn.addEventListener('click', () => {
            const selectedName = profileSelect.value;
            if (selectedName) {
                applyProfile(selectedName);
            }
        });
    }
    
    // Control panel buttons
    const startSimBtn = document.getElementById('start-simulation-btn');
    if (startSimBtn) {
        startSimBtn.addEventListener('click', () => {
            const initialUsdt = parseFloat(document.getElementById('initial-usdt').value) || 1000;
            const initialSol = parseFloat(document.getElementById('initial-sol').value) || 10;
            startSimulation(initialUsdt, initialSol);
        });
    }
    
    const startLiveBtn = document.getElementById('start-live-btn');
    if (startLiveBtn) {
        startLiveBtn.addEventListener('click', () => {
            startLive();
        });
    }
    
    const stopBtn = document.getElementById('stop-btn');
    if (stopBtn) {
        stopBtn.addEventListener('click', () => {
            stopBot();
        });
    }
    
    const manualRefreshBtn = document.getElementById('manual-refresh-btn');
    if (manualRefreshBtn) {
        manualRefreshBtn.addEventListener('click', () => {
            fetchStatus();
        });
    }
    
    // Tab switching
    const tabButtons = document.querySelectorAll('.tab-btn');
    tabButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            const tabName = btn.getAttribute('data-tab');
            
            // Update button states
            tabButtons.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            
            // Update tab content
            document.querySelectorAll('.tab-content').forEach(content => {
                content.classList.remove('active');
            });
            const tabContent = document.getElementById(tabName);
            if (tabContent) {
                tabContent.classList.add('active');
            }
        });
    });
}

