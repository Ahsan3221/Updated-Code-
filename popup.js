// ═══════════════════════════════════════════════════════
// POPUP CONTROLLER V3.0
// FB Empire Helper Extension
// ═══════════════════════════════════════════════════════

const $ = (id) => document.getElementById(id);

// Auto-refresh interval (ms)
const AUTO_REFRESH_INTERVAL = 3000;
let autoRefreshTimer = null;
let currentState = {};

// ═══════════════════════════════════════════════════════
// OUTPUT HELPER
// ═══════════════════════════════════════════════════════

function output(data) {
    const el = $('output');
    if (!el) return;

    if (typeof data === 'string') {
        el.textContent = data;
    } else {
        try {
            el.textContent = JSON.stringify(
                data, null, 2
            );
        } catch (e) {
            el.textContent = String(data);
        }
    }
}

function showError(msg) {
    const box = $('error-box');
    const errMsg = $('error-msg');
    if (box && errMsg) {
        errMsg.textContent = msg;
        box.classList.remove('hidden');
    }
}

function hideError() {
    const box = $('error-box');
    if (box) {
        box.classList.add('hidden');
    }
}

// ═══════════════════════════════════════════════════════
// LOADING STATE HELPERS
// ═══════════════════════════════════════════════════════

function setButtonLoading(buttonId, loading) {
    const btn = $(buttonId);
    if (!btn) return;

    if (loading) {
        btn.disabled = true;
        btn.dataset.originalText = btn.textContent;
        btn.textContent = '⏳ Loading...';
    } else {
        btn.disabled = false;
        if (btn.dataset.originalText) {
            btn.textContent = btn.dataset.originalText;
        }
    }
}

function flashSuccess(buttonId) {
    const btn = $(buttonId);
    if (!btn) return;

    const original = btn.textContent;
    btn.textContent = '✅ Done';
    btn.style.background = '#4caf50';

    setTimeout(() => {
        btn.textContent = original;
        btn.style.background = '';
    }, 1000);
}

// ═══════════════════════════════════════════════════════
// RENDER STATE (Enhanced)
// ═══════════════════════════════════════════════════════

function render(state) {
    if (!state) return;

    // Store current state
    currentState = { ...currentState, ...state };

    // ═══ Connection dot + text ═══
    const dot = $('dot');
    const conn = $('connection');

    if (state.connected) {
        if (dot) dot.className = 'dot on';
        if (conn) conn.textContent = 'Python connected';
        hideError();
    } else {
        if (dot) dot.className = 'dot off';
        if (conn) conn.textContent = 'Python offline';
    }

    // ═══ Screen ═══
    const screen = $('screen');
    if (screen) {
        const s = state.currentScreen || 'unknown';
        screen.textContent = s;

        // Color code based on screen type
        screen.className = 'value';
        if (s.startsWith('composer_')) {
            screen.classList.add('screen-composer');
        } else if (s === 'boost_popup' ||
                   s === 'publishing') {
            screen.classList.add('screen-important');
        } else if (s === 'login' ||
                   s === 'unknown') {
            screen.classList.add('screen-warning');
        }
    }

    // ═══ Composer Step (NEW) ═══
    const composerStep = $('composer-step');
    if (composerStep) {
        const s = state.currentScreen || '';
        let step = '-';

        if (s === 'composer_reel_create' ||
            s === 'composer_create') {
            step = '1️⃣ Create';
        } else if (s === 'composer_reel_edit' ||
                   s === 'composer_edit') {
            step = '2️⃣ Edit';
        } else if (s === 'composer_reel_share' ||
                   s === 'composer_share') {
            step = '3️⃣ Share';
        } else if (s === 'publishing') {
            step = '⏳ Publishing...';
        } else if (s === 'boost_popup') {
            step = '✅ Published!';
        }

        composerStep.textContent = step;
    }

    // ═══ Action ═══
    const action = $('action');
    if (action) {
        action.textContent =
            state.lastAction || 'Idle';
    }

    // ═══ Tab Info (NEW) ═══
    const tabInfo = $('tab-info');
    if (tabInfo) {
        const count = state.tabCount || 0;
        const activeId = state.activeTabId || '-';
        tabInfo.textContent =
            'Tabs: ' + count +
            ' | Active: #' + activeId;
    }

    // ═══ Message stats ═══
    const messages = $('messages');
    if (messages) {
        const sent = state.messagesSent || 0;
        const recv = state.messagesReceived || 0;
        messages.textContent =
            'Sent: ' + sent + ' | Recv: ' + recv;
    }

    // ═══ Connection uptime (NEW) ═══
    const uptime = $('uptime');
    if (uptime && state.connectedAt) {
        try {
            const connectTime = new Date(
                state.connectedAt
            );
            const seconds = Math.floor(
                (Date.now() - connectTime) / 1000
            );

            let display = '';
            if (seconds < 60) {
                display = seconds + 's';
            } else if (seconds < 3600) {
                display = Math.floor(seconds / 60) + 'm';
            } else {
                display = Math.floor(
                    seconds / 3600
                ) + 'h ' +
                Math.floor(
                    (seconds % 3600) / 60
                ) + 'm';
            }

            uptime.textContent = display;
        } catch (e) {
            uptime.textContent = '-';
        }
    }

    // ═══ Error display ═══
    if (state.lastError) {
        showError(state.lastError);
    }
}

