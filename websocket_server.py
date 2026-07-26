"""
WebSocket Server V3.0 for FB Helper Extension
Handles communication between Python and Chrome Extension

Features:
- Thread-safe request/response
- Event callback system (push-based)
- Pull-based methods (backward compatible)
- Connection state tracking
- Auto-cleanup of stale requests
"""

import asyncio
import json
import threading
import time
import websockets


# ═══════════════════════════════════════════════════════
# GLOBAL STATE
# ═══════════════════════════════════════════════════════

_ws_connection = None
_ws_server = None
_ws_loop = None
_ws_thread = None
_response_queue = {}
_request_counter = 0
_lock = threading.Lock()
_connected = False
_connect_time = None

# Event callback registry
# Format: {event_type: [callback1, callback2, ...]}
_event_listeners = {}
_listener_lock = threading.Lock()


# ═══════════════════════════════════════════════════════
# TIMESTAMP HELPER
# ═══════════════════════════════════════════════════════

def _ts():
    """Timestamp for logging"""
    return time.strftime("[%H:%M:%S]")


def _log(msg):
    """Log with timestamp"""
    print(f"{_ts()} [WS] {msg}")


# ═══════════════════════════════════════════════════════
# CONNECTION CHECK
# ═══════════════════════════════════════════════════════

def is_connected():
    """Check if extension is connected"""
    return (
        _connected and
        _ws_connection is not None
    )


def get_connection_info():
    """Get connection statistics"""
    return {
        'connected': is_connected(),
        'connect_time': _connect_time,
        'pending_requests': len(_response_queue),
        'listeners': sum(
            len(v) for v in _event_listeners.values()
        )
    }


# ═══════════════════════════════════════════════════════
# EVENT SYSTEM (NEW)
# ═══════════════════════════════════════════════════════

def on(event_type, callback):
    """
    Register callback for extension event

    Args:
        event_type: Event name like 'dom_change',
                    'tab_changed', 'tab_ready',
                    'connect', 'disconnect'
        callback: Function(data) to call when event fires

    Example:
        def handle_tab(data):
            print("New tab:", data.get('url'))

        ws.on('tab_changed', handle_tab)
    """
    with _listener_lock:
        if event_type not in _event_listeners:
            _event_listeners[event_type] = []
        _event_listeners[event_type].append(callback)


def off(event_type, callback=None):
    """
    Remove callback(s) for event

    Args:
        event_type: Event name
        callback: Specific callback to remove
                  (None = remove all for this event)
    """
    with _listener_lock:
        if event_type not in _event_listeners:
            return

        if callback is None:
            _event_listeners[event_type] = []
        else:
            try:
                _event_listeners[event_type].remove(
                    callback
                )
            except ValueError:
                pass


def _fire_event(event_type, data):
    """
    Fire event to all registered callbacks
    Runs in separate threads to avoid blocking
    """
    with _listener_lock:
        callbacks = list(
            _event_listeners.get(event_type, [])
        )

    for cb in callbacks:
        try:
            # Run callback in separate thread
            # so it doesn't block WebSocket handler
            t = threading.Thread(
                target=cb,
                args=(data,),
                daemon=True
            )
            t.start()
        except Exception as e:
            _log(f"Callback error ({event_type}): {e}")


# ═══════════════════════════════════════════════════════
# WEBSOCKET HANDLER
# ═══════════════════════════════════════════════════════

async def _handler(websocket, path=None):
    """Handle WebSocket connections from extension"""
    global _ws_connection, _connected, _connect_time

    _ws_connection = websocket
    _connected = True
    _connect_time = time.time()
    _log("✅ Extension connected!")

    # Fire connect event
    _fire_event('connect', {
        'timestamp': _connect_time
    })

    try:
        async for message in websocket:
            try:
                data = json.loads(message)
                await _process_message(data)

            except json.JSONDecodeError:
                _log("⚠️ Bad JSON received")
            except Exception as e:
                _log(f"Handler error: {e}")

    except websockets.exceptions.ConnectionClosed:
        _log("Extension disconnected (normal)")
    except Exception as e:
        _log(f"Connection error: {e}")
    finally:
        _ws_connection = None
        _connected = False

        # Fire disconnect event
        _fire_event('disconnect', {
            'timestamp': time.time()
        })


