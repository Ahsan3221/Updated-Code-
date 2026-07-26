"""
Human Control System V2.0 - FIXED VERSION
Mouse now stays inside Chrome window during warmup
"""
import ctypes
import ctypes.wintypes
import win32api
import win32con
import win32gui
import win32process
import time
import random
import math
import numpy as np
from typing import Tuple, Optional, List


# ═══ WIN32 STRUCTURES ═══

class MOUSEINPUT(ctypes.Structure):
    _fields_ = [
        ("dx",          ctypes.c_long),
        ("dy",          ctypes.c_long),
        ("mouseData",   ctypes.c_ulong),
        ("dwFlags",     ctypes.c_ulong),
        ("time",        ctypes.c_ulong),
        ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong)),
    ]


class KEYBDINPUT(ctypes.Structure):
    _fields_ = [
        ("wVk",         ctypes.c_ushort),
        ("wScan",       ctypes.c_ushort),
        ("dwFlags",     ctypes.c_ulong),
        ("time",        ctypes.c_ulong),
        ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong)),
    ]


class _INPUT_UNION(ctypes.Union):
    _fields_ = [
        ("mi", MOUSEINPUT),
        ("ki", KEYBDINPUT),
    ]


class INPUT(ctypes.Structure):
    _fields_ = [
        ("type",  ctypes.c_ulong),
        ("_input", _INPUT_UNION),
    ]


# ═══ CONSTANTS ═══
INPUT_MOUSE    = 0
INPUT_KEYBOARD = 1
MOUSEEVENTF_MOVE        = 0x0001
MOUSEEVENTF_LEFTDOWN    = 0x0002
MOUSEEVENTF_LEFTUP      = 0x0004
MOUSEEVENTF_RIGHTDOWN   = 0x0008
MOUSEEVENTF_RIGHTUP     = 0x0010
MOUSEEVENTF_MIDDLEDOWN  = 0x0020
MOUSEEVENTF_MIDDLEUP    = 0x0040
MOUSEEVENTF_WHEEL       = 0x0800
MOUSEEVENTF_ABSOLUTE    = 0x8000
KEYEVENTF_KEYUP         = 0x0002
KEYEVENTF_SCANCODE      = 0x0008

# Screen dimensions
SCREEN_W = ctypes.windll.user32.GetSystemMetrics(0)
SCREEN_H = ctypes.windll.user32.GetSystemMetrics(1)


# ═══════════════════════════════════════
# HUMAN MOUSE CLASS - FIXED
# ═══════════════════════════════════════

