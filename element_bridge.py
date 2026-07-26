"""
Element Bridge V3.0 - Chrome Extension API
Connects Python with Chrome Extension for
Facebook element finding.

Extension is PRIMARY tool.
Selenium fallback only for critical elements.
"""

import time
from fb_helper import websocket_server as ws


class ElementBridge:
    """
    Find Facebook elements via Chrome Extension
    Falls back to Selenium for critical elements only
    """

    def __init__(self, selenium_finder=None):
        self.selenium_finder = selenium_finder
        self._server_started = False

    # ═══════════════════════════════════════════════════
    # SERVER LIFECYCLE
    # ═══════════════════════════════════════════════════

    def start(self, port=8765):
        """Start WebSocket server"""
        if not self._server_started:
            ws.start_server(port)
            self._server_started = True
            print("[BRIDGE] Server started on port", port)

    def stop(self):
        """Stop WebSocket server"""
        if self._server_started:
            ws.stop_server()
            self._server_started = False

    def is_extension_connected(self):
        """Check if Chrome extension is connected"""
        return ws.is_connected()

    def wait_for_extension(self, timeout=10):
        """
        Wait for extension to connect
        Returns True if connected, False if timeout
        """
        start = time.time()
        while time.time() - start < timeout:
            if ws.is_connected():
                return True
            time.sleep(0.5)
        return False

    def ping(self, timeout=3):
        """Test extension connection with ping"""
        if not ws.is_connected():
            return False

        message = {
            'type': 'ping',
            'data': {},
        }
        response = ws.send_request(
            message, timeout=timeout
        )
        return response is not None

    # ═══════════════════════════════════════════════════
    # FIND ELEMENT (Extension + Fallback)
    # ═══════════════════════════════════════════════════

    def find_element(
        self, target_name,
        dynamic_data=None,
        timeout=8
    ):
        """
        Find element on Facebook page

        Args:
            target_name: Target key from FB_TARGETS
                (e.g., "smart_post_button", "add_photo_video")
            dynamic_data: Optional dict for dynamic targets
                (e.g., {"page_name": "My Page"})
            timeout: Max seconds to wait

        Returns:
            {
                found: True/False,
                x: page_x, y: page_y,
                width: w, height: h,
                text: "button text",
                ariaLabel: "aria-label",
                score: 85,
                strategy: "textPatterns",
                source: "extension" or "fallback",
                screenX, screenY, ...
            }
        """

                # Try Extension first (PRIMARY)
        if ws.is_connected():
            result = self._find_via_extension(
                target_name, dynamic_data, timeout
            )
            if result and result.get('found'):
                # 🔴 FIX: Validate coordinates (prevent 0,0 clicks)
                x = result.get('x', 0)
                y = result.get('y', 0)
                if x == 0 and y == 0:
                    print(f"[BRIDGE] ⚠️ '{target_name}' found but coords are (0,0). Marking invalid!")
                    result['found'] = False
                else:
                    result['source'] = 'extension'
                    return result

        # Fallback to Selenium (only critical targets)
        if self.selenium_finder:
            result = self._find_via_selenium(
                target_name, dynamic_data, timeout
            )
            if result and result.get('found'):
                result['source'] = 'fallback'
                return result

        return {
            'found': False,
            'source': 'none',
            'error': 'Element not found: ' + target_name
        }

    def _find_via_extension(
        self, target_name, dynamic_data, timeout
    ):
        """Find element via Chrome Extension"""
        message = {
            'type': 'find_element',
            'target': target_name,
            'data': dynamic_data or {},
        }

        response = ws.send_request(
            message, timeout=timeout
        )

        if response and response.get('data'):
            return response['data']

        return None

    def _find_via_selenium(
        self, target_name, dynamic_data, timeout
    ):
        """
        Fallback: Find via Selenium (LIMITED)
        Only for critical targets - extension is primary
        """
        if not self.selenium_finder:
            return None

        # Only fallback for these critical targets
        critical_targets = {
            'add_photo_video': [
                "Add photo/video", "Photo/video"
            ],
            'caption_box': None,  # Special handler
            'next_button': ["Next"],
            'share_button': ["Share"],
            'publish_button': ["Publish"],
            'reel_share_button': ["Share"],
            'maybe_later': ["Maybe later", "Not now"],
            'boost_maybe_later': ["Maybe later"],
        }

        # Not a critical target - skip fallback
        if target_name not in critical_targets:
            return None

        # Caption box needs special handler
        if target_name == 'caption_box':
            try:
                pos = self.selenium_finder.find_caption_box(
                    wait=timeout
                )
                if pos and pos[0]:
                    return {
                        'found': True,
                        'x': pos[0],
                        'y': pos[1],
                    }
            except Exception:
                pass
            return None

        # Standard text-based fallback
        texts = critical_targets.get(target_name, [])
        if not texts:
            return None

        for text in texts:
            try:
                pos = self.selenium_finder.find_fb_button(
                    text, wait=min(timeout, 5)
                )
                if pos and pos[0]:
                    return {
                        'found': True,
                        'x': pos[0],
                        'y': pos[1],
                        'text': text,
                    }
            except Exception:
                continue

        return None

    # ═══════════════════════════════════════════════════
    # CHECK ELEMENT STATE
    # ═══════════════════════════════════════════════════

    def check_element_state(
        self, target_name,
        dynamic_data=None,
        timeout=3
    ):
        """
        Check if element is enabled/visible

        Returns:
            {
                found: bool,
                enabled: bool,
                visible: bool,
                x, y, text, ariaLabel
            }
        """
        if ws.is_connected():
            message = {
                'type': 'check_element_state',
                'target': target_name,
                'data': dynamic_data or {},
            }
            response = ws.send_request(
                message, timeout=timeout
            )
            if response and response.get('data'):
                return response['data']

        return {
            'found': False,
            'enabled': False,
            'visible': False,
        }

    # ═══════════════════════════════════════════════════
    # SCREEN DETECTION
    # ═══════════════════════════════════════════════════

    def get_screen(self, timeout=5):
        """
        Get current screen name

        Returns screen name like:
        - 'feed', 'page_profile'
        - 'business_home', 'business_suite'
        - 'composer_create', 'composer_reel_edit'
        - 'publishing', 'boost_popup'
        - 'switched_popup', 'login'
        """
        if ws.is_connected():
            message = {
                'type': 'get_screen',
                'data': {},
            }
            response = ws.send_request(
                message, timeout=timeout
            )
            if response and response.get('data'):
                return response['data'].get(
                    'screen', 'unknown'
                )

        return 'unknown'

    def is_on_screen(self, expected_screen, timeout=3):
        """
        Quick check if currently on expected screen

        Args:
            expected_screen: e.g., 'boost_popup', 'feed'

        Returns: True/False
        """
        current = self.get_screen(timeout=timeout)
        return current == expected_screen

    # ═══════════════════════════════════════════════════
    # PAGE INFO
    # ═══════════════════════════════════════════════════

    def get_page_info(self, timeout=5):
        """
        Get complete page information

        Returns:
            {
                url: 'https://...',
                title: 'Facebook',
                profile_name: 'John Doe',
                screen: 'feed',
                composer_step: 'create',
                screenX, screenY, innerWidth, etc.
            }
        """
        if ws.is_connected():
            message = {
                'type': 'get_page_info',
                'data': {},
            }
            response = ws.send_request(
                message, timeout=timeout
            )
            if response and response.get('data'):
                return response['data']

        return {
            'url': 'unknown',
            'title': 'unknown',
            'profile_name': 'unknown',
            'screen': 'unknown',
            'composer_step': 'unknown',
        }

    def get_current_url(self, timeout=3):
        """Quick get current URL"""
        info = self.get_page_info(timeout=timeout)
        return info.get('url', '')

    def get_profile_name(self, timeout=3):
        """Get currently active profile name"""
        info = self.get_page_info(timeout=timeout)
        return info.get('profile_name', '')

    # ═══════════════════════════════════════════════════
    # DEBUG: GET ALL BUTTONS
    # ═══════════════════════════════════════════════════

    def get_all_buttons(self, timeout=5):
        """
        Get all buttons on page (DEBUG only)
        Returns list of button info dicts
        """
        if ws.is_connected():
            message = {
                'type': 'get_all_buttons',
                'data': {},
            }
            response = ws.send_request(
                message, timeout=timeout
            )
            if response and response.get('data'):
                return response['data'].get(
                    'buttons', []
                )

        # Fallback to Selenium
        if self.selenium_finder:
            try:
                return self.selenium_finder.get_all_buttons()
            except Exception:
                pass

        return []
            # ═══════════════════════════════════════════════════
    # UPLOAD PROGRESS DETECTION (NEW)
    # ═══════════════════════════════════════════════════

    def get_upload_progress(self, timeout=3):
        """
        Get current upload progress

        Returns:
            {
                found: bool,
                percent: 0-100,
                complete: bool
            }
        """
        if ws.is_connected():
            message = {
                'type': 'get_upload_progress',
                'data': {},
            }
            response = ws.send_request(
                message, timeout=timeout
            )
            if response and response.get('data'):
                return response['data']

        return {
            'found': False,
            'percent': 0,
            'complete': False
        }

    def is_upload_complete(self, timeout=3):
        """
        Quick check if upload is complete

        Checks multiple indicators:
        - No progress % < 100 visible
        - Next/Share/Publish button enabled

        Returns: True/False
        """
        if ws.is_connected():
            message = {
                'type': 'is_upload_complete',
                'data': {},
            }
            response = ws.send_request(
                message, timeout=timeout
            )
            if response and response.get('data'):
                return response['data'].get(
                    'complete', False
                )

        return False

    def wait_for_upload_complete(
        self,
        timeout=1800,
        check_interval=5,
        on_progress=None
    ):
        """
        Wait until video upload is complete

        Args:
            timeout: Max wait seconds (default 30 min)
            check_interval: Check every N seconds
            on_progress: Optional callback(percent)

        Returns:
            {
                success: bool,
                elapsed: seconds,
                final_percent: int
            }
        """
        start = time.time()
        last_percent = 0
        last_report = 0

        print("[BRIDGE] Waiting for upload...")

        while time.time() - start < timeout:
            try:
                # Check if complete
                if self.is_upload_complete(timeout=3):
                    elapsed = int(time.time() - start)
                    print(
                        "[BRIDGE] ✅ Upload complete "
                        "in " + str(elapsed) + "s"
                    )
                    return {
                        'success': True,
                        'elapsed': elapsed,
                        'final_percent': 100
                    }

                # Get current percent for reporting
                progress = self.get_upload_progress(
                    timeout=2
                )
                percent = progress.get('percent', 0)

                # Report progress every 10 sec
                now = time.time()
                if percent != last_percent or \
                   now - last_report > 10:
                    print(
                        "[BRIDGE] Upload: " +
                        str(percent) + "%"
                    )
                    last_percent = percent
                    last_report = now

                    if on_progress:
                        try:
                            on_progress(percent)
                        except Exception:
                            pass

            except Exception as e:
                print("[BRIDGE] Progress check error:", e)

            time.sleep(check_interval)

        elapsed = int(time.time() - start)
        print(
            "[BRIDGE] ❌ Upload timeout after " +
            str(elapsed) + "s"
        )
        return {
            'success': False,
            'elapsed': elapsed,
            'final_percent': last_percent
        }

    # ═══════════════════════════════════════════════════
    # COMPOSER STEP DETECTION (NEW)
    # ═══════════════════════════════════════════════════

    def get_composer_step(self, timeout=3):
        """
        Get current composer step (for reels)

        Returns one of:
            'create' - Step 1: Add media + description
            'edit' - Step 2: Audio/video edit
            'share' - Step 3: Privacy/settings
            'publishing' - Publishing overlay
            'not_composer' - Not on composer page
            'unknown' - Cannot determine
        """
        if ws.is_connected():
            message = {
                'type': 'get_composer_step',
                'data': {},
            }
            response = ws.send_request(
                message, timeout=timeout
            )
            if response and response.get('data'):
                return response['data'].get(
                    'step', 'unknown'
                )

        return 'unknown'

    # ═══════════════════════════════════════════════════
    # WAIT METHODS
    # ═══════════════════════════════════════════════════

    def wait_for_element(
        self, target_name,
        dynamic_data=None,
        timeout=30,
        check_interval=2,
        must_be_enabled=False
    ):
        """
        Wait for element to appear (and optionally be enabled)

        Args:
            target_name: Target key
            dynamic_data: Optional dynamic data
            timeout: Max seconds to wait
            check_interval: Check every N seconds
            must_be_enabled: Also wait for enabled state

        Returns:
            Element info dict or {'found': False}
        """
        start = time.time()

        while time.time() - start < timeout:
            result = self.find_element(
                target_name,
                dynamic_data=dynamic_data,
                timeout=3
            )

            if result and result.get('found'):
                # If enabled check required
                if must_be_enabled:
                    state = self.check_element_state(
                        target_name,
                        dynamic_data=dynamic_data,
                        timeout=2
                    )
                    if state.get('enabled'):
                        return result
                    # Not enabled yet, keep waiting
                else:
                    return result

            time.sleep(check_interval)

        return {'found': False}

    def wait_for_screen(
        self,
        expected_screens,
        timeout=30,
        check_interval=2
    ):
        """
        Wait until on one of the expected screens

        Args:
            expected_screens: str or list of screen names
                (e.g., 'boost_popup' or
                 ['composer_create', 'composer_reel_create'])
            timeout: Max seconds
            check_interval: Check every N seconds

        Returns:
            {
                success: bool,
                screen: str,
                elapsed: seconds
            }
        """
        # Normalize to list
        if isinstance(expected_screens, str):
            expected_screens = [expected_screens]

        start = time.time()
        last_screen = None

        while time.time() - start < timeout:
            try:
                current = self.get_screen(timeout=2)

                # Log screen changes
                if current != last_screen:
                    print(
                        "[BRIDGE] Screen: " + current
                    )
                    last_screen = current

                if current in expected_screens:
                    elapsed = int(time.time() - start)
                    return {
                        'success': True,
                        'screen': current,
                        'elapsed': elapsed
                    }

            except Exception as e:
                print("[BRIDGE] Screen check error:", e)

            time.sleep(check_interval)

        elapsed = int(time.time() - start)
        return {
            'success': False,
            'screen': last_screen or 'unknown',
            'elapsed': elapsed
        }

    def wait_for_composer_step(
        self,
        expected_step,
        timeout=30,
        check_interval=2
    ):
        """
        Wait for composer to reach specific step

        Args:
            expected_step: 'create', 'edit', 'share'
            timeout: Max seconds
            check_interval: Check interval

        Returns:
            {
                success: bool,
                step: str,
                elapsed: seconds
            }
        """
        start = time.time()
        last_step = None

        while time.time() - start < timeout:
            try:
                current = self.get_composer_step(
                    timeout=2
                )

                if current != last_step:
                    print(
                        "[BRIDGE] Composer step: " +
                        current
                    )
                    last_step = current

                if current == expected_step:
                    elapsed = int(time.time() - start)
                    return {
                        'success': True,
                        'step': current,
                        'elapsed': elapsed
                    }

            except Exception:
                pass

            time.sleep(check_interval)

        elapsed = int(time.time() - start)
        return {
            'success': False,
            'step': last_step or 'unknown',
            'elapsed': elapsed
        }

    # ═══════════════════════════════════════════════════
    # TAB MANAGEMENT (NEW)
    # ═══════════════════════════════════════════════════

    def get_tab_info(self, timeout=3):
        """
        Get current tab information

        Returns:
            {
                activeTabId: int,
                tabCount: int,
                tabIds: [int, int, ...]
            }
        """
        if ws.is_connected():
            message = {
                'type': 'get_tab_info',
                'data': {},
            }
            response = ws.send_request(
                message, timeout=timeout
            )
            if response and response.get('data'):
                return response['data']

        return {
            'activeTabId': None,
            'tabCount': 0,
            'tabIds': []
        }

    def switch_to_newest_tab(self, timeout=5):
        """
        Force switch to the newest Facebook tab
        Useful after clicking "Meta Business Suite"
        which opens in new tab

        Returns:
            {
                success: bool,
                tab_id: int,
                url: str
            }
        """
        if not ws.is_connected():
            return {
                'success': False,
                'error': 'Extension not connected'
            }

        message = {
            'type': 'switch_to_newest_tab',
            'data': {},
        }
        response = ws.send_request(
            message, timeout=timeout
        )

        if response and response.get('data'):
            data = response['data']
            return {
                'success': True,
                'tab_id': data.get('tab_id'),
                'url': data.get('url', '')
            }

        return {
            'success': False,
            'error': 'Failed to switch tab'
        }

    def wait_for_new_tab(
        self,
        timeout=15,
        check_interval=1
    ):
        """
        Wait for a new Facebook tab to appear
        Useful after clicking links that open new tabs

        Args:
            timeout: Max seconds to wait
            check_interval: Check interval

        Returns:
            {
                success: bool,
                tab_id: int,
                url: str
            }
        """
        # Get initial tab count
        initial = self.get_tab_info(timeout=2)
        initial_count = initial.get('tabCount', 0)

        print(
            "[BRIDGE] Waiting for new tab " +
            "(current: " + str(initial_count) + ")"
        )

        start = time.time()

        while time.time() - start < timeout:
            current = self.get_tab_info(timeout=2)
            current_count = current.get('tabCount', 0)

            if current_count > initial_count:
                # New tab appeared - switch to it
                switched = self.switch_to_newest_tab(
                    timeout=3
                )
                if switched.get('success'):
                    elapsed = int(time.time() - start)
                    print(
                        "[BRIDGE] ✅ New tab in " +
                        str(elapsed) + "s"
                    )
                    return switched

            time.sleep(check_interval)

        return {
            'success': False,
            'error': 'No new tab appeared'
        }

    # ═══════════════════════════════════════════════════
    # POPUP HELPERS (NEW)
    # ═══════════════════════════════════════════════════

    def dismiss_popup(
        self,
        popup_type='auto',
        timeout=5
    ):
        """
        Find popup dismiss button coordinates

        Args:
            popup_type: 'auto', 'boost', 'switched',
                        'maybe_later', 'close_x'

        Returns:
            Element info dict for clicking
            {found: bool, x, y, ...}
        """
        # Try specific popup type
        target_map = {
            'boost': 'boost_maybe_later',
            'switched': 'switched_popup_close',
            'maybe_later': 'maybe_later',
            'close_x': 'switched_popup_close',
        }

        # Auto-detect popup based on current screen
        if popup_type == 'auto':
            screen = self.get_screen(timeout=2)
            if screen == 'boost_popup':
                popup_type = 'boost'
            elif screen == 'switched_popup':
                popup_type = 'switched'
            else:
                # Try generic maybe_later
                popup_type = 'maybe_later'

        target = target_map.get(
            popup_type, 'maybe_later'
        )

        return self.find_element(
            target, timeout=timeout
        )

    # ═══════════════════════════════════════════════════
    # CONVENIENCE METHODS
    # ═══════════════════════════════════════════════════

    def is_composer_open(self, timeout=3):
        """Quick check if composer is open"""
        screen = self.get_screen(timeout=timeout)
        return screen.startswith('composer_')

    def is_publishing(self, timeout=3):
        """Check if currently publishing"""
        return self.is_on_screen(
            'publishing', timeout=timeout
        )

    def is_boost_popup_visible(self, timeout=3):
        """Check if boost popup is showing"""
        return self.is_on_screen(
            'boost_popup', timeout=timeout
        )

    def is_switched_popup_visible(self, timeout=3):
        """Check if 'Switched to' popup is showing"""
        return self.is_on_screen(
            'switched_popup', timeout=timeout
        )

    def is_on_page_profile(self, timeout=3):
        """Check if on page's profile page"""
        return self.is_on_screen(
            'page_profile', timeout=timeout
        )

    def is_on_business_suite(self, timeout=3):
        """Check if on Business Suite"""
        screen = self.get_screen(timeout=timeout)
        return screen.startswith('business_')