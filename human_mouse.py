"""
Human Mouse & Keyboard Controller - FIXED VERSION
Uses Windows API for 100% undetectable input
FIXED: Mouse ab Chrome window se bahar nahi jayega during warmup
"""

import time
import random
import math
import win32api
import win32con
import win32gui
import ctypes
import ctypes.wintypes
from pynput.mouse import Button, Controller as MouseController
from pynput.keyboard import Controller as KeyController, Key

# Screen dimensions
SCREEN_W = ctypes.windll.user32.GetSystemMetrics(0)
SCREEN_H = ctypes.windll.user32.GetSystemMetrics(1)


class HumanMouse:
    """
    100% undetectable human-like mouse and keyboard controller.
    Uses Windows OS events - Facebook cannot detect this!
    FIXED: Mouse stays inside Chrome window during warmup
    """

    def __init__(self):
        self.mouse = MouseController()
        self.keyboard = KeyController()

        # Screen size
        self.screen_width  = win32api.GetSystemMetrics(0)
        self.screen_height = win32api.GetSystemMetrics(1)

        # FIXED: Chrome window handle
        self.chrome_hwnd = None

        # Track for humanization
        self.last_action_time = time.time()
        self.action_count = 0

    # ═══════════════════════════════════════════════════════════
    # FIXED: Chrome Window Setup
    # ═══════════════════════════════════════════════════════════

    def set_chrome_hwnd(self, hwnd: int):
        """
        FIXED: Chrome window handle set karo
        Jab bhi Chrome window milti hai isko call karo
        """
        self.chrome_hwnd = hwnd

    def _get_chrome_bounds(self):
        """
        FIXED: Chrome window ki safe bounds return karo
        Returns: (left, top, right, bottom) ya None
        """
        if not self.chrome_hwnd:
            return None
        try:
            rect = win32gui.GetWindowRect(self.chrome_hwnd)
            if rect:
                left, top, right, bottom = rect
                # Safe padding taakay navbar/border pe na jaye
                return (
                    left   + 60,
                    top    + 120,   # Navbar skip
                    right  - 60,
                    bottom - 80
                )
        except Exception:
            pass
        return None

    def _clamp_to_chrome(self, x: int, y: int):
        """
        FIXED: Coordinates ko Chrome window ke andar clamp karo
        Agar chrome_hwnd set hai to window ke andar rakhega
        Warna screen bounds use karega
        """
        bounds = self._get_chrome_bounds()
        if bounds:
            left, top, right, bottom = bounds
            x = max(left,  min(x, right))
            y = max(top,   min(y, bottom))
        else:
            # Fallback: screen bounds
            x = max(0, min(x, self.screen_width  - 1))
            y = max(0, min(y, self.screen_height - 1))
        return x, y

    def _ensure_chrome_focus(self):
        """
        FIXED: Chrome window focus check karo
        Agar focus hat gayi ho to wapas do
        """
        if self.chrome_hwnd:
            try:
                focused = win32gui.GetForegroundWindow()
                if focused != self.chrome_hwnd:
                    win32gui.SetForegroundWindow(self.chrome_hwnd)
                    time.sleep(random.uniform(0.15, 0.3))
            except Exception:
                pass

    # ═══════════════════════════════════════════════════════════
    # MOUSE POSITION
    # ═══════════════════════════════════════════════════════════

    def get_position(self):
        """Get current mouse position."""
        return win32api.GetCursorPos()

    # ═══════════════════════════════════════════════════════════
    # MOUSE MOVEMENT - FIXED
    # ═══════════════════════════════════════════════════════════

    def move_to(self, x, y, duration=None, curve_intensity=1.0, hwnd=None):
        """
        Move mouse in human-like bezier curve.
        FIXED: hwnd pass karo to mouse window ke andar rahega

        Args:
            x, y            : Target coordinates
            duration        : How long to take (None = auto)
            curve_intensity : 0.0 = straight, 2.0 = very curved
            hwnd            : Chrome window handle (optional)
        """
        # FIXED: Agar hwnd diya gaya to use set karo
        if hwnd:
            self.chrome_hwnd = hwnd

        # FIXED: Coordinates clamp karo Chrome ya screen bounds mein
        x, y = self._clamp_to_chrome(x, y)

        # Current position
        start_x, start_y = self.get_position()

        # Distance
        distance = math.sqrt((x - start_x) ** 2 + (y - start_y) ** 2)

        # Skip if already there
        if distance < 3:
            return

        # Duration (Fitts's Law)
        if duration is None:
            duration = 0.2 + (distance / 1500)
            duration *= random.uniform(0.7, 1.3)
            duration = min(duration, 2.5)

        # Steps
        steps = max(15, int(duration * 60))

        # Bezier control point
        mid_x = (start_x + x) / 2
        mid_y = (start_y + y) / 2

        offset_magnitude = distance * 0.15 * curve_intensity
        offset_x = random.uniform(-offset_magnitude, offset_magnitude)
        offset_y = random.uniform(-offset_magnitude, offset_magnitude)

        control_x = mid_x + offset_x
        control_y = mid_y + offset_y

        # Move through bezier curve
        for i in range(steps + 1):
            t = i / steps
            t_eased = self._ease_in_out(t)

            # Quadratic Bezier
            curr_x = (
                (1 - t_eased) ** 2 * start_x +
                2 * (1 - t_eased) * t_eased * control_x +
                t_eased ** 2 * x
            )
            curr_y = (
                (1 - t_eased) ** 2 * start_y +
                2 * (1 - t_eased) * t_eased * control_y +
                t_eased ** 2 * y
            )

            # Micro-jitter
            jitter_x = random.uniform(-0.8, 0.8)
            jitter_y = random.uniform(-0.8, 0.8)

            final_x = int(curr_x + jitter_x)
            final_y = int(curr_y + jitter_y)

            # FIXED: Har step pe bhi clamp karo
            final_x, final_y = self._clamp_to_chrome(final_x, final_y)

            # Move
            win32api.SetCursorPos((final_x, final_y))

            # Step delay
            step_delay = (duration / steps) * random.uniform(0.7, 1.3)
            time.sleep(step_delay)

        # Overshoot (like real users) - FIXED: overshoot bhi clamp hoga
        if random.random() < 0.25 and distance > 100:
            overshoot_x = x + random.randint(-15, 15)
            overshoot_y = y + random.randint(-15, 15)

            # FIXED: Overshoot bhi window ke andar
            overshoot_x, overshoot_y = self._clamp_to_chrome(
                overshoot_x, overshoot_y
            )

            win32api.SetCursorPos((overshoot_x, overshoot_y))
            time.sleep(random.uniform(0.03, 0.08))

            # Correct back
            win32api.SetCursorPos((x, y))
            time.sleep(random.uniform(0.02, 0.05))

    def _ease_in_out(self, t):
        """Smooth easing function."""
        return t * t * (3.0 - 2.0 * t)

    # ═══════════════════════════════════════════════════════════
    # MOUSE CLICKS
    # ═══════════════════════════════════════════════════════════

    def click(self, x=None, y=None, button='left', add_offset=True):
        """
        Human-like click.
        FIXED: Click se pehle Chrome focus ensure karta hai
        """
        if x is not None and y is not None:
            if add_offset:
                x += random.randint(-4, 4)
                y += random.randint(-3, 3)

            # FIXED: Clamp before move
            x, y = self._clamp_to_chrome(x, y)
            self.move_to(x, y)

        # FIXED: Focus ensure karo
        self._ensure_chrome_focus()

        time.sleep(random.uniform(0.05, 0.15))

        if button == 'left':
            win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN,  0, 0, 0, 0)
            time.sleep(random.uniform(0.06, 0.15))
            win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP,    0, 0, 0, 0)
        elif button == 'right':
            win32api.mouse_event(win32con.MOUSEEVENTF_RIGHTDOWN, 0, 0, 0, 0)
            time.sleep(random.uniform(0.06, 0.15))
            win32api.mouse_event(win32con.MOUSEEVENTF_RIGHTUP,   0, 0, 0, 0)

        time.sleep(random.uniform(0.1, 0.3))
        self.action_count += 1

    def double_click(self, x, y):
        """Human-like double-click."""
        self.click(x, y)
        time.sleep(random.uniform(0.08, 0.18))
        self.click(x, y, add_offset=False)

    def right_click(self, x, y):
        """Right click."""
        self.click(x, y, button='right')

    # ═══════════════════════════════════════════════════════════
    # SCROLLING - FIXED
    # ═══════════════════════════════════════════════════════════

    def scroll(self, direction='down', amount=3, smooth=True):
        """
        Human-like scrolling.
        FIXED: Scroll se pehle Chrome focus ensure karta hai
        """
        # FIXED: Focus check karo warna scroll kaam nahi karta
        self._ensure_chrome_focus()

        scroll_value = 120 if direction == 'up' else -120

        if smooth:
            for _ in range(amount):
                win32api.mouse_event(
                    win32con.MOUSEEVENTF_WHEEL, 0, 0, scroll_value, 0
                )
                time.sleep(random.uniform(0.08, 0.25))
        else:
            win32api.mouse_event(
                win32con.MOUSEEVENTF_WHEEL, 0, 0, scroll_value * amount, 0
            )

    def scroll_page(self, direction='down'):
        """Scroll one full page."""
        self._ensure_chrome_focus()
        for _ in range(random.randint(4, 7)):
            self.scroll(direction, amount=1)
            time.sleep(random.uniform(0.15, 0.3))

    # ═══════════════════════════════════════════════════════════
    # KEYBOARD - TYPING
    # ═══════════════════════════════════════════════════════════

    def type_text(self, text, wpm=None, make_mistakes=True):
        """Human-like typing with variable speed."""
        if wpm is None:
            wpm = random.randint(40, 90)

        base_delay = 60.0 / (wpm * 5)

        for i, char in enumerate(text):
            if make_mistakes and random.random() < 0.03:
                if char.isalpha():
                    wrong_offset = random.randint(-2, 2)
                    if wrong_offset != 0:
                        try:
                            wrong_char = chr(ord(char) + wrong_offset)
                            self.keyboard.type(wrong_char)
                            time.sleep(random.uniform(0.15, 0.4))
                            self.keyboard.press(Key.backspace)
                            self.keyboard.release(Key.backspace)
                            time.sleep(random.uniform(0.05, 0.15))
                        except Exception:
                            pass

            try:
                self.keyboard.type(char)
            except Exception:
                pass

            delay = base_delay * random.uniform(0.5, 1.5)

            if char in '.,!?;:':
                delay += random.uniform(0.15, 0.4)
            elif char == ' ':
                delay += random.uniform(0.03, 0.12)

            if random.random() < 0.03:
                delay += random.uniform(0.4, 1.5)

            time.sleep(delay)

    def press_key(self, key):
        """Press single key."""
        try:
            if isinstance(key, str):
                self.keyboard.type(key)
            else:
                self.keyboard.press(key)
                time.sleep(random.uniform(0.05, 0.12))
                self.keyboard.release(key)
        except Exception:
            pass
        time.sleep(random.uniform(0.1, 0.3))

    def press_combo(self, *keys):
        """Press key combination."""
        for key in keys:
            if isinstance(key, str):
                self.keyboard.press(key)
            else:
                self.keyboard.press(key)
            time.sleep(random.uniform(0.02, 0.05))

        time.sleep(random.uniform(0.05, 0.1))

        for key in reversed(keys):
            if isinstance(key, str):
                self.keyboard.release(key)
            else:
                self.keyboard.release(key)
            time.sleep(random.uniform(0.02, 0.05))

        time.sleep(random.uniform(0.1, 0.2))

    def copy_paste(self, text):
        """Copy text to clipboard and paste."""
        import pyperclip
        pyperclip.copy(text)
        time.sleep(random.uniform(0.1, 0.3))
        self.press_combo(Key.ctrl, 'v')

    # ═══════════════════════════════════════════════════════════
    # HUMAN BEHAVIOR - FIXED
    # ═══════════════════════════════════════════════════════════

    def natural_wait(self, min_seconds=1, max_seconds=3, description=""):
        """
        Simulate reading/thinking time.
        FIXED: Mouse fidgeting bhi Chrome window ke andar rahega
        """
        wait = random.uniform(min_seconds, max_seconds)

        # FIXED: Fidgeting bhi window ke andar
        if random.random() < 0.3 and wait > 1.5:
            current_x, current_y = self.get_position()

            new_x = current_x + random.randint(-30, 30)
            new_y = current_y + random.randint(-20, 20)

            # FIXED: Chrome bounds use karo
            new_x, new_y = self._clamp_to_chrome(new_x, new_y)

            self.move_to(new_x, new_y, duration=random.uniform(0.5, 1.0))

        time.sleep(wait)

    def reading_pause(self, text_length=100):
        """Pause as if reading text."""
        words = text_length / 5
        base_time = words * 0.3
        actual_time = base_time * random.uniform(0.6, 1.5)
        actual_time = max(0.5, min(actual_time, 10))
        time.sleep(actual_time)

    def hover(self, x, y, duration=None):
        """Move to position and hover."""
        # FIXED: Hover bhi clamp hoga
        x, y = self._clamp_to_chrome(x, y)
        self.move_to(x, y, duration)

        if duration is None:
            duration = random.uniform(0.5, 1.5)
        time.sleep(duration)

    def drag_from_to(self, from_x, from_y, to_x, to_y, duration=1.0):
        """Human-like drag operation."""
        # FIXED: Drag coordinates bhi clamp honge
        from_x, from_y = self._clamp_to_chrome(from_x, from_y)
        to_x,   to_y   = self._clamp_to_chrome(to_x,   to_y)

        self.move_to(from_x, from_y)
        time.sleep(random.uniform(0.1, 0.3))

        win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
        time.sleep(random.uniform(0.05, 0.1))

        self.move_to(to_x, to_y, duration=duration)
        time.sleep(random.uniform(0.1, 0.2))

        win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
        time.sleep(random.uniform(0.1, 0.3))

    # ═══════════════════════════════════════════════════════════
    # WARMUP - FIXED
    # ═══════════════════════════════════════════════════════════

    def warmup_in_window(self, duration: int = 20):
        """
        FIXED: Warmup jo sirf Chrome window ke andar kaam kare
        Agar chrome_hwnd set hai to mouse kabhi bahar nahi jayega
        """
        bounds = self._get_chrome_bounds()
        if not bounds:
            print("    [HumanMouse] ⚠️ Chrome bounds nahi mile, warmup skip")
            return

        left, top, right, bottom = bounds
        print(f"    [HumanMouse] 👻 Warmup start: {duration}s (window-locked)")

        start = time.time()
        while time.time() - start < duration:
            remaining = duration - (time.time() - start)
            if remaining < 1:
                break

            # FIXED: Har action se pehle focus check
            self._ensure_chrome_focus()

            activity = random.choices(
                ['scroll_down', 'scroll_up', 'move', 'pause'],
                weights=[40, 15, 30, 15]
            )[0]

            if activity == 'scroll_down':
                self._ensure_chrome_focus()
                self.scroll('down', amount=random.randint(2, 5))
                time.sleep(random.uniform(1.0, 3.0))

            elif activity == 'scroll_up':
                self._ensure_chrome_focus()
                self.scroll('up', amount=random.randint(1, 3))
                time.sleep(random.uniform(0.5, 1.5))

            elif activity == 'move':
                # FIXED: Sirf Chrome window ke andar move karo
                if right > left and bottom > top:
                    x = random.randint(left, right)
                    y = random.randint(top,  bottom)
                    self.move_to(
                        x, y,
                        duration=random.uniform(0.5, 1.5)
                    )
                    time.sleep(random.uniform(0.5, 2.0))

            elif activity == 'pause':
                time.sleep(random.uniform(1.0, 3.0))

        print("    [HumanMouse] ✅ Warmup complete")