class HumanMouse:
    """
    99% Human-like mouse control
    FIXED: Mouse will now stay inside Chrome window during warmup
    """

    def __init__(self):
        self.user32 = ctypes.windll.user32
        self._last_x = 0
        self._last_y = 0
        self._update_position()

    def _update_position(self):
        """Current mouse position update karo"""
        pt = ctypes.wintypes.POINT()
        self.user32.GetCursorPos(ctypes.byref(pt))
        self._last_x = pt.x
        self._last_y = pt.y

    def _to_absolute(self, x: int, y: int) -> Tuple[int, int]:
        """Screen coords to absolute (0-65535)"""
        abs_x = int(x * 65535 / SCREEN_W)
        abs_y = int(y * 65535 / SCREEN_H)
        return abs_x, abs_y

    def _send_mouse_input(
        self, dx: int, dy: int, flags: int,
        mouse_data: int = 0
    ):
        """Raw mouse input send karo via SendInput"""
        extra = ctypes.c_ulong(0)
        ii_ = _INPUT_UNION()
        ii_.mi = MOUSEINPUT(
            dx, dy, mouse_data, flags,
            0, ctypes.pointer(extra)
        )
        x = INPUT(INPUT_MOUSE, ii_)
        self.user32.SendInput(
            1, ctypes.pointer(x), ctypes.sizeof(x)
        )

    def _bezier_curve(
        self,
        start: Tuple[int, int],
        end: Tuple[int, int],
        num_points: int = 50
    ) -> List[Tuple[int, int]]:
        x1, y1 = start
        x2, y2 = end
        dist = math.sqrt((x2-x1)**2 + (y2-y1)**2)

        offset1 = random.randint(int(dist * 0.1), int(dist * 0.4))
        offset2 = random.randint(int(dist * 0.1), int(dist * 0.4))

        angle1 = random.uniform(0, 2 * math.pi)
        angle2 = random.uniform(0, 2 * math.pi)

        cx1 = x1 + offset1 * math.cos(angle1)
        cy1 = y1 + offset1 * math.sin(angle1)
        cx2 = x2 + offset2 * math.cos(angle2)
        cy2 = y2 + offset2 * math.sin(angle2)

        points = []
        for i in range(num_points + 1):
            t = i / num_points
            x = (
                (1-t)**3 * x1 +
                3*(1-t)**2 * t * cx1 +
                3*(1-t) * t**2 * cx2 +
                t**3 * x2
            )
            y = (
                (1-t)**3 * y1 +
                3*(1-t)**2 * t * cy1 +
                3*(1-t) * t**2 * cy2 +
                t**3 * y2
            )
            points.append((int(x), int(y)))
        return points

    def _human_speed_profile(self, num_points: int) -> List[float]:
        delays = []
        for i in range(num_points):
            t = i / num_points
            if t < 0.2:
                speed = 0.3 + t * 3.5
            elif t > 0.8:
                speed = 0.3 + (1 - t) * 3.5
            else:
                speed = 1.0 + random.uniform(-0.2, 0.2)
            speed += random.uniform(-0.1, 0.1)
            speed = max(0.1, speed)
            delays.append(1.0 / (speed * 100))
        return delays

    def _add_micro_tremor(self, x: int, y: int) -> Tuple[int, int]:
        tremor_x = random.randint(-1, 1)
        tremor_y = random.randint(-1, 1)
        return x + tremor_x, y + tremor_y

    # ===================== FIXED FUNCTION =====================
    def move_to(
        self, x: int, y: int,
        duration: float = None,
        overshoot: bool = True,
        hwnd: int = None
    ):
        """
        FIXED: Agar hwnd diya gaya ho to mouse window ke andar hi rahega
        """
        if hwnd:
            rect = win32gui.GetWindowRect(hwnd)
            if rect:
                left, top, right, bottom = rect
                # Clamp coordinates inside window (with padding)
                x = max(left + 50, min(x, right - 50))
                y = max(top + 80, min(y, bottom - 100))   # Top padding zyada rakha taaki navbar pe na jaye

        self._update_position()
        start = (self._last_x, self._last_y)
        end = (x, y)

        dist = math.sqrt((x - self._last_x)**2 + (y - self._last_y)**2)

        if duration is None:
            speed = random.uniform(400, 900)
            duration = dist / speed
            duration = max(0.1, min(duration, 2.0))

        if overshoot and dist > 50:
            overshoot_dist = random.uniform(5, 20)
            angle = math.atan2(y - self._last_y, x - self._last_x)
            overshoot_x = int(x + overshoot_dist * math.cos(angle))
            overshoot_y = int(y + overshoot_dist * math.sin(angle))
            
            self._move_along_bezier(start, (overshoot_x, overshoot_y), duration * 0.9)
            time.sleep(random.uniform(0.02, 0.08))
            self._move_along_bezier((overshoot_x, overshoot_y), end, duration * 0.1)
        else:
            self._move_along_bezier(start, end, duration)

        self._last_x = x
        self._last_y = y

    def _move_along_bezier(self, start, end, duration):
        dist = math.sqrt((end[0]-start[0])**2 + (end[1]-start[1])**2)
        num_points = max(10, min(80, int(dist / 5)))

        points = self._bezier_curve(start, end, num_points)
        delays = self._human_speed_profile(num_points)

        total_delay = sum(delays)
        scale = duration / total_delay if total_delay > 0 else 1

        for i, (px, py) in enumerate(points):
            px, py = self._add_micro_tremor(px, py)
            abs_x, abs_y = self._to_absolute(px, py)

            self._send_mouse_input(
                abs_x, abs_y,
                MOUSEEVENTF_MOVE | MOUSEEVENTF_ABSOLUTE
            )
            delay = delays[i] * scale
            time.sleep(max(0.001, delay))

    # NEW HELPER METHOD
    def move_to_in_window(self, hwnd: int, rel_x: float, rel_y: float, duration=None):
        """Chrome window ke andar relative position pe move karo"""
        rect = win32gui.GetWindowRect(hwnd)
        if not rect:
            return
        win_w = rect[2] - rect[0]
        win_h = rect[3] - rect[1]
        abs_x = rect[0] + int(win_w * rel_x)
        abs_y = rect[1] + int(win_h * rel_y)
        self.move_to(abs_x, abs_y, duration=duration, hwnd=hwnd)

    def random_micro_move(self, hwnd: int = None):
        """FIXED: Micro move bhi window ke andar rahega"""
        self._update_position()
        if hwnd:
            rect = win32gui.GetWindowRect(hwnd)
            if rect:
                left, top, right, bottom = rect
                x = random.randint(left + 80, right - 80)
                y = random.randint(top + 120, bottom - 100)
                self.move_to(x, y, duration=random.uniform(0.15, 0.4), overshoot=False, hwnd=hwnd)
                return

        # Fallback (screen)
        dx = random.randint(-15, 15)
        dy = random.randint(-15, 15)
        self.move_to(self._last_x + dx, self._last_y + dy, 
                    duration=random.uniform(0.1, 0.3), overshoot=False)

    # ... baaki methods (click, scroll, etc.) same rakhe hain ...
    def click(self, x=None, y=None, button="left", move_first=True, double=False):
        if x is not None and y is not None:
            if move_first:
                self.move_to(x, y)
        time.sleep(random.uniform(0.05, 0.15))

        if button == "left":
            down_flag = MOUSEEVENTF_LEFTDOWN
            up_flag = MOUSEEVENTF_LEFTUP
        elif button == "right":
            down_flag = MOUSEEVENTF_RIGHTDOWN
            up_flag = MOUSEEVENTF_RIGHTUP
        else:
            down_flag = MOUSEEVENTF_MIDDLEDOWN
            up_flag = MOUSEEVENTF_MIDDLEUP

        self._send_mouse_input(0, 0, down_flag)
        time.sleep(random.uniform(0.05, 0.15))
        self._send_mouse_input(0, 0, up_flag)
        time.sleep(random.uniform(0.1, 0.3))

    def scroll(self, amount: int, x=None, y=None, smooth=True):
        if x is not None and y is not None:
            self.move_to(x, y)

        if smooth:
            steps = random.randint(3, 8)
            per_step = amount // steps if amount != 0 else 1
            for _ in range(steps):
                self._send_mouse_input(0, 0, MOUSEEVENTF_WHEEL, per_step * 120)
                time.sleep(random.uniform(0.05, 0.15))
        else:
            self._send_mouse_input(0, 0, MOUSEEVENTF_WHEEL, amount * 120)
            # ═══════════════════════════════════════
# HUMAN KEYBOARD CLASS
# ═══════════════════════════════════════

