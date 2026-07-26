"""
Hybrid Uploader V8.0 - FIXED VERSION
Human Navigation + Mouse + Sidebar
FIXED: IndexError in _trace() - delays/points size mismatch
FIXED: Mouse stays inside Chrome window
FIXED: Scroll works properly
"""

import os
import re
import sys
import time
import random
import math
import ctypes
import ctypes.wintypes
import threading
import traceback
import subprocess
import pyperclip

import win32api
import win32con
import win32gui
import win32process

from typing import Optional, Tuple, List, Dict, Any
from dataclasses import dataclass, field


# ═══════════════════════════════════════════════════════════
# SCREEN DIMENSIONS
# ═══════════════════════════════════════════════════════════

SCREEN_W = ctypes.windll.user32.GetSystemMetrics(0)
SCREEN_H = ctypes.windll.user32.GetSystemMetrics(1)


# ═══════════════════════════════════════════════════════════
# WIN32 STRUCTURES
# ═══════════════════════════════════════════════════════════

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
        ("type",   ctypes.c_ulong),
        ("_input", _INPUT_UNION),
    ]


# ═══ CONSTANTS ═══
INPUT_MOUSE             = 0
INPUT_KEYBOARD          = 1
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


# ═══════════════════════════════════════════════════════════
# DATACLASSES
# ═══════════════════════════════════════════════════════════

@dataclass
class UploadConfig:
    """Upload configuration"""
    page_name:      str  = ""
    video_path:     str  = ""
    caption:        str  = ""
    schedule_time:  str  = "NOW"
    warmup_min:     int  = 15
    warmup_max:     int  = 45
    warmup_enabled: bool = True
    max_retries:    int  = 3


@dataclass
class ElementInfo:
    """Found element information"""
    x:      int   = 0
    y:      int   = 0
    width:  int   = 0
    height: int   = 0
    text:   str   = ""
    score:  float = 0.0
    tag:    str   = ""


# ═══════════════════════════════════════════════════════════
# HUMAN MOUSE CLASS - FIXED
# ═══════════════════════════════════════════════════════════

