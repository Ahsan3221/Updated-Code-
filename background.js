// ═══════════════════════════════════════════════════════
// FB EMPIRE HELPER - BACKGROUND SERVICE V3.0
// ═══════════════════════════════════════════════════════
// - WebSocket bridge to Python
// - Multi-tab tracking (auto-switch to newest FB tab)
// - Business Suite new tab handling
// - Stealth: minimal logging, silent errors
// ═══════════════════════════════════════════════════════

const TAG = '[FB_HELPER]';
const WS_URL = 'ws://localhost:8765';
const MAX_RETRIES = 100;
const RECONNECT_DELAY = 3000;

let socket = null;
let retries = 0;
let reconnectTimer = null;

// Track all FB tabs for smart selection
let knownFbTabs = new Set();
let activeFbTabId = null;

let state = {
    connected: false,
    currentScreen: 'unknown',
    lastAction: 'Idle',
    lastError: '',
    connectedAt: null,
    messagesReceived: 0,
    messagesSent: 0,
    activeTabId: null,
    tabCount: 0
};

const log = (...x) => console.log(TAG, ...x);

// ═══════════════════════════════════════════════════════
// STATE MANAGEMENT
// ═══════════════════════════════════════════════════════

function broadcast() {
    try {
        chrome.runtime.sendMessage({
            type: 'status',
            data: state
        }).catch(() => {});
    } catch (e) {}
}

function setState(patch) {
    Object.assign(state, patch);
    broadcast();
}

// ═══════════════════════════════════════════════════════
// URL VALIDATION
// ═══════════════════════════════════════════════════════

function isFacebookUrl(url) {
    if (!url) return false;
    return /https?:\/\/([\w-]+\.)?(facebook|business\.facebook)\.com\//.test(url);
}

// ═══════════════════════════════════════════════════════
// WEBSOCKET CONNECTION
// ═══════════════════════════════════════════════════════

function connect() {
    if (socket) {
        const s = socket.readyState;
        if (s === WebSocket.OPEN ||
            s === WebSocket.CONNECTING) {
            return;
        }
    }

    if (reconnectTimer) {
        clearTimeout(reconnectTimer);
        reconnectTimer = null;
    }

    log('Connecting to Python...');
    setState({ lastAction: 'Connecting...' });

    try {
        socket = new WebSocket(WS_URL);
    } catch (e) {
        scheduleReconnect(e.message);
        return;
    }

    socket.onopen = () => {
        retries = 0;
        setState({
            connected: true,
            lastError: '',
            lastAction: 'Connected to Python',
            connectedAt: new Date().toISOString()
        });
        log('✅ WebSocket connected');

        // Send initial tab info to Python
        refreshTabList().then(() => {
            if (activeFbTabId) {
                sendPython({
                    type: 'tab_ready',
                    data: {
                        tab_id: activeFbTabId,
                        total_fb_tabs: knownFbTabs.size
                    }
                });
            }
        });
    };

    socket.onclose = () => {
        setState({ connected: false });
        scheduleReconnect('Disconnected');
    };

    socket.onerror = (e) => {
        log('WebSocket error');
        setState({ lastError: 'Connection error' });
    };

    socket.onmessage = (event) => {
        try {
            const message = JSON.parse(event.data);
            state.messagesReceived++;
            handlePythonMessage(message);
        } catch (e) {
            log('Bad message from Python:', e);
        }
    };
}

function scheduleReconnect(errorMsg) {
    setState({
        connected: false,
        lastError: errorMsg || 'Unknown'
    });

    retries++;
    if (retries <= MAX_RETRIES) {
        log('Retry ' + retries + '/' + MAX_RETRIES +
            ' in ' + (RECONNECT_DELAY / 1000) + 's');
        reconnectTimer = setTimeout(
            connect, RECONNECT_DELAY
        );
    } else {
        log('❌ Max retries reached');
        setState({
            lastAction: 'Max retries - stopped',
            lastError: 'Connection failed'
        });
    }
}

function sendPython(message) {
    if (!socket) {
        return false;
    }

    if (socket.readyState !== WebSocket.OPEN) {
        return false;
    }

    try {
        socket.send(JSON.stringify(message));
        state.messagesSent++;
        return true;
    } catch (e) {
        log('Send error:', e);
        return false;
    }
}

// ═══════════════════════════════════════════════════════
// TAB TRACKING (NEW)
// ═══════════════════════════════════════════════════════