class HumanKeyboard:
    """
    99% Human-like keyboard control
    Natural typing speed + typos + corrections
    """

    VK_CODES = {
        'a': 0x41, 'b': 0x42, 'c': 0x43, 'd': 0x44,
        'e': 0x45, 'f': 0x46, 'g': 0x47, 'h': 0x48,
        'i': 0x49, 'j': 0x4A, 'k': 0x4B, 'l': 0x4C,
        'm': 0x4D, 'n': 0x4E, 'o': 0x4F, 'p': 0x50,
        'q': 0x51, 'r': 0x52, 's': 0x53, 't': 0x54,
        'u': 0x55, 'v': 0x56, 'w': 0x57, 'x': 0x58,
        'y': 0x59, 'z': 0x5A,
        '0': 0x30, '1': 0x31, '2': 0x32, '3': 0x33,
        '4': 0x34, '5': 0x35, '6': 0x36, '7': 0x37,
        '8': 0x38, '9': 0x39,
        ' ': 0x20, '\n': 0x0D, '\t': 0x09,
        '.': 0xBE, ',': 0xBC, '!': 0x31, '?': 0xBF,
        '-': 0xBD, '_': 0xBD, '#': 0x33, '@': 0x32,
        ':': 0xBA, ';': 0xBA,
        'backspace': 0x08, 'enter': 0x0D,
        'shift': 0x10, 'ctrl': 0x11, 'alt': 0x12,
        'tab': 0x09, 'escape': 0x1B,
        'delete': 0x2E, 'home': 0x24, 'end': 0x23,
        'left': 0x25, 'right': 0x27,
        'up': 0x26, 'down': 0x28,
        'f1': 0x70, 'f2': 0x71, 'f3': 0x72,
    }

    SHIFT_CHARS = {
        '!': '1', '@': '2', '#': '3', '$': '4',
        '%': '5', '^': '6', '&': '7', '*': '8',
        '(': '9', ')': '0', '_': '-', '+': '=',
        '{': '[', '}': ']', '|': '\\', ':': ';',
        '"': "'", '<': ',', '>': '.', '?': '/',
        '~': '`',
    }

    NEARBY_KEYS = {
        'a': ['s', 'q', 'w', 'z'],
        'b': ['v', 'n', 'g', 'h'],
        'c': ['x', 'v', 'd', 'f'],
        'd': ['s', 'f', 'e', 'r', 'c'],
        'e': ['w', 'r', 'd', 's'],
        'f': ['d', 'g', 'r', 't', 'v'],
        'g': ['f', 'h', 't', 'y', 'b'],
        'h': ['g', 'j', 'y', 'u', 'n'],
        'i': ['u', 'o', 'k', 'j'],
        'j': ['h', 'k', 'u', 'i', 'n'],
        'k': ['j', 'l', 'i', 'o', 'm'],
        'l': ['k', 'o', 'p'],
        'm': ['n', 'k', 'j'],
        'n': ['b', 'm', 'h', 'j'],
        'o': ['i', 'p', 'k', 'l'],
        'p': ['o', 'l'],
        'q': ['w', 'a'],
        'r': ['e', 't', 'f', 'd'],
        's': ['a', 'd', 'w', 'e', 'z', 'x'],
        't': ['r', 'y', 'g', 'f'],
        'u': ['y', 'i', 'h', 'j'],
        'v': ['c', 'b', 'f', 'g'],
        'w': ['q', 'e', 'a', 's'],
        'x': ['z', 'c', 's', 'd'],
        'y': ['t', 'u', 'g', 'h'],
        'z': ['a', 'x', 's'],
    }

    def __init__(self):
        self.user32 = ctypes.windll.user32
        self.wpm = random.randint(45, 85)
        self.base_delay = 60.0 / (self.wpm * 5)
        self.typo_rate = random.uniform(0.02, 0.05)
        self.burst_mode = False

    def _send_key(self, vk_code: int, key_up: bool = False, scan_code: int = 0):
        flags = KEYEVENTF_KEYUP if key_up else 0
        if scan_code:
            flags |= KEYEVENTF_SCANCODE
        extra = ctypes.c_ulong(0)
        ii_ = _INPUT_UNION()
        ii_.ki = KEYBDINPUT(vk_code, scan_code, flags, 0, ctypes.pointer(extra))
        x = INPUT(INPUT_KEYBOARD, ii_)
        self.user32.SendInput(1, ctypes.pointer(x), ctypes.sizeof(x))

    def _press_key(self, vk_code: int):
        self._send_key(vk_code, False)
        time.sleep(random.uniform(0.04, 0.12))
        self._send_key(vk_code, True)

    def _press_with_shift(self, vk_code: int):
        self._send_key(self.VK_CODES['shift'], False)
        time.sleep(random.uniform(0.02, 0.06))
        self._send_key(vk_code, False)
        time.sleep(random.uniform(0.04, 0.10))
        self._send_key(vk_code, True)
        time.sleep(random.uniform(0.02, 0.06))
        self._send_key(self.VK_CODES['shift'], True)

    def _get_char_delay(self) -> float:
        if self.burst_mode:
            delay = self.base_delay * random.uniform(0.5, 0.8)
        else:
            delay = self.base_delay * random.uniform(0.7, 1.5)
        if random.random() < 0.05:
            delay += random.uniform(0.2, 0.8)
        if random.random() < 0.1:
            delay += random.uniform(0.05, 0.2)
        return max(0.02, delay)

    def _make_typo(self, char: str) -> str:
        lower = char.lower()
        if lower in self.NEARBY_KEYS:
            return random.choice(self.NEARBY_KEYS[lower])
        return char

    def _type_char(self, char: str):
        needs_shift = char.isupper() or char in self.SHIFT_CHARS
        if char in self.SHIFT_CHARS:
            base_char = self.SHIFT_CHARS[char]
        else:
            base_char = char.lower()

        if base_char in self.VK_CODES:
            vk = self.VK_CODES[base_char]
        else:
            vk = win32api.VkKeyScan(char) & 0xFF
            needs_shift = (win32api.VkKeyScan(char) >> 8) & 1

        if needs_shift:
            self._press_with_shift(vk)
        else:
            self._press_key(vk)

    def type_text(self, text: str, make_typos: bool = True, clear_first: bool = False):
        if clear_first:
            self.select_all()
            time.sleep(0.1)

        self.burst_mode = random.random() < 0.2
        i = 0
        while i < len(text):
            char = text[i]
            if (make_typos and random.random() < self.typo_rate and char.isalpha()):
                typo_char = self._make_typo(char)
                self._type_char(typo_char)
                time.sleep(self._get_char_delay())
                time.sleep(random.uniform(0.1, 0.5))
                self._press_key(self.VK_CODES['backspace'])
                time.sleep(random.uniform(0.05, 0.15))
                self._type_char(char)
            else:
                self._type_char(char)

            time.sleep(self._get_char_delay())
            if random.random() < 0.1:
                self.burst_mode = not self.burst_mode
            if char == ' ':
                time.sleep(random.uniform(0.05, 0.2))
            i += 1

    def press_key(self, key: str):
        key = key.lower()
        if key in self.VK_CODES:
            self._press_key(self.VK_CODES[key])
        time.sleep(random.uniform(0.05, 0.15))

    def hotkey(self, *keys):
        vk_codes = []
        for key in keys:
            k = key.lower()
            if k in self.VK_CODES:
                vk_codes.append(self.VK_CODES[k])
        for vk in vk_codes:
            self._send_key(vk, False)
            time.sleep(random.uniform(0.02, 0.05))
        time.sleep(random.uniform(0.05, 0.1))
        for vk in reversed(vk_codes):
            self._send_key(vk, True)
            time.sleep(random.uniform(0.02, 0.05))

    def select_all(self):
        self.hotkey('ctrl', 'a')
        time.sleep(random.uniform(0.05, 0.15))

    def copy(self):
        self.hotkey('ctrl', 'c')
        time.sleep(random.uniform(0.1, 0.2))

    def paste(self):
        self.hotkey('ctrl', 'v')
        time.sleep(random.uniform(0.1, 0.3))

    def press_enter(self):
        time.sleep(random.uniform(0.1, 0.3))
        self._press_key(self.VK_CODES['enter'])
        time.sleep(random.uniform(0.1, 0.2))

    def press_escape(self):
        self._press_key(self.VK_CODES['escape'])
        time.sleep(random.uniform(0.1, 0.2))