# ═══════════════════════════════════════════════════════════════
# QUICK TEST
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("=" * 55)
    print("HUMAN MOUSE CONTROLLER TEST - FIXED VERSION")
    print("=" * 55)

    mouse = HumanMouse()

    print(f"\n✅ Initialized!")
    print(f"   Screen size: {mouse.screen_width}x{mouse.screen_height}")
    print(f"   Current position: {mouse.get_position()}")

    print("\n" + "=" * 55)
    print("TEST 1: Move to center")
    print("=" * 55)
    input("Press Enter to move mouse to center...")

    center_x = mouse.screen_width  // 2
    center_y = mouse.screen_height // 2

    print(f"Moving to ({center_x}, {center_y})...")
    mouse.move_to(center_x, center_y)
    print(f"✅ Done! Now at: {mouse.get_position()}")

    print("\n" + "=" * 55)
    print("TEST 2: Warmup inside Chrome window")
    print("=" * 55)
    input("Open Chrome then Press Enter...")

    # Chrome window dhundo
    import win32gui as _wg

    def _find_chrome():
        hwnds = []
        def cb(hwnd, _):
            if _wg.IsWindowVisible(hwnd):
                t = _wg.GetWindowText(hwnd)
                c = _wg.GetClassName(hwnd)
                if 'chrome' in c.lower() and len(t) > 0:
                    hwnds.append(hwnd)
            return True
        _wg.EnumWindows(cb, None)
        return hwnds[-1] if hwnds else None

    hwnd = _find_chrome()
    if hwnd:
        print(f"✅ Chrome found! HWND: {hwnd}")
        mouse.set_chrome_hwnd(hwnd)
        print("Running 15s warmup inside Chrome window...")
        mouse.warmup_in_window(duration=15)
        print("✅ Warmup done! Mouse stayed inside Chrome!")
    else:
        print("❌ Chrome not found! Please open Chrome first.")

    print("\n" + "=" * 55)
    print("TEST 3: Scroll test")
    print("=" * 55)
    input("Press Enter to test scroll...")

    print("Scrolling down...")
    mouse.scroll('down', amount=3)
    time.sleep(1)
    print("Scrolling up...")
    mouse.scroll('up', amount=3)
    print("✅ Done!")

    print("\n" + "=" * 55)
    print("ALL TESTS COMPLETE!")
    print("=" * 55)