// Refresh the list of all FB tabs
async function refreshTabList() {
    try {
        const allTabs = await chrome.tabs.query({
            url: [
                '*://*.facebook.com/*',
                '*://*.business.facebook.com/*'
            ]
        });

        knownFbTabs.clear();

        // Sort by lastAccessed (newest first)
        allTabs.sort(
            (a, b) => (b.lastAccessed || 0) -
                      (a.lastAccessed || 0)
        );

        for (const tab of allTabs) {
            knownFbTabs.add(tab.id);
        }

        // Set active tab (prefer currently active FB tab)
        const activeTab = allTabs.find(t => t.active);
        if (activeTab) {
            activeFbTabId = activeTab.id;
        } else if (allTabs.length > 0) {
            activeFbTabId = allTabs[0].id;
        } else {
            activeFbTabId = null;
        }

        setState({
            activeTabId: activeFbTabId,
            tabCount: knownFbTabs.size
        });

        return allTabs;
    } catch (e) {
        log('Tab refresh error:', e);
        return [];
    }
}

// Notify Python when a new FB tab appears
function notifyNewTab(tab, reason) {
    if (!isFacebookUrl(tab.url)) return;

    sendPython({
        type: 'tab_changed',
        data: {
            tab_id: tab.id,
            url: tab.url,
            reason: reason,
            total_fb_tabs: knownFbTabs.size
        }
    });

    setState({
        lastAction: 'Tab: ' + reason
    });
}

// ═══════════════════════════════════════════════════════
// TAB LIFECYCLE LISTENERS
// ═══════════════════════════════════════════════════════

// New tab created
try {
    chrome.tabs.onCreated.addListener((tab) => {
        // Wait for URL to load
        setTimeout(async () => {
            try {
                const updated = await chrome.tabs.get(tab.id);
                if (isFacebookUrl(updated.url)) {
                    knownFbTabs.add(updated.id);
                    activeFbTabId = updated.id;
                    setState({
                        activeTabId: updated.id,
                        tabCount: knownFbTabs.size
                    });
                    notifyNewTab(updated, 'created');
                }
            } catch (e) {}
        }, 500);
    });
} catch (e) {}

// Tab updated (URL change or load complete)
try {
    chrome.tabs.onUpdated.addListener(
        (tabId, changeInfo, tab) => {
            try {
                // Only react on complete load or URL change
                if (changeInfo.status !== 'complete' &&
                    !changeInfo.url) {
                    return;
                }

                if (isFacebookUrl(tab.url)) {
                    if (!knownFbTabs.has(tabId)) {
                        knownFbTabs.add(tabId);
                        activeFbTabId = tabId;
                        setState({
                            activeTabId: tabId,
                            tabCount: knownFbTabs.size
                        });
                        notifyNewTab(tab, 'loaded');
                    } else if (changeInfo.url) {
                        // URL changed within FB tab
                        notifyNewTab(tab, 'url_changed');
                    }
                } else {
                    // Tab navigated away from Facebook
                    if (knownFbTabs.has(tabId)) {
                        knownFbTabs.delete(tabId);
                        setState({
                            tabCount: knownFbTabs.size
                        });
                    }
                }
            } catch (e) {}
        }
    );
} catch (e) {}

// Tab activated (user switched tabs)
try {
    chrome.tabs.onActivated.addListener(async (info) => {
        try {
            const tab = await chrome.tabs.get(info.tabId);
            if (isFacebookUrl(tab.url)) {
                activeFbTabId = tab.id;
                setState({ activeTabId: tab.id });
            }
        } catch (e) {}
    });
} catch (e) {}

// Tab removed
try {
    chrome.tabs.onRemoved.addListener((tabId) => {
        if (knownFbTabs.has(tabId)) {
            knownFbTabs.delete(tabId);
            setState({
                tabCount: knownFbTabs.size
            });

            if (activeFbTabId === tabId) {
                // Pick next available FB tab
                refreshTabList();
            }
        }
    });
} catch (e) {}

// ═══════════════════════════════════════════════════════
// FIND FACEBOOK TAB (SMART SELECTION)
// ═══════════════════════════════════════════════════════

async function findFacebookTab() {
    // First try: use tracked active tab
    if (activeFbTabId) {
        try {
            const tab = await chrome.tabs.get(activeFbTabId);
            if (tab && isFacebookUrl(tab.url)) {
                return tab;
            }
        } catch (e) {
            // Tab may have been closed
            activeFbTabId = null;
        }
    }

    // Second try: query all FB tabs (fresh scan)
    const tabs = await refreshTabList();

    if (tabs.length > 0) {
        // Return most recently accessed
        return tabs[0];
    }

    throw new Error(
        'No Facebook tab found. Open facebook.com first.'
    );
}