async def _process_message(data):
    """Process incoming message from extension"""
    msg_id = data.get('id')
    msg_type = data.get('type', 'unknown')

    # ═══ Response to our request ═══
    if msg_id:
        with _lock:
            if msg_id in _response_queue:
                _response_queue[msg_id] = data
                return

    # ═══ Extension-initiated events ═══
    event_data = data.get('data', {})

    if msg_type == 'dom_change':
        screen = event_data.get('screen', '?')
        _log(f"📺 Screen change → {screen}")
        _fire_event('dom_change', event_data)

    elif msg_type == 'tab_changed':
        url = event_data.get('url', '')[:60]
        reason = event_data.get('reason', '?')
        _log(f"🔀 Tab {reason}: {url}")
        _fire_event('tab_changed', event_data)

    elif msg_type == 'tab_ready':
        tab_id = event_data.get('tab_id', '?')
        total = event_data.get('total_fb_tabs', 0)
        _log(
            f"📑 Tab ready (id={tab_id}, "
            f"total={total})"
        )
        _fire_event('tab_ready', event_data)

    else:
        # Unknown message type - just log
        _log(f"📨 Received: {msg_type}")
        _fire_event(msg_type, event_data)
        # ═══════════════════════════════════════════════════════
# SERVER STARTUP
# ═══════════════════════════════════════════════════════

async def _start_server(port=8765):
    """Start WebSocket server (async)"""
    global _ws_server
    _ws_server = await websockets.serve(
        _handler, "localhost", port
    )
    _log(f"🚀 Server started on ws://localhost:{port}")
    # Keep server running
    await asyncio.Future()  # Run forever


def start_server(port=8765):
    """
    Start WebSocket server in background thread
    Non-blocking - call once from main thread
    """
    global _ws_thread, _ws_loop

    # Prevent double-start
    if _ws_thread and _ws_thread.is_alive():
        _log("⚠️ Server already running")
        return

    def run():
        global _ws_loop
        _ws_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(_ws_loop)
        try:
            _ws_loop.run_until_complete(
                _start_server(port)
            )
        except Exception as e:
            _log(f"❌ Server crashed: {e}")
        finally:
            try:
                _ws_loop.close()
            except Exception:
                pass

    _ws_thread = threading.Thread(
        target=run,
        daemon=True,
        name="WSServerThread"
    )
    _ws_thread.start()
    _log("Server thread started")
    time.sleep(1)  # Give server time to bind


def stop_server():
    """Stop WebSocket server"""
    global _ws_server, _ws_loop, _connected

    _log("Stopping server...")
    _connected = False

    try:
        if _ws_server:
            _ws_server.close()

        if _ws_loop and _ws_loop.is_running():
            # Schedule stop on the loop
            _ws_loop.call_soon_threadsafe(
                _ws_loop.stop
            )

        _log("✅ Server stopped")
    except Exception as e:
        _log(f"Stop error: {e}")


# ═══════════════════════════════════════════════════════
# SEND REQUEST (Wait for Response)
# ═══════════════════════════════════════════════════════

async def _send_and_wait(message, timeout=10):
    """
    Send message to extension and wait for response
    Async internal function
    """
    global _request_counter, _ws_connection

    if not _ws_connection:
        return None

    # Generate unique message ID
    with _lock:
        _request_counter += 1
        msg_id = f"req_{_request_counter}"
        _response_queue[msg_id] = None

    message['id'] = msg_id

    try:
        # Send message
        await _ws_connection.send(
            json.dumps(message)
        )

        # Wait for response
        start = time.time()
        while time.time() - start < timeout:
            with _lock:
                response = _response_queue.get(msg_id)

            if response is not None:
                with _lock:
                    _response_queue.pop(msg_id, None)
                return response

            await asyncio.sleep(0.05)

        # Timeout - cleanup
        with _lock:
            _response_queue.pop(msg_id, None)
        return None

    except websockets.exceptions.ConnectionClosed:
        _log("Connection closed during send")
        with _lock:
            _response_queue.pop(msg_id, None)
        return None
    except Exception as e:
        _log(f"Send error: {e}")
        with _lock:
            _response_queue.pop(msg_id, None)
        return None