// ═══════════════════════════════════════════════════════
// COMMAND SENDER
// ═══════════════════════════════════════════════════════

function command(cmd, extra) {
    return new Promise((resolve) => {
        const msg = {
            type: 'popup_command',
            command: cmd
        };

        if (extra) {
            Object.assign(msg, extra);
        }

        try {
            chrome.runtime.sendMessage(
                msg,
                (response) => {
                    if (chrome.runtime.lastError) {
                        resolve({
                            ok: false,
                            error:
                                chrome.runtime
                                    .lastError.message
                        });
                        return;
                    }
                    resolve(response || {
                        ok: false,
                        error: 'No response'
                    });
                }
            );
        } catch (e) {
            resolve({
                ok: false,
                error: e.message
            });
        }
    });
}
// ═══════════════════════════════════════════════════════
// ACTIONS
// ═══════════════════════════════════════════════════════

async function refreshStatus() {
    setButtonLoading('refresh', true);
    output('Refreshing...');

    try {
        // Get latest status from background
        const statusResult = await command('status');
        if (statusResult && statusResult.state) {
            render(statusResult.state);
        }

        // Get current screen from content script
        const result = await command('get_screen');

        if (result && result.ok) {
            const currentState = statusResult
                ? statusResult.state
                : {};

            render({
                ...currentState,
                currentScreen: result.data.screen
            });
            output(result.data);
        } else {
            const err = (result && result.error)
                ? result.error
                : 'Unable to read Facebook tab';
            output('❌ ' + err);
        }
    } finally {
        setButtonLoading('refresh', false);
    }
}

async function listAllElements() {
    setButtonLoading('debug', true);
    output('Scanning page...');

    try {
        const result = await command('get_all_buttons');

        if (result && result.ok) {
            const data = result.data || {};
            const buttons = data.buttons || [];

            let text = 'Found ' +
                buttons.length + ' elements:\n\n';

            buttons.slice(0, 30).forEach((b, i) => {
                const label = b.text ||
                    b.ariaLabel || '(no text)';
                text += (i + 1) + '. [' +
                    (b.tag || '?') + '] ' +
                    label.substring(0, 60) +
                    (b.disabled ? ' [DISABLED]' : '') +
                    '\n' +
                    '   @ (' + Math.round(b.x) +
                    ', ' + Math.round(b.y) + ')\n\n';
            });

            if (buttons.length > 30) {
                text += '... and ' +
                    (buttons.length - 30) + ' more';
            }

            output(text);
        } else {
            const err = (result && result.error)
                ? result.error
                : 'Failed to scan';
            output('❌ ' + err);
        }
    } finally {
        setButtonLoading('debug', false);
    }
}

async function reconnect() {
    setButtonLoading('reconnect', true);
    output('Reconnecting...');

    try {
        const result = await command('reconnect');

        if (result && result.ok) {
            output('✅ Reconnection initiated');
            flashSuccess('reconnect');

            setTimeout(async () => {
                const status = await command('status');
                if (status && status.state) {
                    render(status.state);
                }
            }, 1500);
        } else {
            const err = (result && result.error)
                ? result.error
                : 'Failed to reconnect';
            output('❌ ' + err);
        }
    } finally {
        setButtonLoading('reconnect', false);
    }
}