// ═══════════════════════════════════════════════════════
// COMMUNICATE WITH CONTENT SCRIPT
// ═══════════════════════════════════════════════════════

async function askContent(command, data) {
    const tab = await findFacebookTab();

    if (!data) data = {};

    return new Promise((resolve, reject) => {
        try {
            chrome.tabs.sendMessage(
                tab.id,
                {
                    command: command,
                    target: data.target,
                    data: data.data || {}
                },
                (response) => {
                    if (chrome.runtime.lastError) {
                        reject(new Error(
                            chrome.runtime.lastError.message
                        ));
                        return;
                    }
                    if (!response) {
                        reject(new Error(
                            'No response from content'
                        ));
                        return;
                    }
                    resolve(response);
                }
            );
        } catch (e) {
            reject(e);
        }
    });
}
// ═══════════════════════════════════════════════════════
// COMMAND MAPPING (Python → Content Script)
// ═══════════════════════════════════════════════════════

const COMMAND_MAP = {
    // Existing commands
    'find_element': 'find_element',
    'click_element': 'click_element',
    'check_element_state': 'check_element_state',
    'get_screen': 'get_screen',
    'get_all_buttons': 'get_all_buttons',
    'get_page_info': 'get_page_info',
    'ping': 'ping',

    // NEW commands (V3.0)
    'get_composer_step': 'get_composer_step',
    'get_upload_progress': 'get_upload_progress',
    'is_upload_complete': 'is_upload_complete',
    'wait_for_element': 'wait_for_element'
};

// ═══════════════════════════════════════════════════════
// RESPONSE MAPPING (Content Script → Python)
// ═══════════════════════════════════════════════════════

const RESPONSE_MAP = {
    // Existing responses
    'find_element': 'element_found',
    'click_element': 'element_clicked',
    'check_element_state': 'element_state',
    'get_screen': 'screen_info',
    'get_all_buttons': 'buttons_list',
    'get_page_info': 'page_info',
    'ping': 'pong',

    // NEW responses (V3.0)
    'get_composer_step': 'composer_step',
    'get_upload_progress': 'upload_progress',
    'is_upload_complete': 'upload_complete_status',
    'wait_for_element': 'element_wait_result'
};

// ═══════════════════════════════════════════════════════
// HANDLE PYTHON MESSAGES
// ═══════════════════════════════════════════════════════

async function handlePythonMessage(message) {
    if (!message || typeof message !== 'object') {
        log('Invalid message from Python');
        return;
    }

    const type = message.type;
    const msgId = message.id || null;

    setState({ lastAction: 'Received: ' + type });

    // Handle ping quickly (no content script needed)
    if (type === 'ping') {
        sendPython({
            type: 'pong',
            id: msgId,
            data: {
                pong: true,
                state: state,
                tabCount: knownFbTabs.size,
                activeTabId: activeFbTabId
            }
        });
        return;
    }

    // Special command: get tab info
    if (type === 'get_tab_info') {
        await refreshTabList();
        sendPython({
            type: 'tab_info',
            id: msgId,
            data: {
                activeTabId: activeFbTabId,
                tabCount: knownFbTabs.size,
                tabIds: [...knownFbTabs]
            }
        });
        return;
    }

    // Special command: force switch to newest tab
    if (type === 'switch_to_newest_tab') {
        try {
            const tabs = await refreshTabList();
            if (tabs.length === 0) {
                throw new Error('No Facebook tabs available');
            }

            // Sort by lastAccessed - newest first
            tabs.sort(
                (a, b) => (b.lastAccessed || 0) -
                          (a.lastAccessed || 0)
            );

            activeFbTabId = tabs[0].id;
            setState({ activeTabId: activeFbTabId });

            // Activate the tab
            try {
                await chrome.tabs.update(
                    activeFbTabId,
                    { active: true }
                );
            } catch (e) {}

            sendPython({
                type: 'tab_switched',
                id: msgId,
                data: {
                    tab_id: activeFbTabId,
                    url: tabs[0].url
                }
            });
        } catch (e) {
            sendPython({
                type: 'error',
                id: msgId,
                error: e.message
            });
        }
        return;
    }

    // Regular command mapping
    const contentCommand = COMMAND_MAP[type];
    if (!contentCommand) {
        sendPython({
            type: 'error',
            id: msgId,
            error: 'Unsupported type: ' + type
        });
        return;
    }

    try {
        const result = await askContent(
            contentCommand,
            {
                target: message.target,
                data: message.data || {}
            }
        );

        const responseType = RESPONSE_MAP[type];

        sendPython({
            type: responseType,
            id: msgId,
            data: result
        });

        setState({
            lastAction: type + ' → OK'
        });

    } catch (e) {
        log('Error handling ' + type + ':', e);

        sendPython({
            type: 'error',
            id: msgId,
            error: e.message || 'Unknown error'
        });

        setState({
            lastAction: type + ' → ERROR',
            lastError: e.message
        });
    }
}