def send_request(message, timeout=10):
    """
    Synchronous wrapper - call from any thread
    Returns response dict or None

    Args:
        message: Dict with 'type' and optional data
        timeout: Max seconds to wait

    Returns:
        Response dict or None if failed/timeout
    """
    global _ws_loop

    if not _ws_connection or not _ws_loop:
        return None

    try:
        # Submit coroutine to server's event loop
        future = asyncio.run_coroutine_threadsafe(
            _send_and_wait(message, timeout),
            _ws_loop
        )
        return future.result(timeout=timeout + 2)

    except asyncio.TimeoutError:
        _log("Request timeout")
        return None
    except Exception as e:
        _log(f"Request error: {e}")
        return None


# ═══════════════════════════════════════════════════════
# BROADCAST (Fire and Forget - No Response Wait)
# ═══════════════════════════════════════════════════════

async def _broadcast_async(message):
    """Send without waiting for response"""
    if not _ws_connection:
        return False

    try:
        await _ws_connection.send(
            json.dumps(message)
        )
        return True
    except Exception as e:
        _log(f"Broadcast error: {e}")
        return False


def broadcast(message):
    """
    Send message to extension without waiting for response
    Useful for notifications, commands that don't need reply

    Args:
        message: Dict to send

    Returns:
        True if queued for send, False otherwise
    """
    global _ws_loop

    if not _ws_connection or not _ws_loop:
        return False

    try:
        # Fire and forget - don't wait for result
        asyncio.run_coroutine_threadsafe(
            _broadcast_async(message),
            _ws_loop
        )
        return True
    except Exception as e:
        _log(f"Broadcast schedule error: {e}")
        return False


# ═══════════════════════════════════════════════════════
# CLEANUP UTILITIES
# ═══════════════════════════════════════════════════════

def cleanup_stale_requests(max_age_seconds=60):
    """
    Remove old pending requests from queue
    Should be called periodically to prevent memory leaks
    """
    with _lock:
        # For now, just clear all if too many
        if len(_response_queue) > 100:
            count = len(_response_queue)
            _response_queue.clear()
            _log(
                f"⚠️ Cleared {count} stale requests"
            )


def get_pending_count():
    """Get number of pending requests"""
    with _lock:
        return len(_response_queue)


def clear_all_listeners():
    """Remove all event listeners"""
    with _listener_lock:
        _event_listeners.clear()
    _log("All event listeners cleared")


# ═══════════════════════════════════════════════════════
# HEALTH CHECK
# ═══════════════════════════════════════════════════════

def ping_extension(timeout=3):
    """
    Test if extension is responsive
    Returns True if extension responds to ping
    """
    if not is_connected():
        return False

    response = send_request(
        {'type': 'ping', 'data': {}},
        timeout=timeout
    )

    if response and response.get('type') == 'pong':
        return True
    return False


def wait_for_connection(timeout=10):
    """
    Wait for extension to connect
    Returns True if connected within timeout
    """
    start = time.time()
    while time.time() - start < timeout:
        if is_connected():
            return True
        time.sleep(0.1)
    return False


# ═══════════════════════════════════════════════════════
# STATS / DEBUG
# ═══════════════════════════════════════════════════════

def get_stats():
    """Get server statistics for debugging"""
    return {
        'connected': is_connected(),
        'connect_time': _connect_time,
        'uptime': (
            time.time() - _connect_time
            if _connect_time else 0
        ),
        'pending_requests': get_pending_count(),
        'total_requests': _request_counter,
        'event_listeners': {
            event: len(callbacks)
            for event, callbacks
            in _event_listeners.items()
        },
        'thread_alive': (
            _ws_thread.is_alive()
            if _ws_thread else False
        )
    }


def print_stats():
    """Print server statistics"""
    stats = get_stats()
    print("\n" + "=" * 50)
    print("[WS] SERVER STATISTICS")
    print("=" * 50)
    for key, value in stats.items():
        print(f"  {key}: {value}")
    print("=" * 50 + "\n")