// ═══════════════════════════════════════════════════════
// NEW ACTIONS
// ═══════════════════════════════════════════════════════

async function getPageInfo() {
    setButtonLoading('page-info', true);
    output('Getting page info...');

    try {
        const result = await command('get_page_info');

        if (result && result.ok) {
            const data = result.data || {};

            let text = '📋 PAGE INFO\n';
            text += '─'.repeat(40) + '\n\n';
            text += 'URL: ' +
                (data.url || 'unknown') + '\n\n';
            text += 'Title: ' +
                (data.title || 'unknown') + '\n\n';
            text += 'Screen: ' +
                (data.screen || 'unknown') + '\n\n';
            text += 'Composer Step: ' +
                (data.composer_step || '-') + '\n\n';
            text += 'Profile: ' +
                (data.profile_name || '-') + '\n\n';
            text += 'Window: ' +
                (data.innerWidth || 0) + ' x ' +
                (data.innerHeight || 0) + '\n';

            output(text);
            flashSuccess('page-info');
        } else {
            const err = (result && result.error)
                ? result.error
                : 'Failed to get info';
            output('❌ ' + err);
        }
    } finally {
        setButtonLoading('page-info', false);
    }
}

async function pingTest() {
    setButtonLoading('ping', true);
    output('Pinging extension...');

    try {
        const startTime = Date.now();
        const result = await command('ping');
        const elapsed = Date.now() - startTime;

        if (result && result.ok) {
            const data = result.data || {};

            let text = '💓 PING RESULT\n';
            text += '─'.repeat(40) + '\n\n';
            text += '✅ Response received\n';
            text += 'Latency: ' + elapsed + 'ms\n';
            text += 'Version: ' +
                (data.version || '?') + '\n\n';
            text += 'Window: ' +
                (data.innerWidth || 0) + ' x ' +
                (data.innerHeight || 0) + '\n';

            output(text);
            flashSuccess('ping');
        } else {
            const err = (result && result.error)
                ? result.error
                : 'No response from extension';
            output('❌ ' + err +
                '\nLatency: ' + elapsed + 'ms');
        }
    } finally {
        setButtonLoading('ping', false);
    }
}

async function getComposerStep() {
    setButtonLoading('composer-check', true);
    output('Checking composer...');

    try {
        const result = await command(
            'get_composer_step'
        );

        if (result && result.ok) {
            const data = result.data || {};

            let text = '🎬 COMPOSER STATE\n';
            text += '─'.repeat(40) + '\n\n';
            text += 'Step: ' +
                (data.step || 'unknown') + '\n\n';
            text += 'Screen: ' +
                (data.screen || 'unknown') + '\n\n';

            // Descriptive status
            if (data.step === 'create') {
                text += '📝 On Create step\n';
                text += '   → Add media & caption';
            } else if (data.step === 'edit') {
                text += '✂️ On Edit step\n';
                text += '   → Edit audio/video';
            } else if (data.step === 'share') {
                text += '🚀 On Share step\n';
                text += '   → Ready to publish!';
            } else if (data.step === 'publishing') {
                text += '⏳ Publishing in progress...';
            } else if (data.step === 'not_composer') {
                text += 'ℹ️ Not on composer page';
            }

            output(text);
            flashSuccess('composer-check');
        } else {
            const err = (result && result.error)
                ? result.error
                : 'Failed to check';
            output('❌ ' + err);
        }
    } finally {
        setButtonLoading('composer-check', false);
    }
}

async function checkUploadProgress() {
    setButtonLoading('upload-check', true);
    output('Checking upload progress...');

    try {
        const result = await command(
            'get_upload_progress'
        );

        if (result && result.ok) {
            const data = result.data || {};

            let text = '📤 UPLOAD PROGRESS\n';
            text += '─'.repeat(40) + '\n\n';

            if (data.found) {
                text += 'Progress: ' +
                    data.percent + '%\n\n';

                // Progress bar
                const filled = Math.floor(
                    data.percent / 5
                );
                const empty = 20 - filled;
                text += '[' +
                    '█'.repeat(filled) +
                    '░'.repeat(empty) +
                    ']\n\n';

                if (data.complete) {
                    text += '✅ Upload COMPLETE!';
                } else {
                    text += '⏳ Still uploading...';
                }
            } else {
                text += 'ℹ️ No upload detected\n';
                text += '(Not in composer or ' +
                    'no video attached)';
            }

            output(text);
            flashSuccess('upload-check');
        } else {
            const err = (result && result.error)
                ? result.error
                : 'Failed to check';
            output('❌ ' + err);
        }
    } finally {
        setButtonLoading('upload-check', false);
    }
}