# ═══════════════════════════════════════
# HUMAN BEHAVIOR CLASS - MAIN FIX HERE
# ═══════════════════════════════════════

class HumanBehavior:
    """
    FIXED: Mouse ab Chrome window ke andar hi rahega
    har activity mein hwnd pass kiya gaya hai
    """

    def __init__(self):
        self.mouse = HumanMouse()
        self.keyboard = HumanKeyboard()
        # FIXED: Chrome window handle store karne ke liye
        self.chrome_hwnd = None

    def set_chrome_hwnd(self, hwnd: int):
        """FIXED: Chrome window handle set karo"""
        self.chrome_hwnd = hwnd

    def _get_chrome_rect(self):
        """Chrome window ki rect return karo"""
        if self.chrome_hwnd:
            try:
                rect = win32gui.GetWindowRect(self.chrome_hwnd)
                return rect  # (left, top, right, bottom)
            except Exception:
                return None
        return None

    def _ensure_chrome_focus(self):
        """FIXED: Har action se pehle Chrome focus check karo"""
        if self.chrome_hwnd:
            try:
                focused = win32gui.GetForegroundWindow()
                if focused != self.chrome_hwnd:
                    win32gui.SetForegroundWindow(self.chrome_hwnd)
                    time.sleep(random.uniform(0.2, 0.4))
            except Exception:
                pass

    def random_pause(self, min_sec: float = 0.5, max_sec: float = 2.0, reason: str = ""):
        duration = random.uniform(min_sec, max_sec)
        if reason:
            print(f"    [HUMAN] Pausing {duration:.1f}s: {reason}")
        time.sleep(duration)

    def reading_pause(self, text_length: int = 100):
        words = text_length / 5
        wpm = random.uniform(150, 300)
        read_time = (words / wpm) * 60
        read_time *= random.uniform(0.5, 1.2)
        read_time = max(0.5, min(read_time, 8.0))
        time.sleep(read_time)

    def human_scroll_down(self, amount: int = None, steps: int = None):
        """FIXED: Scroll se pehle Chrome focus ensure karo"""
        self._ensure_chrome_focus()

        if amount is None:
            amount = random.randint(3, 8)
        if steps is None:
            steps = random.randint(3, 6)

        per_step = max(1, amount // steps)

        for i in range(steps):
            step_amount = per_step + random.randint(-1, 1)
            self.mouse.scroll(-step_amount)
            time.sleep(random.uniform(0.3, 1.5))

            if random.random() < 0.3:
                self.reading_pause(random.randint(50, 200))

            # FIXED: micro move bhi window ke andar
            if random.random() < 0.4:
                self.mouse.random_micro_move(hwnd=self.chrome_hwnd)

    def human_scroll_up(self, amount: int = None):
        """FIXED: Chrome focus ensure karo"""
        self._ensure_chrome_focus()

        if amount is None:
            amount = random.randint(2, 5)

        steps = random.randint(2, 4)
        per_step = max(1, amount // steps)

        for i in range(steps):
            self.mouse.scroll(per_step)
            time.sleep(random.uniform(0.2, 0.8))

    def simulate_reading(self, duration: float = None):
        """FIXED: Reading simulation bhi window ke andar"""
        self._ensure_chrome_focus()

        if duration is None:
            duration = random.uniform(5, 20)

        start = time.time()
        while time.time() - start < duration:
            action = random.choices(
                ['scroll', 'pause', 'micro_move', 'read'],
                weights=[40, 30, 20, 10]
            )[0]

            if action == 'scroll':
                self._ensure_chrome_focus()
                self.mouse.scroll(-random.randint(1, 3))
                time.sleep(random.uniform(0.3, 1.0))

            elif action == 'pause':
                time.sleep(random.uniform(0.5, 2.0))

            elif action == 'micro_move':
                # FIXED: hwnd pass kiya
                self.mouse.random_micro_move(hwnd=self.chrome_hwnd)
                time.sleep(random.uniform(0.2, 0.5))

            elif action == 'read':
                self.reading_pause(random.randint(100, 500))

    def pre_upload_warmup(self, duration: int = None):
        """
        MAIN FIX: Mouse ab Chrome window se bahar nahi jayega
        - Chrome focus har activity se pehle check hota hai
        - Mouse sirf Chrome window ke andar move karta hai
        - look_around bhi window-relative coordinates use karta hai
        """
        if duration is None:
            duration = random.randint(15, 45)

        print(f"    [HUMAN] 👻 Ghost scrolling: {duration}s")

        # FIXED: Pehle Chrome rect check karo
        rect = self._get_chrome_rect()
        if not rect:
            print("    [HUMAN] ⚠️ Chrome window not found, skipping warmup")
            return

        left, top, right, bottom = rect
        win_w = right - left
        win_h = bottom - top

        # FIXED: Chrome window ke safe bounds
        safe_left   = left   + 80
        safe_right  = right  - 80
        safe_top    = top    + 120  # Navbar skip karo
        safe_bottom = bottom - 100

        start = time.time()
        while time.time() - start < duration:
            remaining = duration - (time.time() - start)
            if remaining < 2:
                break

            # FIXED: Har activity se pehle Chrome focus
            self._ensure_chrome_focus()

            activity = random.choices(
                [
                    'scroll_feed',
                    'micro_move',
                    'pause',
                    'scroll_up',
                    'look_around'   # FIXED
                ],
                weights=[40, 20, 20, 10, 10]
            )[0]

            if activity == 'scroll_feed':
                # FIXED: Focus ensure karo phir scroll
                self._ensure_chrome_focus()
                scroll_amt = random.randint(2, 5)
                self.mouse.scroll(-scroll_amt)
                time.sleep(random.uniform(1.0, 3.0))

            elif activity == 'micro_move':
                # FIXED: hwnd pass kiya - window ke andar rahega
                self.mouse.random_micro_move(hwnd=self.chrome_hwnd)
                time.sleep(random.uniform(0.3, 1.0))

            elif activity == 'pause':
                time.sleep(random.uniform(1.0, 3.0))

            elif activity == 'scroll_up':
                self._ensure_chrome_focus()
                self.mouse.scroll(random.randint(1, 3))
                time.sleep(random.uniform(0.5, 1.5))

            elif activity == 'look_around':
                # ✅ MAIN FIX: Pehle SCREEN coords use hote the
                # Ab Chrome window ke andar hi move karega
                if safe_right > safe_left and safe_bottom > safe_top:
                    x = random.randint(safe_left, safe_right)
                    y = random.randint(safe_top, safe_bottom)
                    self.mouse.move_to(
                        x, y,
                        duration=random.uniform(0.5, 1.5),
                        hwnd=self.chrome_hwnd   # FIXED: hwnd pass kiya
                    )
                    time.sleep(random.uniform(0.5, 2.0))

        print("    [HUMAN] ✅ Warmup complete")

    def natural_click_area(self, x: int, y: int, width: int = 10, height: int = 10):
        click_x = x + random.randint(-width//2, width//2)
        click_y = y + random.randint(-height//2, height//2)
        self.mouse.move_to(click_x, click_y)
        time.sleep(random.uniform(0.1, 0.3))
        self.mouse.click()

    def open_file_dialog_and_select(self, file_path: str) -> bool:
        import pyperclip
        print(f"    [HUMAN] 📁 Selecting file via OS dialog")
        pyperclip.copy(file_path)
        time.sleep(random.uniform(0.3, 0.6))
        time.sleep(random.uniform(1.5, 2.5))
        self.keyboard.hotkey('ctrl', 'l')
        time.sleep(random.uniform(0.3, 0.6))
        self.keyboard.paste()
        time.sleep(random.uniform(0.5, 1.0))
        self.keyboard.press_enter()
        time.sleep(random.uniform(1.0, 2.0))
        print("    [HUMAN] ✅ File selected")
        return True
        # ═══════════════════════════════════════
# WINDOW CONTROLLER CLASS
# ═══════════════════════════════════════

class WindowController:
    """
    Windows window management
    Find, focus, resize Chrome window
    FIXED: Chrome hwnd properly track hota hai
    """

    def __init__(self):
        self.mouse = HumanMouse()

    def find_window(
        self,
        title_contains: str = None,
        class_name: str = None
    ) -> Optional[int]:
        """Window handle find karo"""
        found_hwnd = None

        def enum_callback(hwnd, _):
            nonlocal found_hwnd
            if not win32gui.IsWindowVisible(hwnd):
                return True

            window_title = win32gui.GetWindowText(hwnd)
            window_class = win32gui.GetClassName(hwnd)

            title_match = (
                title_contains is None or
                title_contains.lower() in
                window_title.lower()
            )
            class_match = (
                class_name is None or
                class_name.lower() in
                window_class.lower()
            )

            if title_match and class_match:
                found_hwnd = hwnd
                return False
            return True

        win32gui.EnumWindows(enum_callback, None)
        return found_hwnd

    def find_chrome_window(
        self, profile_path: str = None
    ) -> Optional[int]:
        """
        Chrome window find karo
        FIXED: Best visible Chrome window return karta hai
        """
        chrome_hwnds = []

        def enum_callback(hwnd, _):
            if not win32gui.IsWindowVisible(hwnd):
                return True
            try:
                class_name = win32gui.GetClassName(hwnd)
                title = win32gui.GetWindowText(hwnd)
                # FIXED: Sirf main Chrome windows lo
                # (background processes skip karo)
                if ('chrome' in class_name.lower() and
                        len(title) > 0):
                    chrome_hwnds.append(hwnd)
            except Exception:
                pass
            return True

        win32gui.EnumWindows(enum_callback, None)

        if not chrome_hwnds:
            return None

        # FIXED: Sabse badi window return karo
        # (maximize hogi to content area zyada hoga)
        best_hwnd = None
        best_area = 0
        for hwnd in chrome_hwnds:
            try:
                rect = win32gui.GetWindowRect(hwnd)
                if rect:
                    area = (rect[2]-rect[0]) * (rect[3]-rect[1])
                    if area > best_area:
                        best_area = area
                        best_hwnd = hwnd
            except Exception:
                pass

        return best_hwnd

    def focus_window(self, hwnd: int) -> bool:
        """
        Window focus karo
        FIXED: Multiple attempts + verify karta hai
        """
        if not hwnd:
            return False

        try:
            # Minimized hai to restore karo
            if win32gui.IsIconic(hwnd):
                win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
                time.sleep(random.uniform(0.3, 0.6))

            # Foreground mein lao
            win32gui.SetForegroundWindow(hwnd)
            time.sleep(random.uniform(0.2, 0.4))

            # FIXED: Agar focus na mile to 3 baar try karo
            for attempt in range(3):
                focused = win32gui.GetForegroundWindow()
                if focused == hwnd:
                    return True
                # Alt trick se focus force karo
                win32api.keybd_event(0x12, 0, 0, 0)       # Alt down
                win32gui.SetForegroundWindow(hwnd)
                win32api.keybd_event(0x12, 0, 0x0002, 0)  # Alt up
                time.sleep(0.2)

            return win32gui.GetForegroundWindow() == hwnd

        except Exception as e:
            print(f"    [WIN] Focus error: {e}")
            return False

    def get_window_rect(
        self, hwnd: int
    ) -> Optional[Tuple[int, int, int, int]]:
        """
        Window rectangle get karo
        Returns: (left, top, right, bottom)
        """
        try:
            if not hwnd:
                return None
            return win32gui.GetWindowRect(hwnd)
        except Exception:
            return None

    def get_window_center(
        self, hwnd: int
    ) -> Optional[Tuple[int, int]]:
        """Window center coordinates"""
        rect = self.get_window_rect(hwnd)
        if rect:
            cx = (rect[0] + rect[2]) // 2
            cy = (rect[1] + rect[3]) // 2
            return cx, cy
        return None

    def maximize_window(self, hwnd: int):
        """Window maximize karo"""
        try:
            win32gui.ShowWindow(hwnd, win32con.SW_MAXIMIZE)
            time.sleep(random.uniform(0.3, 0.7))
        except Exception:
            pass

    def get_process_windows(
        self, process_name: str
    ) -> List[int]:
        """Process ke saare windows find karo"""
        hwnds = []

        def enum_callback(hwnd, _):
            if not win32gui.IsWindowVisible(hwnd):
                return True
            try:
                _, pid = win32process.GetWindowThreadProcessId(hwnd)
                import psutil
                proc = psutil.Process(pid)
                if process_name.lower() in proc.name().lower():
                    hwnds.append(hwnd)
            except Exception:
                pass
            return True

        win32gui.EnumWindows(enum_callback, None)
        return hwnds

    def wait_for_window(
        self,
        title_contains: str,
        timeout: int = 30,
        check_interval: float = 0.5
    ) -> Optional[int]:
        """Window appear hone ka wait karo"""
        start = time.time()
        while time.time() - start < timeout:
            hwnd = self.find_window(title_contains)
            if hwnd:
                return hwnd
            time.sleep(check_interval)
        return None

    def click_in_window(
        self,
        hwnd: int,
        rel_x: float,
        rel_y: float
    ):
        """
        Window ke relative coordinates pe click
        FIXED: Boundary check add kiya
        rel_x, rel_y: 0.0 to 1.0
        """
        rect = self.get_window_rect(hwnd)
        if not rect:
            return

        win_w = rect[2] - rect[0]
        win_h = rect[3] - rect[1]

        abs_x = rect[0] + int(win_w * rel_x)
        abs_y = rect[1] + int(win_h * rel_y)

        # FIXED: Boundary clamp karo
        abs_x = max(rect[0] + 10, min(abs_x, rect[2] - 10))
        abs_y = max(rect[1] + 10, min(abs_y, rect[3] - 10))

        # Natural offset
        abs_x += random.randint(-3, 3)
        abs_y += random.randint(-3, 3)

        self.mouse.click(abs_x, abs_y)


# ═══════════════════════════════════════
# HUMAN FACEBOOK UPLOADER CLASS
# ═══════════════════════════════════════

class HumanFacebookUploader:
    """
    Full Human Simulation Facebook Uploader
    FIXED: Chrome hwnd properly set hota hai
           HumanBehavior ko hwnd pass kiya jaata hai
    """

    def __init__(self, chrome_path: str):
        self.chrome_path = chrome_path
        self.mouse = HumanMouse()
        self.keyboard = HumanKeyboard()
        self.behavior = HumanBehavior()
        self.window = WindowController()
        self.chrome_hwnd = None
        self.ui_log = print

    def set_logger(self, log_func):
        """Logger set karo"""
        self.ui_log = log_func

    def _log(self, msg: str):
        self.ui_log(f"    [WIN32] {msg}")

    def _update_behavior_hwnd(self):
        """
        FIXED: Jab bhi chrome_hwnd update ho
        HumanBehavior ko bhi bata do
        """
        if self.chrome_hwnd:
            self.behavior.set_chrome_hwnd(self.chrome_hwnd)

    def launch_chrome(self) -> bool:
        """Chrome launch karo with profile"""
        import subprocess
        import psutil
        import os

        self._log("🚀 Launching Chrome...")

        base = os.path.basename(
            os.path.normpath(self.chrome_path)
        )
        parent = os.path.dirname(
            os.path.normpath(self.chrome_path)
        )

        if (base.lower() == "default" or
                base.lower().startswith("profile")):
            user_data = parent
            profile = base
        else:
            user_data = self.chrome_path
            profile = "Default"

        chrome_paths = [
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
            r"C:\Users\{}\AppData\Local\Google\Chrome\Application\chrome.exe".format(
                os.environ.get('USERNAME', '')
            ),
        ]

        chrome_exe = None
        for cp in chrome_paths:
            if os.path.exists(cp):
                chrome_exe = cp
                break

        if not chrome_exe:
            self._log("❌ Chrome not found!")
            return False

        self._kill_profile_chrome(user_data)
        time.sleep(random.uniform(2, 3))

        cmd = [
            chrome_exe,
            f"--user-data-dir={user_data}",
            f"--profile-directory={profile}",
            "--start-maximized",
            "--no-first-run",
            "--no-default-browser-check",
            "--disable-notifications",
            "https://www.facebook.com"
        ]

        subprocess.Popen(cmd)
        self._log("⏳ Waiting for Chrome...")

        time.sleep(random.uniform(3, 5))

        # FIXED: find_chrome_window use karo (better detection)
        self.chrome_hwnd = self.window.find_chrome_window()

        if not self.chrome_hwnd:
            # Fallback: title se dhundo
            self.chrome_hwnd = self.window.wait_for_window(
                "Chrome", timeout=30
            )

        if not self.chrome_hwnd:
            self._log("❌ Chrome window not found!")
            return False

        # FIXED: HumanBehavior ko hwnd do
        self._update_behavior_hwnd()

        self.window.focus_window(self.chrome_hwnd)
        self.window.maximize_window(self.chrome_hwnd)
        time.sleep(random.uniform(2, 3))

        self._log(f"✅ Chrome launched! HWND: {self.chrome_hwnd}")
        return True

    def _kill_profile_chrome(self, user_data: str):
        """Profile ke Chrome processes kill karo"""
        import psutil
        killed = 0
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                if 'chrome' in proc.info['name'].lower():
                    cmdline = ' '.join(
                        proc.info.get('cmdline', [])
                    )
                    if user_data.lower() in cmdline.lower():
                        proc.kill()
                        killed += 1
            except Exception:
                pass
        if killed:
            self._log(f"🔴 Killed {killed} Chrome process(es)")

    def navigate_to_url(self, url: str, wait: float = 3.0):
        """URL navigate karo via address bar"""
        if not self.chrome_hwnd:
            return

        # FIXED: Focus verify karo
        self.window.focus_window(self.chrome_hwnd)
        time.sleep(random.uniform(0.3, 0.6))

        self.keyboard.hotkey('ctrl', 'l')
        time.sleep(random.uniform(0.3, 0.6))

        import pyperclip
        pyperclip.copy(url)
        self.keyboard.paste()
        time.sleep(random.uniform(0.2, 0.4))

        self.keyboard.press_enter()
        self._log(f"🌐 Navigating: {url}")

        time.sleep(wait + random.uniform(0, 2))

        # FIXED: Navigate ke baad hwnd refresh karo
        new_hwnd = self.window.find_chrome_window()
        if new_hwnd:
            self.chrome_hwnd = new_hwnd
            self._update_behavior_hwnd()

    def do_warmup(self, config: dict):
        """
        FIXED: Warmup ab Chrome hwnd ke saath kaam karta hai
        Mouse window se bahar nahi jayega
        """
        if not config.get('enabled', True):
            return

        if not self.chrome_hwnd:
            self._log("⚠️ No Chrome window for warmup!")
            return

        # FIXED: Focus pehle
        self.window.focus_window(self.chrome_hwnd)
        time.sleep(random.uniform(0.5, 1.0))

        # FIXED: hwnd update karo behavior mein
        self._update_behavior_hwnd()

        min_sec = config.get('min', 15)
        max_sec = config.get('max', 45)
        duration = random.randint(min_sec, max_sec)

        self._log(f"👻 Human warmup: {duration}s (window-locked)")

        # FIXED: pre_upload_warmup ab window ke andar rahega
        self.behavior.pre_upload_warmup(duration)

    def find_and_click_create_post(self) -> bool:
        """Create Post button dhundo aur click karo"""
        self._log("🔍 Finding 'Create Post' button...")

        if not self.chrome_hwnd:
            return False

        # FIXED: Focus ensure karo
        self.window.focus_window(self.chrome_hwnd)
        rect = self.window.get_window_rect(self.chrome_hwnd)
        if not rect:
            return False

        win_w = rect[2] - rect[0]
        win_h = rect[3] - rect[1]

        positions = [
            (0.15, 0.12),
            (0.20, 0.15),
            (0.12, 0.20),
            (0.50, 0.10),
        ]

        for rel_x, rel_y in positions:
            abs_x = rect[0] + int(win_w * rel_x)
            abs_y = rect[1] + int(win_h * rel_y)
            abs_x += random.randint(-5, 5)
            abs_y += random.randint(-5, 5)

            # FIXED: Clamp to window
            abs_x = max(rect[0]+10, min(abs_x, rect[2]-10))
            abs_y = max(rect[1]+10, min(abs_y, rect[3]-10))

            self._log(f"   Trying position: ({rel_x}, {rel_y})")
            self.mouse.click(abs_x, abs_y)
            time.sleep(random.uniform(1.5, 2.5))

            if self._check_composer_open():
                self._log("✅ Composer opened!")
                return True

        return False

    def _check_composer_open(self) -> bool:
        """Post composer open hua check karo"""
        if not self.chrome_hwnd:
            return False
        try:
            title = win32gui.GetWindowText(self.chrome_hwnd)
            keywords = ['create', 'post', 'compose', 'write', 'publish']
            return any(kw in title.lower() for kw in keywords)
        except Exception:
            return False

    def attach_video_file(self, file_path: str) -> bool:
        """Video file attach karo"""
        import os
        self._log(f"📎 Attaching: {os.path.basename(file_path)}")

        if not os.path.exists(file_path):
            self._log("❌ File not found!")
            return False

        import pyperclip
        pyperclip.copy(file_path)

        if not self.chrome_hwnd:
            return False

        # FIXED: Focus pehle
        self.window.focus_window(self.chrome_hwnd)
        rect = self.window.get_window_rect(self.chrome_hwnd)
        if not rect:
            return False

        win_w = rect[2] - rect[0]
        win_h = rect[3] - rect[1]

        photo_positions = [
            (0.12, 0.45),
            (0.15, 0.50),
            (0.10, 0.55),
            (0.20, 0.45),
        ]

        for rel_x, rel_y in photo_positions:
            abs_x = rect[0] + int(win_w * rel_x)
            abs_y = rect[1] + int(win_h * rel_y)

            # FIXED: Clamp to window
            abs_x = max(rect[0]+10, min(abs_x, rect[2]-10))
            abs_y = max(rect[1]+10, min(abs_y, rect[3]-10))

            self.mouse.click(abs_x, abs_y)
            time.sleep(random.uniform(1.5, 3.0))

            dialog_hwnd = self.window.wait_for_window("Open", timeout=5)
            if dialog_hwnd:
                self._log("📁 File dialog opened!")
                self.window.focus_window(dialog_hwnd)
                time.sleep(random.uniform(0.5, 1.0))

                self.keyboard.hotkey('ctrl', 'l')
                time.sleep(random.uniform(0.3, 0.5))

                self.keyboard.type_text(file_path, make_typos=False)
                time.sleep(random.uniform(0.3, 0.5))

                self.keyboard.press_enter()
                time.sleep(random.uniform(2, 4))

                # FIXED: Dialog close hone ke baad Chrome focus wapas lo
                self.window.focus_window(self.chrome_hwnd)
                self._update_behavior_hwnd()

                self._log("✅ File attached!")
                return True

        self._log("❌ Could not find file button!")
        return False

    def type_caption(self, caption: str) -> bool:
        """Caption type karo human-like"""
        self._log("✍️  Typing caption...")

        if not self.chrome_hwnd:
            return False

        # FIXED: Focus ensure karo
        self.window.focus_window(self.chrome_hwnd)
        rect = self.window.get_window_rect(self.chrome_hwnd)
        if not rect:
            return False

        win_w = rect[2] - rect[0]
        win_h = rect[3] - rect[1]

        caption_positions = [
            (0.50, 0.35),
            (0.50, 0.40),
            (0.45, 0.38),
            (0.55, 0.35),
        ]

        for rel_x, rel_y in caption_positions:
            abs_x = rect[0] + int(win_w * rel_x)
            abs_y = rect[1] + int(win_h * rel_y)

            # FIXED: Clamp to window
            abs_x = max(rect[0]+10, min(abs_x, rect[2]-10))
            abs_y = max(rect[1]+10, min(abs_y, rect[3]-10))

            self.mouse.click(abs_x, abs_y)
            time.sleep(random.uniform(0.5, 1.0))
            break

        self.keyboard.type_text(caption, make_typos=True)
        time.sleep(random.uniform(0.5, 1.5))

        self._log("✅ Caption typed!")
        return True

    def click_publish(self) -> bool:
        """Publish/Share button click karo"""
        self._log("🚀 Clicking Publish...")

        if not self.chrome_hwnd:
            return False

        # FIXED: Focus ensure karo
        self.window.focus_window(self.chrome_hwnd)
        rect = self.window.get_window_rect(self.chrome_hwnd)
        if not rect:
            return False

        win_w = rect[2] - rect[0]
        win_h = rect[3] - rect[1]

        publish_positions = [
            (0.85, 0.90),
            (0.80, 0.88),
            (0.90, 0.92),
            (0.75, 0.90),
        ]

        for rel_x, rel_y in publish_positions:
            abs_x = rect[0] + int(win_w * rel_x)
            abs_y = rect[1] + int(win_h * rel_y)

            # FIXED: Clamp to window
            abs_x = max(rect[0]+10, min(abs_x, rect[2]-10))
            abs_y = max(rect[1]+10, min(abs_y, rect[3]-10))

            time.sleep(random.uniform(0.5, 1.5))
            self.mouse.click(abs_x, abs_y)
            time.sleep(random.uniform(2.0, 4.0))

            if self._check_published():
                self._log("✅ Published!")
                return True

        return False

    def _check_published(self) -> bool:
        """Post published hua verify karo"""
        if not self.chrome_hwnd:
            return False
        try:
            title = win32gui.GetWindowText(self.chrome_hwnd)
            success_keywords = ['published', 'posted', 'shared', 'live', 'success']
            return any(kw in title.lower() for kw in success_keywords)
        except Exception:
            return False

    def dismiss_popup(self) -> bool:
        """Popup dismiss karo"""
        self._log("🔍 Checking for popups...")

        if not self.chrome_hwnd:
            return False

        # FIXED: Focus ensure karo
        self.window.focus_window(self.chrome_hwnd)
        rect = self.window.get_window_rect(self.chrome_hwnd)
        if not rect:
            return False

        win_w = rect[2] - rect[0]
        win_h = rect[3] - rect[1]

        self.keyboard.press_escape()
        time.sleep(random.uniform(0.5, 1.0))

        dismiss_positions = [
            (0.50, 0.65),
            (0.45, 0.68),
            (0.55, 0.62),
        ]

        for rel_x, rel_y in dismiss_positions:
            abs_x = rect[0] + int(win_w * rel_x)
            abs_y = rect[1] + int(win_h * rel_y)

            # FIXED: Clamp to window
            abs_x = max(rect[0]+10, min(abs_x, rect[2]-10))
            abs_y = max(rect[1]+10, min(abs_y, rect[3]-10))

            self.mouse.click(abs_x, abs_y)
            time.sleep(random.uniform(0.5, 1.0))

        return True

    def upload_video(
        self,
        file_path: str,
        caption: str,
        page_name: str = "",
        warmup_config: dict = None,
        schedule_time: str = "NOW",
        ui_log=None
    ) -> bool:
        """Full upload flow - Human simulation end-to-end"""
        if ui_log:
            self.ui_log = ui_log

        self._log("=" * 50)
        self._log("🤖 HUMAN WIN32 UPLOADER STARTED")
        self._log("=" * 50)

        try:
            # Step 1: Chrome launch
            if not self.launch_chrome():
                return False

            # Step 2: Navigate to Business Suite
            self.navigate_to_url(
                "https://business.facebook.com/latest/home",
                wait=random.uniform(4, 7)
            )

            # Step 3: Human warmup
            # FIXED: hwnd properly set hai warmup se pehle
            if warmup_config:
                self.do_warmup(warmup_config)

            # Step 4: Create Post
            self._log("📝 Opening post composer...")
            if not self.find_and_click_create_post():
                self._log("⚠️ Trying direct URL approach...")
                self.navigate_to_url(
                    "https://business.facebook.com/latest/composer/post/",
                    wait=random.uniform(3, 5)
                )

            time.sleep(random.uniform(2, 4))

            # Step 5: Attach video
            if not self.attach_video_file(file_path):
                self._log("❌ File attach failed!")
                return False

            # Video upload wait
            self._log("⏳ Waiting for video upload...")
            time.sleep(random.uniform(15, 30))

            # Step 6: Type caption
            if caption:
                self.type_caption(caption)

            # Step 7: Human pause
            self._log("🤔 Human thinking pause...")
            time.sleep(random.uniform(2, 5))

            # Step 8: Publish
            if not self.click_publish():
                self._log("❌ Publish failed!")
                return False

            # Step 9: Dismiss popups
            time.sleep(random.uniform(2, 4))
            self.dismiss_popup()

            self._log("🎉 UPLOAD COMPLETE!")
            return True

        except Exception as e:
            self._log(f"❌ CRITICAL ERROR: {e}")
            import traceback
            traceback.print_exc()
            return False


# ═══════════════════════════════════════
# QUICK TEST
# ═══════════════════════════════════════

def test_human_mouse():
    """Quick mouse test"""
    print("[TEST] Human Mouse Test")
    mouse = HumanMouse()

    print(f"  Screen: {SCREEN_W}x{SCREEN_H}")
    print("  Moving to center...")
    mouse.move_to(SCREEN_W // 2, SCREEN_H // 2)
    time.sleep(0.5)

    print("  Scrolling...")
    mouse.scroll(-3)
    time.sleep(0.5)

    print("  Random micro move (screen)...")
    mouse.random_micro_move()

    print("[TEST] ✅ Done!")


def test_warmup_in_window():
    """
    FIXED: Warmup test Chrome window ke andar
    """
    print("[TEST] Warmup Window Test")

    wc = WindowController()
    behavior = HumanBehavior()

    # Chrome window dhundo
    hwnd = wc.find_chrome_window()
    if not hwnd:
        print("[TEST] ❌ Chrome window not found!")
        print("[TEST] Please open Chrome first.")
        return

    print(f"[TEST] ✅ Chrome found! HWND: {hwnd}")
    rect = wc.get_window_rect(hwnd)
    print(f"[TEST] Window rect: {rect}")

    # FIXED: hwnd set karo
    behavior.set_chrome_hwnd(hwnd)
    wc.focus_window(hwnd)
    time.sleep(0.5)

    print("[TEST] Starting 10s warmup (mouse stays in Chrome)...")
    behavior.pre_upload_warmup(duration=10)
    print("[TEST] ✅ Warmup done! Mouse stayed in Chrome!")


if __name__ == "__main__":
    print("=" * 55)
    print("Human Control System V2.0 - FIXED")
    print("=" * 55)
    print("\n1. Basic mouse test")
    print("2. Warmup in Chrome window test")
    choice = input("\nChoice (1/2): ").strip()

    if choice == "1":
        test_human_mouse()
    elif choice == "2":
        test_warmup_in_window()
    else:
        test_human_mouse()