// ═══════════════════════════════════════════════════════
// MESSAGE LISTENER
// (From content.js and popup.js)
// ═══════════════════════════════════════════════════════

chrome.runtime.onMessage.addListener(
    (message, sender, respond) => {
        if (!message || !message.type) {
            return false;
        }

        // ═══ From content.js: DOM change ═══
        if (message.type === 'dom_change') {
            const data = message.data || {};
            if (data.screen) {
                state.currentScreen = data.screen;
            }
            sendPython({
                type: 'dom_change',
                data: data
            });
            broadcast();
            return false;
        }

        // ═══ From popup.js: Commands ═══
        if (message.type === 'popup_command') {
            handlePopupCommand(message, respond);
            return true;  // Async response
        }

        return false;
    }
);

// ═══════════════════════════════════════════════════════
// POPUP COMMANDS (FIXED - Clean try-catch)
// ═══════════════════════════════════════════════════════

async function handlePopupCommand(message, respond) {
    const cmd = message.command;

    // ═══ Reconnect command ═══
    if (cmd === 'reconnect') {
        try {
            if (socket) {
                socket.close();
            }
        } catch (e) {}

        retries = 0;
        setState({ lastAction: 'Manual reconnect' });
        connect();
        respond({ ok: true });
        return;
    }

    // ═══ Status command ═══
    if (cmd === 'status') {
        respond({
            ok: true,
            state: state
        });
        return;
    }

    // ═══ Disconnect command ═══
    if (cmd === 'disconnect') {
        try {
            if (socket) {
                socket.close();
            }
        } catch (e) {}

        retries = MAX_RETRIES + 1;
        setState({
            connected: false,
            lastAction: 'Manually disconnected'
        });
        respond({ ok: true });
        return;
    }

    // ═══ Tab info command ═══
    if (cmd === 'tab_info') {
        try {
            await refreshTabList();
            respond({
                ok: true,
                data: {
                    activeTabId: activeFbTabId,
                    tabCount: knownFbTabs.size
                }
            });
        } catch (e) {
            respond({
                ok: false,
                error: e.message
            });
        }
        return;
    }

    // ═══ Forward other commands to content script ═══
    try {
        setState({
            lastAction: 'Popup: ' + cmd
        });

        const data = await askContent(
            cmd,
            {
                target: message.target,
                data: message.data
            }
        );

        if (data && data.screen) {
            setState({ currentScreen: data.screen });
        }

        respond({ ok: true, data: data });
    } catch (e) {
        respond({
            ok: false,
            error: e.message
        });
    }
}

// ═══════════════════════════════════════════════════════
// KEEP SERVICE WORKER ALIVE
// ═══════════════════════════════════════════════════════
// Manifest V3 service workers can sleep after 30 sec
// This interval keeps it alive when connected

setInterval(() => {
    try {
        if (socket &&
            socket.readyState === WebSocket.OPEN) {
            // Send a lightweight keep-alive
            // (Only if idle - won't spam Python)
            const now = Date.now();
            const lastActivity = state.messagesSent +
                state.messagesReceived;

            // Just touch the state to prevent sleep
            broadcast();
        }
    } catch (e) {}
}, 20000);

// ═══════════════════════════════════════════════════════
// LIFECYCLE
// ═══════════════════════════════════════════════════════

try {
    chrome.runtime.onInstalled.addListener(() => {
        log('Extension installed');
        refreshTabList();
        connect();
    });
} catch (e) {}

try {
    chrome.runtime.onStartup.addListener(() => {
        log('Extension started');
        refreshTabList();
        connect();
    });
} catch (e) {}

// ═══════════════════════════════════════════════════════
// INITIALIZATION
// ═══════════════════════════════════════════════════════

log('Background service V3.0 starting...');
refreshTabList().then(() => {
    connect();
});