async function switchToNewestTab() {
    setButtonLoading('switch-tab', true);
    output('Switching to newest tab...');

    try {
        const result = await command(
            'tab_info'
        );

        if (result && result.ok) {
            const data = result.data || {};

            let text = '🔀 TAB INFO\n';
            text += '─'.repeat(40) + '\n\n';
            text += 'Active Tab ID: ' +
                (data.activeTabId || '-') + '\n';
            text += 'Total FB Tabs: ' +
                (data.tabCount || 0) + '\n';

            output(text);
            flashSuccess('switch-tab');
        } else {
            output('❌ Failed to get tab info');
        }
    } finally {
        setButtonLoading('switch-tab', false);
    }
}

function clearOutput() {
    output('Ready. Click a button above.');
    hideError();
}

// ═══════════════════════════════════════════════════════
// AUTO-REFRESH SYSTEM
// ═══════════════════════════════════════════════════════

async function autoRefreshTick() {
    try {
        // Silent status refresh (no output change)
        const statusResult = await command('status');
        if (statusResult && statusResult.state) {
            render(statusResult.state);
        }

        // Also update screen silently
        const screenResult = await command('get_screen');
        if (screenResult && screenResult.ok) {
            const merged = {
                ...currentState,
                currentScreen: screenResult.data.screen
            };
            render(merged);
        }
    } catch (e) {
        // Silent fail - don't disturb user
    }
}

function startAutoRefresh() {
    if (autoRefreshTimer) return;

    autoRefreshTimer = setInterval(
        autoRefreshTick,
        AUTO_REFRESH_INTERVAL
    );
}

function stopAutoRefresh() {
    if (autoRefreshTimer) {
        clearInterval(autoRefreshTimer);
        autoRefreshTimer = null;
    }
}

// ═══════════════════════════════════════════════════════
// EVENT LISTENERS SETUP
// ═══════════════════════════════════════════════════════

function setupEvents() {
    // Existing buttons
    const debug = $('debug');
    if (debug) {
        debug.onclick = listAllElements;
    }

    const refresh = $('refresh');
    if (refresh) {
        refresh.onclick = refreshStatus;
    }

    const reconnectBtn = $('reconnect');
    if (reconnectBtn) {
        reconnectBtn.onclick = reconnect;
    }

    const clear = $('clear');
    if (clear) {
        clear.onclick = clearOutput;
    }

    // NEW buttons
    const pageInfo = $('page-info');
    if (pageInfo) {
        pageInfo.onclick = getPageInfo;
    }

    const ping = $('ping');
    if (ping) {
        ping.onclick = pingTest;
    }

    const composerCheck = $('composer-check');
    if (composerCheck) {
        composerCheck.onclick = getComposerStep;
    }

    const uploadCheck = $('upload-check');
    if (uploadCheck) {
        uploadCheck.onclick = checkUploadProgress;
    }

    const switchTab = $('switch-tab');
    if (switchTab) {
        switchTab.onclick = switchToNewestTab;
    }
}

// ═══════════════════════════════════════════════════════
// STATUS UPDATES FROM BACKGROUND
// ═══════════════════════════════════════════════════════

chrome.runtime.onMessage.addListener(
    (msg, sender, respond) => {
        if (msg && msg.type === 'status') {
            render(msg.data);
        }
        return false;
    }
);

// ═══════════════════════════════════════════════════════
// LIFECYCLE
// ═══════════════════════════════════════════════════════

async function init() {
    setupEvents();

    // Get initial state
    const result = await command('status');
    if (result && result.state) {
        render(result.state);
    }

    // Then get current page info
    await refreshStatus();

    // Start auto-refresh
    startAutoRefresh();
}

// Cleanup when popup closes
window.addEventListener('unload', () => {
    stopAutoRefresh();
});

// Start when DOM ready
if (document.readyState === 'loading') {
    document.addEventListener(
        'DOMContentLoaded', init
    );
} else {
    init();
}