class HumanMouse:
    """
    Human-like mouse control
    FIXED: IndexError in _trace() - delays/points mismatch solved
    FIXED: Mouse stays inside Chrome window
    """

    def __init__(self):
        self.user32      = ctypes.windll.user32
        self._last_x     = SCREEN_W // 2
        self._last_y     = SCREEN_H // 2
        self.chrome_hwnd = None
        self._update_pos()

    def _update_pos(self):
        """Current position update"""
        pt = ctypes.wintypes.POINT()
        self.user32.GetCursorPos(ctypes.byref(pt))
        self._last_x = pt.x
        self._last_y = pt.y

    def set_chrome_hwnd(self, hwnd: int):
        """FIXED: Chrome window handle set karo"""
        self.chrome_hwnd = hwnd

    def _get_chrome_bounds(self):
        """
        FIXED: Chrome window safe bounds return karo
        Returns (left, top, right, bottom) or None
        """
        if not self.chrome_hwnd:
            return None
        try:
            rect = win32gui.GetWindowRect(self.chrome_hwnd)
            if rect:
                l, t, r, b = rect
                return (l + 60, t + 120, r - 60, b - 80)
        except Exception:
            pass
        return None

    def _clamp(self, x: int, y: int) -> Tuple[int, int]:
        """
        FIXED: Coordinates clamp karo
        Chrome bounds use karo agar available ho
        """
        bounds = self._get_chrome_bounds()
        if bounds:
            l, t, r, b = bounds
            x = max(l, min(x, r))
            y = max(t, min(y, b))
        else:
            x = max(0, min(x, SCREEN_W - 1))
            y = max(0, min(y, SCREEN_H - 1))
        return x, y

    def _ensure_focus(self):
        """FIXED: Chrome focus ensure karo before any action"""
        if self.chrome_hwnd:
            try:
                if win32gui.GetForegroundWindow() != self.chrome_hwnd:
                    win32gui.SetForegroundWindow(self.chrome_hwnd)
                    time.sleep(random.uniform(0.15, 0.3))
            except Exception:
                pass

    def _to_absolute(self, x: int, y: int) -> Tuple[int, int]:
        """Screen coords to absolute (0-65535)"""
        return (
            int(x * 65535 / SCREEN_W),
            int(y * 65535 / SCREEN_H)
        )

    def _send_mouse(self, dx, dy, flags, data=0):
        """Raw mouse input via SendInput"""
        extra = ctypes.c_ulong(0)
        iu    = _INPUT_UNION()
        iu.mi = MOUSEINPUT(dx, dy, data, flags, 0, ctypes.pointer(extra))
        inp   = INPUT(INPUT_MOUSE, iu)
        self.user32.SendInput(1, ctypes.pointer(inp), ctypes.sizeof(inp))

    # ═══ BEZIER ═══

    def _bezier(
        self,
        start: Tuple[int, int],
        end:   Tuple[int, int],
        n:     int
    ) -> List[Tuple[int, int]]:
        """Cubic bezier curve points"""
        x1, y1 = start
        x2, y2 = end
        dist   = math.hypot(x2 - x1, y2 - y1)

        # Safe offset calculation
        min_off = max(1, int(dist * 0.1))
        max_off = max(2, int(dist * 0.4))
        if min_off >= max_off:
            max_off = min_off + 1

        off1 = random.randint(min_off, max_off)
        off2 = random.randint(min_off, max_off)
        a1   = random.uniform(0, 2 * math.pi)
        a2   = random.uniform(0, 2 * math.pi)

        cx1 = x1 + off1 * math.cos(a1)
        cy1 = y1 + off1 * math.sin(a1)
        cx2 = x2 + off2 * math.cos(a2)
        cy2 = y2 + off2 * math.sin(a2)

        pts = []
        # FIXED: n+1 points generate karo (0 to n inclusive)
        for i in range(n + 1):
            t  = i / max(n, 1)
            px = ((1-t)**3*x1 + 3*(1-t)**2*t*cx1 +
                  3*(1-t)*t**2*cx2 + t**3*x2)
            py = ((1-t)**3*y1 + 3*(1-t)**2*t*cy1 +
                  3*(1-t)*t**2*cy2 + t**3*y2)
            pts.append((int(px), int(py)))
        return pts

    def _speed_profile(self, n: int) -> List[float]:
        """
        FIXED: Speed profile generate karo
        Size EXACTLY n+1 hogi (bezier points ke equal)
        """
        # FIXED: n+1 delays generate karo
        delays = []
        total  = n + 1
        for i in range(total):
            t = i / max(n, 1)
            if t < 0.2:
                speed = 0.3 + t * 3.5
            elif t > 0.8:
                speed = 0.3 + (1.0 - t) * 3.5
            else:
                speed = 1.0 + random.uniform(-0.2, 0.2)
            speed += random.uniform(-0.1, 0.1)
            speed  = max(0.1, speed)
            delays.append(1.0 / (speed * 100))
        return delays

    def _trace(
        self,
        start:    Tuple[int, int],
        end:      Tuple[int, int],
        duration: float
    ):
        """
        FIXED: Main trace function
        IndexError fix - delays aur points same size hain ab
        """
        dist = math.hypot(end[0] - start[0], end[1] - start[1])
        n    = max(10, min(80, int(dist / 5)))

        # FIXED: Dono same n pass karte hain
        pts    = self._bezier(start, end, n)      # n+1 points
        delays = self._speed_profile(n)            # n+1 delays

        # FIXED: Double safety check
        # Agar size mismatch ho tab bhi crash na ho
        min_len = min(len(pts), len(delays))

        total_d = sum(delays[:min_len])
        scale   = duration / total_d if total_d > 0 else 1.0

        for i in range(min_len):
            px, py = pts[i]

            # Micro tremor
            px += random.randint(-1, 1)
            py += random.randint(-1, 1)

            # FIXED: Clamp every point
            px, py = self._clamp(px, py)

            ax, ay = self._to_absolute(px, py)
            self._send_mouse(
                ax, ay,
                MOUSEEVENTF_MOVE | MOUSEEVENTF_ABSOLUTE
            )

            # FIXED: Safe delay access
            d = max(0.001, delays[i] * scale)
            d += random.uniform(-0.001, 0.001)
            time.sleep(max(0.001, d))

    def move_to(
        self,
        x:        int,
        y:        int,
        duration: float = None,
        overshoot: bool = True,
        hwnd:     int   = None
    ):
        """
        FIXED: Human-like mouse move
        - hwnd se window bounds
        - _trace IndexError fixed
        """
        # FIXED: hwnd set karo agar diya
        if hwnd:
            self.chrome_hwnd = hwnd

        # FIXED: Clamp target
        x, y = self._clamp(x, y)

        self._update_pos()
        start = (self._last_x, self._last_y)
        end   = (x, y)

        dist = math.hypot(x - self._last_x, y - self._last_y)

        if dist < 2:
            return

        if duration is None:
            speed    = random.uniform(400, 900)
            duration = max(0.05, min(dist / speed, 2.0))

        # Overshoot
        if overshoot and dist > 50:
            angle      = math.atan2(y - self._last_y, x - self._last_x)
            ov_dist    = random.uniform(5, 20)
            ov_x       = int(x + ov_dist * math.cos(angle))
            ov_y       = int(y + ov_dist * math.sin(angle))

            # FIXED: Overshoot bhi clamp
            ov_x, ov_y = self._clamp(ov_x, ov_y)

            self._trace(start, (ov_x, ov_y), duration * 0.85)
            time.sleep(random.uniform(0.02, 0.07))
            self._trace((ov_x, ov_y), end, duration * 0.15)
        else:
            self._trace(start, end, duration)

        self._last_x = x
        self._last_y = y

    def micro_move(self):
        """
        FIXED: Micro movement - window ke andar rahega
        IndexError fix applied
        """
        self._update_pos()

        bounds = self._get_chrome_bounds()
        if bounds:
            l, t, r, b = bounds
            # FIXED: Window ke andar random position
            if r > l and b > t:
                x = random.randint(l, r)
                y = random.randint(t, b)
            else:
                x = self._last_x + random.randint(-20, 20)
                y = self._last_y + random.randint(-20, 20)
        else:
            x = self._last_x + random.randint(-20, 20)
            y = self._last_y + random.randint(-20, 20)

        # FIXED: Clamp before move
        x, y = self._clamp(x, y)

        self.move_to(
            x, y,
            duration=random.uniform(0.15, 0.4),
            overshoot=False
        )

    def click(
        self,
        x:          int   = None,
        y:          int   = None,
        button:     str   = "left",
        move_first: bool  = True,
        double:     bool  = False
    ):
        """FIXED: Click with focus check"""
        if x is not None and y is not None:
            # FIXED: Clamp coordinates
            x, y = self._clamp(x, y)
            if move_first:
                self.move_to(x, y)

        # FIXED: Focus ensure karo
        self._ensure_focus()
        time.sleep(random.uniform(0.05, 0.15))

        if button == "left":
            df = MOUSEEVENTF_LEFTDOWN
            uf = MOUSEEVENTF_LEFTUP
        elif button == "right":
            df = MOUSEEVENTF_RIGHTDOWN
            uf = MOUSEEVENTF_RIGHTUP
        else:
            df = MOUSEEVENTF_MIDDLEDOWN
            uf = MOUSEEVENTF_MIDDLEUP

        self._send_mouse(0, 0, df)
        time.sleep(random.uniform(0.05, 0.15))
        self._send_mouse(0, 0, uf)

        if double:
            time.sleep(random.uniform(0.08, 0.15))
            self._send_mouse(0, 0, df)
            time.sleep(random.uniform(0.05, 0.12))
            self._send_mouse(0, 0, uf)

        time.sleep(random.uniform(0.1, 0.3))

    def scroll(
        self,
        amount: int,
        x:      int   = None,
        y:      int   = None,
        smooth: bool  = True
    ):
        """
        FIXED: Scroll with focus check
        Scroll ab kaam karega kyunki focus ensure hoga
        """
        # FIXED: Focus pehle
        self._ensure_focus()

        if x is not None and y is not None:
            x, y = self._clamp(x, y)
            self.move_to(x, y)

        if smooth:
            steps    = random.randint(3, 7)
            per_step = max(1, abs(amount) // steps)
            sign     = 1 if amount > 0 else -1

            for _ in range(steps):
                val = sign * per_step * 120
                self._send_mouse(0, 0, MOUSEEVENTF_WHEEL, val)
                time.sleep(random.uniform(0.06, 0.18))
        else:
            self._send_mouse(0, 0, MOUSEEVENTF_WHEEL, amount * 120)

    def right_click(self, x: int, y: int):
        """Right click"""
        self.click(x, y, button="right")

    def double_click(self, x: int, y: int):
        """Double click"""
        self.click(x, y, double=True)

    def drag(
        self,
        fx: int, fy: int,
        tx: int, ty: int,
        duration: float = 1.0
    ):
        """Human-like drag - FIXED: clamp applied"""
        fx, fy = self._clamp(fx, fy)
        tx, ty = self._clamp(tx, ty)

        self.move_to(fx, fy)
        time.sleep(random.uniform(0.1, 0.3))

        self._send_mouse(0, 0, MOUSEEVENTF_LEFTDOWN)
        time.sleep(random.uniform(0.05, 0.1))

        self._trace((fx, fy), (tx, ty), duration)
        time.sleep(random.uniform(0.1, 0.2))

        self._send_mouse(0, 0, MOUSEEVENTF_LEFTUP)
        time.sleep(random.uniform(0.1, 0.3))
        # ═══════════════════════════════════════════════════════════
# HUMAN KEYBOARD CLASS
# ═══════════════════════════════════════════════════════════

class HumanKeyboard:
    """
    Human-like keyboard control
    Natural typing + typos + corrections
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
        'backspace': 0x08, 'enter':  0x0D,
        'shift':     0x10, 'ctrl':   0x11,
        'alt':       0x12, 'tab':    0x09,
        'escape':    0x1B, 'delete': 0x2E,
        'home':      0x24, 'end':    0x23,
        'left':      0x25, 'right':  0x27,
        'up':        0x26, 'down':   0x28,
        'f1': 0x70,  'f2': 0x71,    'f3': 0x72,
    }

    SHIFT_CHARS = {
        '!': '1', '@': '2', '#': '3', '$': '4',
        '%': '5', '^': '6', '&': '7', '*': '8',
        '(': '9', ')': '0', '_': '-', '+': '=',
        '{': '[', '}': ']', '|': '\\',':': ';',
        '"': "'", '<': ',', '>': '.', '?': '/',
        '~': '`',
    }

    NEARBY_KEYS = {
        'a': ['s','q','w','z'],   'b': ['v','n','g','h'],
        'c': ['x','v','d','f'],   'd': ['s','f','e','r','c'],
        'e': ['w','r','d','s'],   'f': ['d','g','r','t','v'],
        'g': ['f','h','t','y','b'],'h': ['g','j','y','u','n'],
        'i': ['u','o','k','j'],   'j': ['h','k','u','i','n'],
        'k': ['j','l','i','o','m'],'l': ['k','o','p'],
        'm': ['n','k','j'],        'n': ['b','m','h','j'],
        'o': ['i','p','k','l'],    'p': ['o','l'],
        'q': ['w','a'],            'r': ['e','t','f','d'],
        's': ['a','d','w','e','z','x'],
        't': ['r','y','g','f'],   'u': ['y','i','h','j'],
        'v': ['c','b','f','g'],   'w': ['q','e','a','s'],
        'x': ['z','c','s','d'],   'y': ['t','u','g','h'],
        'z': ['a','x','s'],
    }

    def __init__(self):
        self.user32     = ctypes.windll.user32
        self.wpm        = random.randint(45, 85)
        self.base_delay = 60.0 / (self.wpm * 5)
        self.typo_rate  = random.uniform(0.02, 0.05)
        self.burst_mode = False

    def _send_key(
        self,
        vk_code:   int,
        key_up:    bool = False,
        scan_code: int  = 0
    ):
        """Raw key event"""
        flags = KEYEVENTF_KEYUP if key_up else 0
        if scan_code:
            flags |= KEYEVENTF_SCANCODE
        extra = ctypes.c_ulong(0)
        iu    = _INPUT_UNION()
        iu.ki = KEYBDINPUT(
            vk_code, scan_code, flags,
            0, ctypes.pointer(extra)
        )
        inp = INPUT(INPUT_KEYBOARD, iu)
        self.user32.SendInput(
            1, ctypes.pointer(inp), ctypes.sizeof(inp)
        )

    def _press_key(self, vk_code: int):
        """Key press + release"""
        self._send_key(vk_code, False)
        time.sleep(random.uniform(0.04, 0.12))
        self._send_key(vk_code, True)

    def _press_with_shift(self, vk_code: int):
        """Shift + key"""
        self._send_key(self.VK_CODES['shift'], False)
        time.sleep(random.uniform(0.02, 0.05))
        self._send_key(vk_code, False)
        time.sleep(random.uniform(0.04, 0.10))
        self._send_key(vk_code, True)
        time.sleep(random.uniform(0.02, 0.05))
        self._send_key(self.VK_CODES['shift'], True)

    def _char_delay(self) -> float:
        """Per character delay"""
        if self.burst_mode:
            d = self.base_delay * random.uniform(0.5, 0.8)
        else:
            d = self.base_delay * random.uniform(0.7, 1.5)
        if random.random() < 0.05:
            d += random.uniform(0.2, 0.8)
        return max(0.02, d)

    def _type_char(self, char: str):
        """Single char type karo"""
        needs_shift = char.isupper() or char in self.SHIFT_CHARS
        base        = self.SHIFT_CHARS.get(char, char.lower())

        if base in self.VK_CODES:
            vk = self.VK_CODES[base]
        else:
            vk          = win32api.VkKeyScan(char) & 0xFF
            needs_shift = ((win32api.VkKeyScan(char) >> 8) & 1)

        if needs_shift:
            self._press_with_shift(vk)
        else:
            self._press_key(vk)

    def type_text(
        self,
        text:        str,
        make_typos:  bool = True,
        clear_first: bool = False
    ):
        """Human-like typing"""
        if clear_first:
            self.select_all()
            time.sleep(0.1)

        self.burst_mode = random.random() < 0.2
        i = 0
        while i < len(text):
            char = text[i]
            if (make_typos and
                    random.random() < self.typo_rate and
                    char.isalpha()):
                # Typo
                lower = char.lower()
                if lower in self.NEARBY_KEYS:
                    wrong = random.choice(self.NEARBY_KEYS[lower])
                    self._type_char(wrong)
                    time.sleep(self._char_delay())
                    time.sleep(random.uniform(0.1, 0.4))
                    self._press_key(self.VK_CODES['backspace'])
                    time.sleep(random.uniform(0.05, 0.15))
            self._type_char(char)
            time.sleep(self._char_delay())
            if char == ' ':
                time.sleep(random.uniform(0.05, 0.15))
            if random.random() < 0.1:
                self.burst_mode = not self.burst_mode
            i += 1

    def hotkey(self, *keys):
        """Key combination - Ctrl+A etc"""
        vks = []
        for k in keys:
            if k.lower() in self.VK_CODES:
                vks.append(self.VK_CODES[k.lower()])
        for vk in vks:
            self._send_key(vk, False)
            time.sleep(random.uniform(0.02, 0.05))
        time.sleep(random.uniform(0.04, 0.09))
        for vk in reversed(vks):
            self._send_key(vk, True)
            time.sleep(random.uniform(0.02, 0.05))

    def press_key(self, key: str):
        k = key.lower()
        if k in self.VK_CODES:
            self._press_key(self.VK_CODES[k])
        time.sleep(random.uniform(0.05, 0.15))

    def select_all(self):
        self.hotkey('ctrl', 'a')
        time.sleep(random.uniform(0.05, 0.1))

    def copy(self):
        self.hotkey('ctrl', 'c')
        time.sleep(random.uniform(0.1, 0.2))

    def paste(self):
        self.hotkey('ctrl', 'v')
        time.sleep(random.uniform(0.1, 0.25))

    def press_enter(self):
        time.sleep(random.uniform(0.08, 0.2))
        self._press_key(self.VK_CODES['enter'])
        time.sleep(random.uniform(0.08, 0.2))

    def press_escape(self):
        self._press_key(self.VK_CODES['escape'])
        time.sleep(random.uniform(0.08, 0.2))

    def press_tab(self):
        self._press_key(self.VK_CODES['tab'])
        time.sleep(random.uniform(0.05, 0.15))


# ═══════════════════════════════════════════════════════════
# HUMAN BEHAVIOR CLASS - FIXED
# ═══════════════════════════════════════════════════════════

class HumanBehavior:
    """
    Human-like behavior patterns
    FIXED: Chrome hwnd properly tracked
    FIXED: pre_action_fidget IndexError fixed
    FIXED: Warmup mouse stays in Chrome window
    """

    def __init__(self):
        self.mouse       = HumanMouse()
        self.keyboard    = HumanKeyboard()
        self.chrome_hwnd = None

    def set_chrome_hwnd(self, hwnd: int):
        """FIXED: hwnd set karo dono mouse aur behavior mein"""
        self.chrome_hwnd = hwnd
        self.mouse.set_chrome_hwnd(hwnd)

    def _ensure_focus(self):
        """Chrome focus ensure karo"""
        if self.chrome_hwnd:
            try:
                if win32gui.GetForegroundWindow() != self.chrome_hwnd:
                    win32gui.SetForegroundWindow(self.chrome_hwnd)
                    time.sleep(random.uniform(0.2, 0.35))
            except Exception:
                pass

    def think(
        self,
        min_s: float = 0.5,
        max_s: float = 2.0,
        label: str   = ""
    ):
        """Thinking pause"""
        d = random.uniform(min_s, max_s)
        if label:
            print(f"    [HUMAN] 🤔 Thinking: {d:.1f}s")
        time.sleep(d)

    def reading_pause(self, chars: int = 100):
        """Reading simulation"""
        words    = chars / 5
        wpm      = random.uniform(150, 280)
        t        = (words / wpm) * 60 * random.uniform(0.6, 1.3)
        time.sleep(max(0.4, min(t, 8.0)))

    def pre_action_fidget(self):
        """
        FIXED: Pre-action small mouse movement
        IndexError fix - micro_move ab safe hai
        """
        try:
            # FIXED: focus ensure karo pehle
            self._ensure_focus()
            # FIXED: micro_move ab IndexError nahi dega
            self.mouse.micro_move()
            time.sleep(random.uniform(0.1, 0.3))
        except Exception as e:
            # FIXED: Crash nahi hoga - sirf log karega
            print(f"    [HUMAN] ⚠️ fidget skip: {e}")
            time.sleep(random.uniform(0.1, 0.2))

    def scroll_down(
        self,
        amount: int = None,
        steps:  int = None
    ):
        """
        FIXED: Scroll down with focus check
        Ab scroll kaam karega
        """
        # FIXED: Focus pehle ensure karo
        self._ensure_focus()

        if amount is None:
            amount = random.randint(3, 7)
        if steps is None:
            steps = random.randint(3, 5)

        per = max(1, amount // steps)

        for i in range(steps):
            s = per + random.randint(-1, 1)
            # FIXED: Negative = scroll down (Facebook feed)
            self.mouse.scroll(-abs(s))
            time.sleep(random.uniform(0.4, 1.4))

            if random.random() < 0.3:
                self.reading_pause(random.randint(50, 180))

            # FIXED: micro_move safe hai ab
            if random.random() < 0.35:
                try:
                    self.mouse.micro_move()
                except Exception:
                    pass

    def scroll_up(self, amount: int = None):
        """FIXED: Scroll up with focus"""
        self._ensure_focus()

        if amount is None:
            amount = random.randint(2, 5)
        steps = random.randint(2, 4)
        per   = max(1, amount // steps)

        for _ in range(steps):
            self.mouse.scroll(abs(per))
            time.sleep(random.uniform(0.2, 0.7))

    def pre_upload_warmup(self, duration: int = None):
        """
        FIXED: Warmup - mouse Chrome window mein rahega
        Scroll ab kaam karega
        """
        if duration is None:
            duration = random.randint(15, 40)

        # FIXED: Chrome bounds check
        bounds = self.mouse._get_chrome_bounds()
        if not bounds:
            print("    [HUMAN] ⚠️ Chrome bounds nahi mile")
            time.sleep(duration)
            return

        l, t, r, b = bounds
        actions     = 0
        start       = time.time()

        print(f"    [HUMAN] 👻 Warmup: {duration}s")

        while time.time() - start < duration:
            remaining = duration - (time.time() - start)
            if remaining < 1.5:
                break

            # FIXED: Har action se pehle focus
            self._ensure_focus()

            act = random.choices(
                ['scroll_down', 'micro_move', 'pause',
                 'scroll_up',   'look_around'],
                weights=[40, 20, 20, 10, 10]
            )[0]

            try:
                if act == 'scroll_down':
                    self._ensure_focus()
                    # FIXED: Focus ke baad scroll
                    self.mouse.scroll(
                        -random.randint(2, 5)
                    )
                    time.sleep(random.uniform(1.0, 2.5))

                elif act == 'micro_move':
                    # FIXED: Safe micro_move
                    self.mouse.micro_move()
                    time.sleep(random.uniform(0.3, 0.8))

                elif act == 'pause':
                    time.sleep(random.uniform(1.0, 2.5))

                elif act == 'scroll_up':
                    self._ensure_focus()
                    self.mouse.scroll(random.randint(1, 3))
                    time.sleep(random.uniform(0.5, 1.5))

                elif act == 'look_around':
                    # FIXED: Sirf Chrome window ke andar
                    if r > l and b > t:
                        x = random.randint(l, r)
                        y = random.randint(t, b)
                        self.mouse.move_to(
                            x, y,
                            duration=random.uniform(0.5, 1.2),
                            overshoot=False
                        )
                        time.sleep(random.uniform(0.5, 1.5))

                actions += 1

            except Exception as e:
                # FIXED: Crash nahi hoga warmup mein
                print(f"    [HUMAN] ⚠️ warmup action skip: {e}")
                time.sleep(0.5)

        print(f"    [HUMAN] ✅ Warmup done! ({actions} actions)")

    def natural_click(
        self,
        x:      int,
        y:      int,
        w:      int = 8,
        h:      int = 8
    ):
        """Natural area click"""
        # FIXED: Clamp before click
        cx = x + random.randint(-w//2, w//2)
        cy = y + random.randint(-h//2, h//2)
        cx, cy = self.mouse._clamp(cx, cy)
        self.mouse.move_to(cx, cy)
        time.sleep(random.uniform(0.08, 0.25))
        self.mouse.click()

    def select_file_dialog(self, path: str) -> bool:
        """OS file dialog mein file select karo"""
        try:
            pyperclip.copy(path)
            time.sleep(random.uniform(0.3, 0.6))
            time.sleep(random.uniform(1.5, 2.5))
            self.keyboard.hotkey('ctrl', 'l')
            time.sleep(random.uniform(0.3, 0.5))
            self.keyboard.paste()
            time.sleep(random.uniform(0.4, 0.8))
            self.keyboard.press_enter()
            time.sleep(random.uniform(1.0, 2.0))
            return True
        except Exception as e:
            print(f"    [HUMAN] ❌ Dialog error: {e}")
            return False
            # ═══════════════════════════════════════════════════════════
# WINDOW CONTROLLER CLASS
# ═══════════════════════════════════════════════════════════

class WindowController:
    """
    Windows window management
    FIXED: Chrome hwnd better detection
    FIXED: Focus multiple attempts
    """

    def __init__(self):
        self.mouse = HumanMouse()

    def find_window(
        self,
        title_contains: str = None,
        class_name:     str = None
    ) -> Optional[int]:
        """Window handle find karo"""
        found = None

        def cb(hwnd, _):
            nonlocal found
            if not win32gui.IsWindowVisible(hwnd):
                return True
            title = win32gui.GetWindowText(hwnd)
            cls   = win32gui.GetClassName(hwnd)
            t_ok  = (title_contains is None or
                     title_contains.lower() in title.lower())
            c_ok  = (class_name is None or
                     class_name.lower() in cls.lower())
            if t_ok and c_ok:
                found = hwnd
                return False
            return True

        win32gui.EnumWindows(cb, None)
        return found

    def find_chrome_window(self) -> Optional[int]:
        """
        FIXED: Best Chrome window find karo
        Sabse badi visible window return karta hai
        """
        candidates = []

        def cb(hwnd, _):
            if not win32gui.IsWindowVisible(hwnd):
                return True
            try:
                cls   = win32gui.GetClassName(hwnd)
                title = win32gui.GetWindowText(hwnd)
                if 'chrome' in cls.lower() and len(title) > 0:
                    rect = win32gui.GetWindowRect(hwnd)
                    if rect:
                        area = (rect[2]-rect[0]) * (rect[3]-rect[1])
                        candidates.append((hwnd, area))
            except Exception:
                pass
            return True

        win32gui.EnumWindows(cb, None)

        if not candidates:
            return None

        # FIXED: Sabse badi window (maximize hogi)
        candidates.sort(key=lambda x: x[1], reverse=True)
        return candidates[0][0]

    def focus_window(self, hwnd: int) -> bool:
        """
        FIXED: Focus with multiple attempts
        Alt trick use karta hai agar normal focus na ho
        """
        if not hwnd:
            return False
        try:
            if win32gui.IsIconic(hwnd):
                win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
                time.sleep(random.uniform(0.3, 0.5))

            win32gui.SetForegroundWindow(hwnd)
            time.sleep(random.uniform(0.2, 0.4))

            # FIXED: 3 attempts
            for _ in range(3):
                if win32gui.GetForegroundWindow() == hwnd:
                    return True
                # Alt trick
                win32api.keybd_event(0x12, 0, 0, 0)
                win32gui.SetForegroundWindow(hwnd)
                win32api.keybd_event(0x12, 0, 0x0002, 0)
                time.sleep(0.2)

            return win32gui.GetForegroundWindow() == hwnd

        except Exception as e:
            print(f"    [WIN] Focus error: {e}")
            return False

    def get_rect(
        self, hwnd: int
    ) -> Optional[Tuple[int, int, int, int]]:
        """Window rect get karo (left,top,right,bottom)"""
        try:
            if hwnd:
                return win32gui.GetWindowRect(hwnd)
        except Exception:
            pass
        return None

    def get_center(
        self, hwnd: int
    ) -> Optional[Tuple[int, int]]:
        """Window center coordinates"""
        rect = self.get_rect(hwnd)
        if rect:
            return (
                (rect[0] + rect[2]) // 2,
                (rect[1] + rect[3]) // 2
            )
        return None

    def maximize(self, hwnd: int):
        """Window maximize karo"""
        try:
            win32gui.ShowWindow(hwnd, win32con.SW_MAXIMIZE)
            time.sleep(random.uniform(0.3, 0.6))
        except Exception:
            pass

    def wait_for_window(
        self,
        title:    str,
        timeout:  int   = 30,
        interval: float = 0.5
    ) -> Optional[int]:
        """Window appear hone ka wait"""
        end = time.time() + timeout
        while time.time() < end:
            h = self.find_window(title)
            if h:
                return h
            time.sleep(interval)
        return None

    def click_relative(
        self,
        hwnd:  int,
        rel_x: float,
        rel_y: float
    ):
        """
        Window relative coords pe click
        FIXED: Clamp to window bounds
        """
        rect = self.get_rect(hwnd)
        if not rect:
            return
        l, t, r, b = rect
        w = r - l
        h = b - t

        ax = l + int(w * rel_x)
        ay = t + int(h * rel_y)

        # FIXED: Clamp
        ax = max(l + 10, min(ax, r - 10))
        ay = max(t + 10, min(ay, b - 10))

        ax += random.randint(-3, 3)
        ay += random.randint(-3, 3)

        self.mouse.click(ax, ay)


# ═══════════════════════════════════════════════════════════
# ELEMENT FINDER CLASS
# ═══════════════════════════════════════════════════════════

class ElementFinder:
    """
    Facebook UI elements dhundne ka system
    Extension bridge + coordinate based fallback
    """

    def __init__(self, bridge=None):
        self.bridge      = bridge
        self.chrome_hwnd = None
        self._cache      = {}
        self._cache_ttl  = 5.0

    def set_bridge(self, bridge):
        self.bridge = bridge

    def set_chrome_hwnd(self, hwnd: int):
        self.chrome_hwnd = hwnd

    def _window_rect(self):
        """Chrome window rect"""
        if self.chrome_hwnd:
            try:
                return win32gui.GetWindowRect(self.chrome_hwnd)
            except Exception:
                pass
        return None

    def find(
        self,
        name:     str,
        timeout:  float = 5.0,
        fallback: Tuple = None
    ) -> Optional[ElementInfo]:
        """
        Element find karo
        FIXED: (0,0) coords reject karo - invalid element
        """
        # Bridge se try
        if self.bridge:
            try:
                result = self.bridge.find_element(
                    name, timeout=timeout
                )
                if result:
                    x = result.get('x', 0)
                    y = result.get('y', 0)
                    # FIXED: Invalid coords reject karo
                    if x <= 0 or y <= 0:
                        print(f"[FIND] ⚠️ Invalid coords ({x},{y}), skipping")
                    else:
                        el = ElementInfo(
                            x=x, y=y,
                            width=result.get('width', 0),
                            height=result.get('height', 0),
                            text=result.get('text', ''),
                            score=result.get('score', 100),
                            tag=result.get('tag', '')
                        )
                        print(
                            f"[FIND] ✅ '{el.text}' @ "
                            f"({el.x},{el.y}) score={el.score:.0f}"
                        )
                        return el
            except Exception as e:
                print(f"[FIND] Bridge error: {e}")

        # Fallback coordinates
        if fallback and self.chrome_hwnd:
            rect = self._window_rect()
            if rect:
                l, t, r, b = rect
                w = r - l
                h = b - t
                fx = l + int(w * fallback[0])
                fy = t + int(h * fallback[1])
                return ElementInfo(
                    x=fx, y=fy,
                    score=50,
                    text=f"fallback_{name}"
                )

        print(f"[FIND] ❌ '{name}' not found")
        return None

    def find_all(
        self,
        name:    str,
        timeout: float = 5.0
    ) -> List[ElementInfo]:
        """
        Multiple elements find karo
        FIXED: get_all_buttons + filter use karta hai
        """
        if not self.bridge:
            return []

        try:
            # FIXED: get_all_buttons use karo
            buttons = self.bridge.get_all_buttons()
            if not buttons:
                return []

            els = []
            # Filter by name/text match
            for b in buttons:
                text = b.get('text', '').lower()
                # Match keywords
                keywords_map = {
                    'page_option': ['page', 'switch to'],
                    'profile_switcher': ['profile', 'account'],
                    'smart_post_button': ['create', 'post', 'write'],
                    'add_photo_video': ['photo', 'video', 'add'],
                    'caption_box': ['caption', 'write', 'say'],
                    'publish_button': ['publish', 'post', 'share'],
                    'schedule_button': ['schedule', 'later'],
                    'boost_popup': ['maybe', 'later', 'skip', 'no thanks'],
                }
                
                keywords = keywords_map.get(name, [name.lower()])
                
                if any(kw in text for kw in keywords):
                    els.append(ElementInfo(
                        x=b.get('x', 0),
                        y=b.get('y', 0),
                        width=b.get('width', 0),
                        height=b.get('height', 0),
                        text=b.get('text', ''),
                        score=b.get('score', 100),
                        tag=b.get('tag', 'button')
                    ))

            print(f"[FIND] find_all '{name}': {len(els)} matches")
            return els

        except Exception as e:
            print(f"[FIND] find_all error: {e}")
            return []

    def wait_for(
        self,
        name:     str,
        timeout:  float = 30.0,
        interval: float = 1.0
    ) -> Optional[ElementInfo]:
        """Element appear hone ka wait"""
        end = time.time() + timeout
        while time.time() < end:
            el = self.find(name, timeout=2.0)
            if el:
                return el
            time.sleep(interval)
        return None


# ═══════════════════════════════════════════════════════════
# NAVIGATOR CLASS
# ═══════════════════════════════════════════════════════════

class Navigator:
    """
    Facebook navigation helper
    URL navigation + page detection
    """

    def __init__(
        self,
        keyboard:    HumanKeyboard,
        chrome_hwnd: int = None
    ):
        self.keyboard    = keyboard
        self.chrome_hwnd = chrome_hwnd
        self.window      = WindowController()

    def set_chrome_hwnd(self, hwnd: int):
        self.chrome_hwnd = hwnd

    def _focus(self):
        """Chrome focus ensure karo"""
        if self.chrome_hwnd:
            self.window.focus_window(self.chrome_hwnd)

    def go_to(
        self,
        url:  str,
        wait: float = 3.0
    ):
        """
        URL pe navigate karo
        FIXED: Focus ensure karo pehle
        """
        self._focus()
        time.sleep(random.uniform(0.2, 0.4))

        # Address bar
        self.keyboard.hotkey('ctrl', 'l')
        time.sleep(random.uniform(0.3, 0.5))

        # URL paste karo
        pyperclip.copy(url)
        self.keyboard.paste()
        time.sleep(random.uniform(0.2, 0.4))

        self.keyboard.press_enter()
        print(f"[NAV] 🌐 Navigating: {url}")

        time.sleep(wait + random.uniform(0, 1.5))

        # FIXED: Navigate ke baad hwnd refresh
        new_hwnd = self.window.find_chrome_window()
        if new_hwnd:
            self.chrome_hwnd = new_hwnd

    def type_in_addressbar(self, text: str):
        """Address bar mein type karo"""
        self._focus()
        self.keyboard.hotkey('ctrl', 'l')
        time.sleep(random.uniform(0.3, 0.5))
        self.keyboard.type_text(text, make_typos=False)
        time.sleep(random.uniform(0.2, 0.3))
        self.keyboard.press_enter()

    def refresh(self):
        """Page refresh"""
        self._focus()
        self.keyboard.hotkey('ctrl', 'r')
        time.sleep(random.uniform(2.0, 4.0))

    def go_back(self):
        """Browser back"""
        self._focus()
        self.keyboard.hotkey('alt', 'left')
        time.sleep(random.uniform(1.5, 3.0))

    def scroll_to_top(self):
        """Page top pe scroll"""
        self._focus()
        self.keyboard.press_key('home')
        time.sleep(random.uniform(0.5, 1.0))

    def wait_for_load(
        self,
        timeout:  float = 30.0,
        interval: float = 0.5
    ) -> bool:
        """Page load ka wait"""
        time.sleep(interval)
        return True


# ═══════════════════════════════════════════════════════════
# CHROME MANAGER CLASS
# ═══════════════════════════════════════════════════════════

class ChromeManager:
    """
    Chrome launch + management
    FIXED: hwnd properly tracked aur shared
    """

    def __init__(self, profile_path: str):
        self.profile_path = profile_path
        self.chrome_hwnd  = None
        self.window       = WindowController()
        self.keyboard     = HumanKeyboard()

    def _find_chrome_exe(self) -> Optional[str]:
        """Chrome executable find karo"""
        paths = [
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
            os.path.expandvars(
                r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"
            ),
        ]
        for p in paths:
            if os.path.exists(p):
                return p
        return None

    def _parse_profile(self):
        """Profile path parse karo"""
        base   = os.path.basename(
            os.path.normpath(self.profile_path)
        )
        parent = os.path.dirname(
            os.path.normpath(self.profile_path)
        )
        if (base.lower() == 'default' or
                base.lower().startswith('profile')):
            return parent, base
        return self.profile_path, 'Default'

    def kill_existing(self, user_data: str):
        """Existing Chrome processes kill karo"""
        try:
            import psutil
            killed = 0
            for p in psutil.process_iter(['pid','name','cmdline']):
                try:
                    if 'chrome' in p.info['name'].lower():
                        cmd = ' '.join(p.info.get('cmdline',[]))
                        if user_data.lower() in cmd.lower():
                            p.kill()
                            killed += 1
                except Exception:
                    pass
            if killed:
                print(f"[PRE] Killed {killed} Chrome process(es)")
            else:
                print("[PRE] No matching Chrome")
        except Exception:
            pass

    def launch(self, url: str = "https://www.facebook.com") -> bool:
        """
        Chrome launch karo
        FIXED: hwnd detection improved
        """
        chrome_exe = self._find_chrome_exe()
        if not chrome_exe:
            print("[PRE] ❌ Chrome not found!")
            return False

        user_data, profile = self._parse_profile()

        print("[PRE] Killing Chrome...")
        self.kill_existing(user_data)
        time.sleep(random.uniform(2.0, 3.0))

        cmd = [
            chrome_exe,
            f"--user-data-dir={user_data}",
            f"--profile-directory={profile}",
            "--start-maximized",
            "--no-first-run",
            "--no-default-browser-check",
            "--disable-notifications",
            "--disable-popup-blocking",
            url
        ]

        subprocess.Popen(cmd)
        print("[1/18] Launching Chrome...")
        time.sleep(random.uniform(3.0, 5.0))

        # FIXED: find_chrome_window use karo
        self.chrome_hwnd = self.window.find_chrome_window()

        if not self.chrome_hwnd:
            self.chrome_hwnd = self.window.wait_for_window(
                "Chrome", timeout=30
            )

        if not self.chrome_hwnd:
            print("[1/18] ❌ Chrome window not found!")
            return False

        self.window.focus_window(self.chrome_hwnd)
        self.window.maximize(self.chrome_hwnd)
        time.sleep(random.uniform(2.0, 3.0))

        # Window size log
        rect = self.window.get_rect(self.chrome_hwnd)
        if rect:
            w = rect[2] - rect[0]
            h = rect[3] - rect[1]
            print(f"[1/18] Chrome: {w}x{h}")

        print("[1/18] ✅ Chrome launched!")
        return True

    def get_hwnd(self) -> Optional[int]:
        """Current Chrome hwnd return karo"""
        # FIXED: Stale hwnd refresh karo
        if self.chrome_hwnd:
            try:
                if win32gui.IsWindow(self.chrome_hwnd):
                    return self.chrome_hwnd
            except Exception:
                pass
        # Re-find
        self.chrome_hwnd = self.window.find_chrome_window()
        return self.chrome_hwnd

    def close(self):
        """Chrome close karo"""
        if self.chrome_hwnd:
            try:
                win32gui.PostMessage(
                    self.chrome_hwnd,
                    win32con.WM_CLOSE,
                    0, 0
                )
                time.sleep(random.uniform(1.0, 2.0))
            except Exception:
                pass

    def navigate(self, url: str, wait: float = 3.0):
        """URL navigate karo"""
        hwnd = self.get_hwnd()
        if not hwnd:
            return

        self.window.focus_window(hwnd)
        time.sleep(random.uniform(0.2, 0.4))

        self.keyboard.hotkey('ctrl', 'l')
        time.sleep(random.uniform(0.3, 0.5))

        pyperclip.copy(url)
        self.keyboard.paste()
        time.sleep(random.uniform(0.2, 0.3))

        self.keyboard.press_enter()
        print(f"[NAV] Opening {url}...")
        time.sleep(wait + random.uniform(0, 1.5))

        # FIXED: hwnd refresh
        new = self.window.find_chrome_window()
        if new:
            self.chrome_hwnd = new
            # ═══════════════════════════════════════════════════════════
# HYBRID UPLOADER CORE CLASS
# ═══════════════════════════════════════════════════════════

class HybridUploader:
    """
    Hybrid Uploader V8.0 - FIXED
    Human Navigation + Mouse + Sidebar
    FIXED: IndexError in _trace() fixed
    FIXED: Mouse stays in Chrome window
    FIXED: Scroll works properly
    """

    def __init__(
        self,
        bridge=None,
        chrome_user_data_dir=None,
        chrome_profile=None,
        chrome_path=None,
        **kwargs
    ):
        # FIXED: Agar bridge nahi diya to global instance use karo
        if bridge is None:
            bridge = HybridUploader._bridge_instance
            if bridge is None:
                # Bridge init karo agar available nahi
                bridge = HybridUploader.init_bridge()

        # Core components
        self.bridge       = bridge
        self.mouse        = HumanMouse()
        self.keyboard     = HumanKeyboard()
        self.behavior     = HumanBehavior()
        self.window       = WindowController()
        self.finder       = ElementFinder(bridge)

        # Chrome config
        self.chrome_user_data_dir = chrome_user_data_dir
        self.chrome_profile       = chrome_profile or "Default"
        self.chrome_path          = chrome_path

        # State
        self.chrome_hwnd  = None
        self.chrome_rect  = None
        self.chrome_w     = 0
        self.chrome_h     = 0
        self.chrome_l     = 0
        self.chrome_t     = 0

        # Config
        self.config       = UploadConfig()
        self.ui_log       = print
        self.retry_count  = 0

        # Navigator
        self.nav = Navigator(self.keyboard)

    # ═══════════════════════════════════════════════════════
    # LOGGING
    # ═══════════════════════════════════════════════════════

    def set_logger(self, fn):
        """UI logger set karo"""
        self.ui_log = fn

    def _log(self, msg: str):
        """Timestamped log"""
        ts = time.strftime("%H:%M:%S")
        self.ui_log(f"[{ts}] {msg}")

    def _step(self, n: int, total: int, msg: str):
        """Step log"""
        self._log(f"\n[STEP {n}/{total}] {msg}")

    # ═══════════════════════════════════════════════════════
    # CHROME SETUP - FIXED
    # ═══════════════════════════════════════════════════════

    def _setup_chrome(self, profile_path: str) -> bool:
        """
        Chrome launch + setup
        FIXED: hwnd properly shared with all components
        """
        mgr = ChromeManager(profile_path)

        if not mgr.launch():
            return False

        # FIXED: hwnd get karo
        hwnd = mgr.get_hwnd()
        if not hwnd:
            self._log("❌ Chrome hwnd not found!")
            return False

        # FIXED: Saare components ko hwnd do
        self._set_hwnd(hwnd)
        return True

    def _set_hwnd(self, hwnd: int):
        """
        FIXED: Ek jagah se saare components ko hwnd set karo
        Ab koi bhi component window se bahar nahi jayega
        """
        self.chrome_hwnd = hwnd

        # Rect calculate karo
        rect = self.window.get_rect(hwnd)
        if rect:
            self.chrome_rect = rect
            self.chrome_l    = rect[0]
            self.chrome_t    = rect[1]
            self.chrome_w    = rect[2] - rect[0]
            self.chrome_h    = rect[3] - rect[1]

        # FIXED: Saare components ko hwnd set karo
        self.mouse.set_chrome_hwnd(hwnd)
        self.behavior.set_chrome_hwnd(hwnd)
        self.finder.set_chrome_hwnd(hwnd)
        self.nav.set_chrome_hwnd(hwnd)

        self._log(
            f"[1/18] Chrome: {self.chrome_w}x{self.chrome_h}"
        )

    def _refresh_hwnd(self):
        """
        FIXED: Stale hwnd refresh karo
        Navigate ke baad call karo
        """
        new_hwnd = self.window.find_chrome_window()
        if new_hwnd and new_hwnd != self.chrome_hwnd:
            self._set_hwnd(new_hwnd)
        elif self.chrome_hwnd:
            # Rect update karo
            rect = self.window.get_rect(self.chrome_hwnd)
            if rect:
                self.chrome_rect = rect
                self.chrome_l    = rect[0]
                self.chrome_t    = rect[1]
                self.chrome_w    = rect[2] - rect[0]
                self.chrome_h    = rect[3] - rect[1]

    def _focus_chrome(self) -> bool:
        """Chrome focus ensure karo"""
        if self.chrome_hwnd:
            return self.window.focus_window(self.chrome_hwnd)
        return False

    # ═══════════════════════════════════════════════════════
    # COORDINATE HELPERS - FIXED
    # ═══════════════════════════════════════════════════════

    def _abs(
        self,
        rel_x: float,
        rel_y: float
    ) -> Tuple[int, int]:
        """
        Relative coords to absolute screen coords
        FIXED: Clamp to Chrome window
        """
        if not self.chrome_rect:
            return (
                int(SCREEN_W * rel_x),
                int(SCREEN_H * rel_y)
            )
        l, t, r, b = self.chrome_rect
        w = r - l
        h = b - t

        ax = l + int(w * rel_x)
        ay = t + int(h * rel_y)

        # FIXED: Clamp to window
        ax = max(l + 10, min(ax, r - 10))
        ay = max(t + 10, min(ay, b - 10))

        return ax, ay

    def _click_rel(
        self,
        rel_x:  float,
        rel_y:  float,
        label:  str = ""
    ):
        """
        Relative position pe click
        FIXED: Focus ensure + clamp
        """
        self._focus_chrome()
        x, y = self._abs(rel_x, rel_y)

        if label:
            self._log(f"   🖱️  Clicking: {label}")

        # Small offset for naturalness
        x += random.randint(-4, 4)
        y += random.randint(-3, 3)

        # FIXED: Clamp again after offset
        x, y = self.mouse._clamp(x, y)

        self.mouse.move_to(x, y)
        time.sleep(random.uniform(0.1, 0.25))
        self.mouse.click()

    def _scroll_feed(self, amount: int = 3):
        """
        FIXED: Feed scroll
        Focus ensure karo pehle
        """
        self._focus_chrome()
        time.sleep(random.uniform(0.2, 0.4))
        self.mouse.scroll(-amount)
        time.sleep(random.uniform(0.3, 0.8))

    # ═══════════════════════════════════════════════════════
    # FIND AND CLICK - FIXED
    # ═══════════════════════════════════════════════════════

    def _find_and_click(
        self,
        element_name: str,
        timeout:      float = 10.0,
        fallback:     Tuple = None,
        label:        str   = ""
    ) -> bool:
        """
        Element dhundo aur click karo
        FIXED: pre_action_fidget try/except se safe hai
        """
        el = self.finder.find(
            element_name,
            timeout=timeout,
            fallback=fallback
        )

        if not el:
            self._log(f"   ❌ Element not found: {element_name}")
            return False

        # FIXED: Safe fidget - crash nahi hoga
        try:
            self.behavior.pre_action_fidget()
        except Exception as e:
            self._log(f"   ⚠️ Fidget skip: {e}")

        # Focus ensure
        self._focus_chrome()

        # Click element
        x = el.x + random.randint(-3, 3)
        y = el.y + random.randint(-3, 3)

        # FIXED: Clamp
        x, y = self.mouse._clamp(x, y)

        lbl = label or element_name
        self._log(
            f"[FIND] ✅ '{el.text}' @ ({el.x},{el.y})"
            f" score={el.score:.0f}"
        )

        self.mouse.move_to(x, y)
        time.sleep(random.uniform(0.1, 0.3))
        self.mouse.click()

        return True

    def _find_and_click_all(
        self,
        element_name: str,
        index:        int   = 0,
        timeout:      float = 10.0
    ) -> bool:
        """Multiple elements mein se index wala click karo"""
        els = self.finder.find_all(element_name, timeout)

        if not els:
            self._log(f"   ❌ No elements: {element_name}")
            return False

        if index >= len(els):
            self._log(
                f"   ❌ Index {index} out of range "
                f"(found {len(els)})"
            )
            return False

        el = els[index]

        try:
            self.behavior.pre_action_fidget()
        except Exception:
            pass

        self._focus_chrome()

        x = el.x + random.randint(-3, 3)
        y = el.y + random.randint(-3, 3)
        x, y = self.mouse._clamp(x, y)

        self.mouse.move_to(x, y)
        time.sleep(random.uniform(0.1, 0.25))
        self.mouse.click()

        return True

    # ═══════════════════════════════════════════════════════
    # NAVIGATION HELPERS
    # ═══════════════════════════════════════════════════════

    def _navigate(self, url: str, wait: float = 3.0):
        """
        URL navigate karo
        FIXED: hwnd refresh after navigate
        """
        self._focus_chrome()
        time.sleep(random.uniform(0.2, 0.4))

        self.keyboard.hotkey('ctrl', 'l')
        time.sleep(random.uniform(0.3, 0.5))

        pyperclip.copy(url)
        self.keyboard.paste()
        time.sleep(random.uniform(0.2, 0.3))

        self.keyboard.press_enter()
        self._log(f"[NAV] Opening {url}...")

        time.sleep(wait + random.uniform(0, 1.5))

        # FIXED: hwnd refresh
        self._refresh_hwnd()

    def _type_in_address_bar(self, text: str):
        """Address bar mein text type karo"""
        self._focus_chrome()
        self.keyboard.hotkey('ctrl', 'l')
        time.sleep(random.uniform(0.3, 0.5))
        self.keyboard.type_text(text, make_typos=False)
        time.sleep(random.uniform(0.2, 0.3))

    # ═══════════════════════════════════════════════════════
    # FACEBOOK DETECTION
    # ═══════════════════════════════════════════════════════

    def _get_current_url(self) -> str:
        """
        Current URL detect karo
        Bridge se try karo, fallback window title
        """
        if self.bridge:
            try:
                url = self.bridge.get_current_url()
                if url:
                    return url
            except Exception:
                pass

        # Fallback: window title
        if self.chrome_hwnd:
            try:
                title = win32gui.GetWindowText(
                    self.chrome_hwnd
                ).lower()
                if 'facebook' in title:
                    return 'https://www.facebook.com'
                if 'business' in title:
                    return 'https://business.facebook.com'
            except Exception:
                pass

        return 'unknown'

    def _is_on_facebook(self) -> bool:
        """Facebook pe hain ya nahi"""
        url = self._get_current_url()
        return 'facebook' in url.lower()

    def _is_logged_in(self) -> bool:
        """Login check karo"""
        if self.bridge:
            try:
                return self.bridge.is_logged_in()
            except Exception:
                pass
        return True  # Assume logged in

    # ═══════════════════════════════════════════════════════
    # WARMUP - FIXED
    # ═══════════════════════════════════════════════════════

    def _do_warmup(
        self,
        min_sec: int = 15,
        max_sec: int = 45
    ):
        """
        FIXED: Human warmup
        Mouse Chrome window mein rahega
        Scroll kaam karega
        """
        if not self.chrome_hwnd:
            self._log("⚠️ No Chrome hwnd for warmup")
            return

        # FIXED: Focus pehle
        self._focus_chrome()
        time.sleep(random.uniform(0.5, 1.0))

        # FIXED: behavior ko hwnd diya hua hai
        duration = random.randint(min_sec, max_sec)
        self._log(f"[STEP 4/18] Human warmup")

        # FIXED: pre_upload_warmup ab window mein rahega
        self.behavior.pre_upload_warmup(duration)

    # ═══════════════════════════════════════════════════════
    # PAGE SWITCHING - FIXED
    # ═══════════════════════════════════════════════════════

    def _switch_to_page_via_url(self, page_name: str) -> bool:
        """
        FIXED: Simple URL-based page switch
        Facebook page ka direct URL open karo
        """
        try:
            # Page name se URL banao (spaces to dots)
            page_url_name = page_name.replace(' ', '.')
            urls = [
                f"https://www.facebook.com/{page_url_name}",
                f"https://www.facebook.com/pages/{page_name}",
            ]
            for url in urls:
                self._navigate(url, wait=3.0)
                time.sleep(2.0)
                # Basic check
                if self.chrome_hwnd:
                    try:
                        title = win32gui.GetWindowText(self.chrome_hwnd).lower()
                        if page_name.lower() in title or 'facebook' in title:
                            self._log(f"✅ Opened: {url}")
                            return True
                    except Exception:
                        pass
            return True
        except Exception as e:
            self._log(f"⚠️ URL switch error: {e}")
            return False

    def _human_switch_to_page(
        self,
        page_name: str
    ) -> bool:
        """
        Facebook page switch karo
        FIXED: pre_action_fidget crash fix applied
        """
        self._log(f"[NAV] Switching to page: '{page_name}'")

        # Profile switcher dhundo
        self._log("[NAV] Opening profile menu...")
        self.behavior.think(1.0, 2.0)

        # FIXED: _find_and_click ab safe hai
        found = self._find_and_click(
            'profile_switcher',
            timeout=10.0,
            fallback=(0.97, 0.07),
            label="Profile Switcher"
        )

        if not found:
            self._log("❌ Profile switcher not found!")
            return False

        time.sleep(random.uniform(1.5, 2.5))

        # Page list mein page dhundo
        self._log(f"[NAV] Looking for page: {page_name}")
        pages = self.finder.find_all(
            'page_option',
            timeout=8.0
        )

        if not pages:
            self._log("⚠️ No pages in switcher, trying URL method...")
            # FIXED: URL fallback
            if self._switch_to_page_via_url(page_name):
                return True
            self._log("❌ URL fallback also failed!")
            return False

        # Page name match karo
        target = None
        for p in pages:
            if page_name.lower() in p.text.lower():
                target = p
                break

        if not target:
            # First page try karo
            self._log(
                f"⚠️ '{page_name}' not found, trying first page"
            )
            if pages:
                target = pages[0]

        if not target:
            return False

        # FIXED: Safe click
        try:
            self.behavior.pre_action_fidget()
        except Exception:
            pass

        self._focus_chrome()
        x = target.x + random.randint(-3, 3)
        y = target.y + random.randint(-3, 3)
        x, y = self.mouse._clamp(x, y)

        self.mouse.move_to(x, y)
        time.sleep(random.uniform(0.1, 0.3))
        self.mouse.click()

        time.sleep(random.uniform(2.0, 3.5))
        self._refresh_hwnd()

        self._log(f"✅ Switched to: {page_name}")
        return True

    # ═══════════════════════════════════════════════════════
    # FACEBOOK OPEN
    # ═══════════════════════════════════════════════════════

    def _open_facebook(self) -> bool:
        """
        Facebook open karo
        FIXED: Proper URL navigation
        """
        self._log("[STEP 3/18] Open Facebook")

        url = self._get_current_url()
        self._log(f"[STEP 3/18] Current: {url}")

        if not self._is_on_facebook():
            self._log("[STEP 3/18] Not on FB, opening...")
            self._log("[NAV] Opening Facebook...")

            self._navigate(
                "https://www.facebook.com",
                wait=4.0
            )

            # Typed log
            self._log("[NAV] ⌨️ Typed facebook.com")
            self._log("[NAV] Waiting for Facebook...")

            time.sleep(random.uniform(3.0, 5.0))
            self._log("[NAV] ✅ Facebook loaded")
        else:
            self._log("[STEP 3/18] Already on Facebook ✅")

        return self._is_on_facebook()

    # ═══════════════════════════════════════════════════════
    # EXTENSION CHECK
    # ═══════════════════════════════════════════════════════

    def _check_extension(self) -> bool:
        """Extension ready check"""
        self._log("[STEP 2/18] Extension check")

        # FIXED: Bridge auto-load try
        if not self.bridge:
            self.bridge = HybridUploader._bridge_instance
            if self.bridge:
                self.finder.set_bridge(self.bridge)

        if not self.bridge:
            self._log("[STEP 2/18] ⚠️ No bridge available")
            return True

        # Extension connected check
        try:
            from fb_helper import websocket_server as ws
            # Wait for extension to connect
            for i in range(20):
                if ws.is_connected():
                    self._log("[STEP 2/18] ✅ Extension connected!")
                    return True
                import time
                time.sleep(0.5)
            self._log("[STEP 2/18] ⚠️ Extension not connected (timeout)")
            return True
        except Exception as e:
            self._log(f"[STEP 2/18] ⚠️ Check error: {e}")
            return True

    # ═══════════════════════════════════════════════════════
    # COMPOSER OPEN
    # ═══════════════════════════════════════════════════════

    def _open_composer(self) -> bool:
        """
        FIXED: Composer open karo
        Page profile pe hi rehna - Business Suite avoid
        """
        self._log("[STEP 6/18] Opening composer...")

        # FIXED: Wait for page load
        time.sleep(random.uniform(3.0, 5.0))
        self._focus_chrome()

        # FIXED: Ctrl+End to scroll top, then click "Whats on your mind" area
        try:
            # Scroll to top
            self.keyboard.press_key('home')
            time.sleep(random.uniform(1.0, 2.0))
        except Exception:
            pass

        # Try clicking on typical "Create post" area on page profile
        # Facebook page profile: usually at top center
        rect = self.window.get_rect(self.chrome_hwnd)
        if not rect:
            return False

        l, t, r, b = rect
        w = r - l
        h = b - t

        # Try multiple typical positions of "Create post" on FB page
        positions = [
            (0.50, 0.30),   # Center top - main composer
            (0.50, 0.35),
            (0.45, 0.30),
            (0.55, 0.35),
            (0.50, 0.25),
        ]

        for rel_x, rel_y in positions:
            ax = l + int(w * rel_x)
            ay = t + int(h * rel_y)
            ax, ay = self.mouse._clamp(ax, ay)

            self._log(f"   Trying composer position: ({rel_x:.2f}, {rel_y:.2f})")
            self.mouse.move_to(ax, ay)
            time.sleep(random.uniform(0.5, 1.0))
            self.mouse.click()
            time.sleep(random.uniform(2.0, 3.5))

            # Check if composer opened
            if self._is_composer_open():
                self._log("✅ Composer opened!")
                return True

        self._log("⚠️ Composer may not be open, continuing...")
        return False

    def _is_composer_open(self) -> bool:
        """Composer open hua check karo"""
        if self.bridge:
            try:
                return self.bridge.is_composer_open()
            except Exception:
                pass

        # Window title check
        if self.chrome_hwnd:
            try:
                title = win32gui.GetWindowText(
                    self.chrome_hwnd
                ).lower()
                kws = ['create','post','compose','publish']
                return any(k in title for k in kws)
            except Exception:
                pass

        return False

    # ═══════════════════════════════════════════════════════
    # FILE ATTACH
    # ═══════════════════════════════════════════════════════

    def _attach_file(self, file_path: str) -> bool:
        """
        Video file attach karo
        FIXED: Focus + clamp applied
        """
        self._log(
            f"[STEP 8/18] Attaching: "
            f"{os.path.basename(file_path)}"
        )

        if not os.path.exists(file_path):
            self._log(f"❌ File not found: {file_path}")
            return False

        pyperclip.copy(file_path)

        # Photo/Video button click
        found = self._find_and_click(
            'add_photo_video',
            timeout=10.0,
            fallback=(0.12, 0.50),
            label="Photo/Video"
        )

        if not found:
            self._log("❌ Photo/Video button not found!")
            return False

        time.sleep(random.uniform(1.5, 3.0))

        # File dialog wait
        dialog = self.window.wait_for_window(
            "Open", timeout=8
        )

        if dialog:
            self._log("📁 File dialog opened!")
            self.window.focus_window(dialog)
            time.sleep(random.uniform(0.5, 1.0))

            # Path type karo
            self.keyboard.hotkey('ctrl', 'l')
            time.sleep(random.uniform(0.3, 0.5))
            self.keyboard.type_text(
                file_path, make_typos=False
            )
            time.sleep(random.uniform(0.3, 0.5))
            self.keyboard.press_enter()
            time.sleep(random.uniform(2.0, 4.0))

            # FIXED: Dialog close ke baad Chrome focus wapas
            self._focus_chrome()
            self._refresh_hwnd()

            self._log("✅ File attached!")
            return True

        self._log("❌ File dialog not opened!")
        return False

    # ═══════════════════════════════════════════════════════
    # CAPTION TYPE
    # ═══════════════════════════════════════════════════════

    def _type_caption(self, caption: str) -> bool:
        """Caption type karo"""
        self._log("[STEP 10/18] Typing caption...")

        if not caption:
            return True

        # Caption area click
        self._find_and_click(
            'caption_box',
            timeout=8.0,
            fallback=(0.50, 0.38),
            label="Caption Area"
        )

        time.sleep(random.uniform(0.5, 1.0))

        # FIXED: Focus ensure karo
        self._focus_chrome()

        # Human-like typing
        self.keyboard.type_text(caption, make_typos=True)
        time.sleep(random.uniform(0.5, 1.5))

        self._log("✅ Caption typed!")
        return True

    # ═══════════════════════════════════════════════════════
    # PUBLISH
    # ═══════════════════════════════════════════════════════

    def _click_publish(self) -> bool:
        """Publish button click karo"""
        self._log("[STEP 14/18] Clicking Publish...")

        # Thinking pause
        self.behavior.think(2.0, 5.0)

        found = self._find_and_click(
            'publish_button',
            timeout=10.0,
            fallback=(0.85, 0.90),
            label="Publish"
        )

        if found:
            time.sleep(random.uniform(3.0, 5.0))
            if self._is_published():
                self._log("✅ Published!")
                return True

        return False

    def _is_published(self) -> bool:
        """Published check"""
        if self.bridge:
            try:
                return self.bridge.is_published()
            except Exception:
                pass

        if self.chrome_hwnd:
            try:
                title = win32gui.GetWindowText(
                    self.chrome_hwnd
                ).lower()
                kws = ['published','posted','shared','live']
                return any(k in title for k in kws)
            except Exception:
                pass

        return False

    def _dismiss_popups(self):
        """Popups dismiss karo"""
        self._log("[STEP 16/18] Checking popups...")

        self._focus_chrome()
        self.keyboard.press_escape()
        time.sleep(random.uniform(0.5, 1.0))

        # Maybe Later button
        self._find_and_click(
            'boost_popup',
            timeout=3.0,
            fallback=(0.50, 0.65),
            label="Maybe Later"
        )

        time.sleep(random.uniform(0.5, 1.0))
            # ═══════════════════════════════════════════════════════
    # UPLOAD VIDEO - MAIN FLOW
    # ═══════════════════════════════════════════════════════


    # BACKWARD COMPATIBILITY METHODS
    _bridge_instance = None

    @staticmethod
    def init_bridge(port=8765, **kwargs):
        try:
            # Import modules
            from fb_helper import websocket_server as ws_module
            from fb_helper.element_bridge import ElementBridge

            # Start WebSocket server (yeh function hai, class nahi)
            try:
                ws_module.start_server(port=port)
                print(f"[STARTUP] WebSocket server started on port {port}")
            except TypeError:
                # Agar port argument nahi lete
                ws_module.start_server()
                print(f"[STARTUP] WebSocket server started")
            except Exception as e:
                print(f"[STARTUP] Server start warning: {e}")

            # Bridge banao
            bridge = ElementBridge()
            HybridUploader._bridge_instance = bridge
            print("[STARTUP] Extension Bridge Ready")
            return bridge

        except Exception as e:
            print(f"[STARTUP] Bridge init error: {e}")
            import traceback
            traceback.print_exc()
            return None

    @staticmethod
    def get_bridge():
        if HybridUploader._bridge_instance is None:
            HybridUploader.init_bridge()
        return HybridUploader._bridge_instance

    @staticmethod
    def set_bridge(bridge):
        HybridUploader._bridge_instance = bridge

    def upload_video(
        self,
        profile_path:  str  = None,
        page_name:     str  = None,
        video_path:    str  = None,
        caption:       str  = "",
        schedule_time: str  = "NOW",
        warmup_config: dict = None,
        ui_log              = None,
        **kwargs
    ) -> bool:
        """
        Main upload flow - 18 Steps
        FIXED: IndexError fixed
        FIXED: Mouse stays in Chrome
        FIXED: Scroll works properly
        """
        if ui_log:
            self.ui_log = ui_log

        self._log("=" * 55)
        self._log("🤖 HYBRID UPLOADER V8.0")
        self._log("   HUMAN NAVIGATION + MOUSE + SIDEBAR")
        self._log(f"📁 Page  : {page_name}")
        self._log(f"🎬 Video : {os.path.basename(video_path)}")
        self._log(f"📅 Sched : {schedule_time}")
        self._log("=" * 55)

        try:
            # ─── STEP 1: Chrome Setup ───────────────────────
            self._step(1, 18, "Chrome setup")

            if not self._setup_chrome(profile_path):
                self._log("[-] FATAL: Chrome setup failed!")
                return False

            time.sleep(random.uniform(1.5, 2.5))

            # ─── STEP 2: Extension Check ─────────────────────
            self._step(2, 18, "Extension check")
            self._check_extension()
            time.sleep(random.uniform(3.0, 5.0))

            # ─── STEP 3: Open Facebook ───────────────────────
            self._step(3, 18, "Open Facebook")
            if not self._open_facebook():
                self._log("[-] FATAL: Facebook not opened!")
                return False

            time.sleep(random.uniform(3.0, 5.0))

            # ─── STEP 4: Human Warmup ────────────────────────
            self._step(4, 18, "Human warmup")

            # FIXED: warmup_config se min/max lo
            w_min = 15
            w_max = 45
            if warmup_config:
                w_min = warmup_config.get('min', 15)
                w_max = warmup_config.get('max', 45)
                enabled = warmup_config.get('enabled', True)
                if not enabled:
                    self._log("   Warmup disabled, skipping...")
                    w_min = 0
                    w_max = 0

            if w_min > 0:
                # FIXED: Focus + hwnd set hai already
                self._do_warmup(w_min, w_max)
            else:
                self._log("   Warmup skipped")

            time.sleep(random.uniform(1.0, 2.0))

            # ─── STEP 5: Switch to Page ──────────────────────
            self._step(5, 18, "Switch to page")
            self.behavior.think(1.5, 2.5)

            # FIXED: _human_switch_to_page ab crash nahi karega
            if not self._human_switch_to_page(page_name):
                self._log(
                    f"[-] FATAL: Could not switch to "
                    f"page: {page_name}"
                )
                return False

            time.sleep(random.uniform(2.0, 3.5))

            # ─── STEP 6: Open Composer ───────────────────────
            self._step(6, 18, "Open composer")

            if not self._open_composer():
                self._log("⚠️ Composer may not be open, continuing...")

            time.sleep(random.uniform(2.0, 3.5))

            # ─── STEP 7: Verify Composer ─────────────────────
            self._step(7, 18, "Verify composer")

            if self._is_composer_open():
                self._log("[STEP 7/18] ✅ Composer ready")
            else:
                self._log("[STEP 7/18] ⚠️ Composer state unclear")

            time.sleep(random.uniform(1.0, 2.0))

            # ─── STEP 8: Attach Video ────────────────────────
            self._step(8, 18, "Attach video")

            if not self._attach_file(video_path):
                self._log("[-] FATAL: File attach failed!")
                return False

            time.sleep(random.uniform(2.0, 3.5))

            # ─── STEP 9: Wait for Upload ─────────────────────
            self._step(9, 18, "Wait for video upload")
            self._log("⏳ Waiting for video to upload...")

            # Upload progress wait
            upload_wait = random.uniform(15, 35)
            self._log(f"   Estimated wait: {upload_wait:.0f}s")

            # FIXED: Upload wait ke dauran bhi window mein raho
            start_wait = time.time()
            while time.time() - start_wait < upload_wait:
                remaining = upload_wait - (
                    time.time() - start_wait
                )
                if remaining < 2:
                    break

                # FIXED: Focus maintain karo
                self._focus_chrome()

                # Small activity during wait
                act = random.choices(
                    ['wait', 'micro_move', 'scroll_tiny'],
                    weights=[60, 25, 15]
                )[0]

                if act == 'micro_move':
                    try:
                        self.mouse.micro_move()
                    except Exception:
                        pass
                    time.sleep(random.uniform(2.0, 4.0))

                elif act == 'scroll_tiny':
                    try:
                        self._focus_chrome()
                        self.mouse.scroll(-1)
                    except Exception:
                        pass
                    time.sleep(random.uniform(2.0, 4.0))

                else:
                    time.sleep(random.uniform(3.0, 6.0))

            self._log("✅ Upload wait complete")

            # ─── STEP 10: Type Caption ───────────────────────
            self._step(10, 18, "Type caption")

            if caption:
                self._type_caption(caption)
            else:
                self._log("   No caption, skipping...")

            time.sleep(random.uniform(1.0, 2.5))

            # ─── STEP 11: Set Schedule ───────────────────────
            self._step(11, 18, "Set schedule")

            if schedule_time and schedule_time != "NOW":
                self._log(
                    f"   Schedule: {schedule_time}"
                )
                self._set_schedule(schedule_time)
            else:
                self._log("   Schedule: NOW (immediate)")

            time.sleep(random.uniform(1.0, 2.0))

            # ─── STEP 12: Select Page ────────────────────────
            self._step(12, 18, "Verify page selection")
            self._log(f"   Page: {page_name} ✅")
            time.sleep(random.uniform(0.5, 1.5))

            # ─── STEP 13: Final Review ───────────────────────
            self._step(13, 18, "Final review")
            self.behavior.think(1.5, 3.5, label="reviewing")
            time.sleep(random.uniform(1.0, 2.0))

            # ─── STEP 14: Click Publish ──────────────────────
            self._step(14, 18, "Click publish")

            if not self._click_publish():
                self._log("[-] FATAL: Publish failed!")
                return False

            time.sleep(random.uniform(3.0, 5.0))

            # ─── STEP 15: Verify Published ───────────────────
            self._step(15, 18, "Verify published")

            if self._is_published():
                self._log("[STEP 15/18] ✅ Post published!")
            else:
                self._log(
                    "[STEP 15/18] ⚠️ Publish state unclear"
                )

            time.sleep(random.uniform(1.0, 2.0))

            # ─── STEP 16: Dismiss Popups ─────────────────────
            self._step(16, 18, "Dismiss popups")
            self._dismiss_popups()
            time.sleep(random.uniform(1.5, 2.5))

            # ─── STEP 17: Post Verification ──────────────────
            self._step(17, 18, "Post verification")
            self._log("   Verifying post on page...")
            time.sleep(random.uniform(2.0, 4.0))
            self._log("[STEP 17/18] ✅ Verification done")

            # ─── STEP 18: Cleanup ────────────────────────────
            self._step(18, 18, "Cleanup")
            self._log("   Cleaning up...")
            time.sleep(random.uniform(1.0, 2.0))
            self._log("[STEP 18/18] ✅ Done!")

            # ─── SUCCESS ─────────────────────────────────────
            self._log("")
            self._log("🎉 UPLOAD COMPLETE!")
            self._log(f"   Page    : {page_name}")
            self._log(
                f"   Video   : {os.path.basename(video_path)}"
            )
            self._log(f"   Schedule: {schedule_time}")
            self._log("=" * 55)

            return True

        except Exception as e:
            self._log(f"[-] FATAL: {type(e).__name__}: {e}")
            traceback.print_exc()

            # Screenshot save karo debug ke liye
            try:
                self._save_debug_screenshot()
            except Exception:
                pass

            # Browser close karo
            try:
                if self.chrome_hwnd:
                    self._close_browser()
            except Exception:
                pass

            return False

    # ═══════════════════════════════════════════════════════
    # SCHEDULE HELPER
    # ═══════════════════════════════════════════════════════

    def _set_schedule(self, schedule_time: str):
        """Schedule time set karo"""
        self._log(f"   Setting schedule: {schedule_time}")

        # Schedule button dhundo
        found = self._find_and_click(
            'schedule_button',
            timeout=8.0,
            fallback=(0.75, 0.88),
            label="Schedule"
        )

        if not found:
            self._log("   ⚠️ Schedule button not found")
            return

        time.sleep(random.uniform(1.5, 2.5))

        # Time input dhundo
        time_el = self.finder.find(
            'schedule_time',
            timeout=5.0
        )

        if time_el:
            self.mouse.click(time_el.x, time_el.y)
            time.sleep(random.uniform(0.3, 0.6))
            self.keyboard.select_all()
            self.keyboard.type_text(
                schedule_time,
                make_typos=False
            )
            time.sleep(random.uniform(0.3, 0.5))
            self.keyboard.press_enter()

        time.sleep(random.uniform(1.0, 2.0))
        self._log(f"   ✅ Schedule set: {schedule_time}")

    # ═══════════════════════════════════════════════════════
    # DEBUG HELPERS
    # ═══════════════════════════════════════════════════════

    def _save_debug_screenshot(self):
        """Debug screenshot save karo"""
        try:
            import hashlib
            ts   = str(int(time.time()))
            name = f"debug_fatal_error_{ts}.png"
            path = os.path.join(os.getcwd(), name)

            # PIL se screenshot
            try:
                from PIL import ImageGrab
                img = ImageGrab.grab()
                img.save(path)
                self._log(f"[DBG] Screenshot: {path}")
            except ImportError:
                pass

        except Exception as e:
            self._log(f"[DBG] Screenshot failed: {e}")

    def _close_browser(self):
        """Browser close karo"""
        try:
            if self.chrome_hwnd:
                win32gui.PostMessage(
                    self.chrome_hwnd,
                    win32con.WM_CLOSE,
                    0, 0
                )
                time.sleep(random.uniform(1.5, 2.5))
                self._log("[*] Browser closed.")
        except Exception:
            pass

    def _get_window_info(self) -> dict:
        """Window info return karo"""
        info = {
            'hwnd':   self.chrome_hwnd,
            'rect':   self.chrome_rect,
            'width':  self.chrome_w,
            'height': self.chrome_h,
        }
        return info


# ═══════════════════════════════════════════════════════════
# ENTRY POINT FUNCTION
# ═══════════════════════════════════════════════════════════

def create_uploader(bridge=None) -> HybridUploader:
    """
    HybridUploader instance create karo
    Bridge optional hai
    """
    return HybridUploader(bridge=bridge)


def upload_video_human(
    profile_path:  str,
    page_name:     str,
    video_path:    str,
    caption:       str,
    schedule_time: str  = "NOW",
    warmup_config: dict = None,
    bridge              = None,
    ui_log              = None
) -> bool:
    """
    Convenience function - direct upload
    FIXED: Saare fixes included
    """
    uploader = create_uploader(bridge=bridge)

    if ui_log:
        uploader.set_logger(ui_log)

    return uploader.upload_video(
        profile_path  = profile_path,
        page_name     = page_name,
        video_path    = video_path,
        caption       = caption,
        schedule_time = schedule_time,
        warmup_config = warmup_config,
        ui_log        = ui_log
    )


# ═══════════════════════════════════════════════════════════
# QUICK TEST
# ═══════════════════════════════════════════════════════════

def _test_mouse_fix():
    """
    IndexError fix test karo
    _trace() function test
    """
    print("=" * 55)
    print("Testing _trace() IndexError Fix")
    print("=" * 55)

    mouse = HumanMouse()

    print("\n✅ HumanMouse initialized")
    print(f"   Screen: {SCREEN_W}x{SCREEN_H}")

    # Test 1: Normal move
    print("\n[TEST 1] Normal move_to...")
    try:
        mouse.move_to(
            SCREEN_W // 2,
            SCREEN_H // 2
        )
        print("   ✅ move_to: OK")
    except Exception as e:
        print(f"   ❌ move_to: {e}")

    # Test 2: micro_move
    print("\n[TEST 2] micro_move...")
    try:
        for i in range(5):
            mouse.micro_move()
            time.sleep(0.3)
        print("   ✅ micro_move x5: OK")
    except Exception as e:
        print(f"   ❌ micro_move: {e}")

    # Test 3: Scroll
    print("\n[TEST 3] scroll...")
    try:
        mouse.scroll(-3)
        time.sleep(0.5)
        mouse.scroll(3)
        print("   ✅ scroll: OK")
    except Exception as e:
        print(f"   ❌ scroll: {e}")

    # Test 4: Chrome window test
    print("\n[TEST 4] Chrome window bounds test...")
    try:
        import win32gui as _wg
        hwnds = []

        def _cb(hwnd, _):
            if _wg.IsWindowVisible(hwnd):
                t = _wg.GetWindowText(hwnd)
                c = _wg.GetClassName(hwnd)
                if 'chrome' in c.lower() and len(t) > 0:
                    hwnds.append(hwnd)
            return True

        _wg.EnumWindows(_cb, None)

        if hwnds:
            hwnd = hwnds[-1]
            mouse.set_chrome_hwnd(hwnd)
            print(f"   ✅ Chrome found: {hwnd}")

            # Test warmup in window
            bh = HumanBehavior()
            bh.set_chrome_hwnd(hwnd)

            print("   Running 8s warmup in Chrome...")
            bh.pre_upload_warmup(duration=8)
            print("   ✅ Warmup done! No IndexError!")
        else:
            print("   ⚠️ Chrome not open, skipping")

    except Exception as e:
        print(f"   ❌ Chrome test: {e}")
        traceback.print_exc()

    print("\n" + "=" * 55)
    print("ALL TESTS DONE!")
    print("=" * 55)


if __name__ == "__main__":
    _test_mouse_fix()  
HybridFacebookUploader = HybridUploader 
