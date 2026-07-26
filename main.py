"""
FB Empire Auto-Bot V10.0 | Premium Edition (HYBRID)
Extension First Architecture
"""
import customtkinter as ctk
import threading
import os
import subprocess
import time

from db_manager import db
from downloader import Downloader
from video_editor import (
    get_stealthmax_preset,
    generate_workspace_persona,
)
from ai_writer import AIWriter
from thumbnail_gen import ThumbnailGenerator
from hybrid_uploader import HybridFacebookUploader

# ═══ UI Modules ═══
from ui.dashboard import show_home_screen
from ui.workspaces import (
    show_workspaces_screen,
    render_workspaces_list,
)
from ui.create_workspace import show_create_profile_screen
from ui.queue_tab import (
    build_queue_tab,
    render_videos_by_category,
    _compute_counts,
    _compute_data_hash,
    _categorize_video,
)
from ui.editing_tab import build_editing_tab
from ui.calendar_tab import build_calendar_tab
from ui.settings_tab import build_settings_tab

# ═══ Utils ═══
from utils.helpers import ToastNotification, time_ago
from utils.excel_logger import (
    log_to_workspace_excel,
    get_workspace_excel_path,
)

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

# ═══ COLORS ═══
BG_MAIN = "#0a0e1a"
BG_SIDEBAR = "#0d1220"
BG_CARD = "#131b2e"
BG_ELEVATED = "#1e293b"
ACCENT = "#6366f1"
ACCENT_HOVER = "#4f46e5"
PURPLE = "#8b5cf6"
SUCCESS = "#10b981"
SUCCESS_BG = "#064e3b"
WARNING = "#f59e0b"
WARNING_BG = "#78350f"
DANGER = "#ef4444"
DANGER_BG = "#7f1d1d"
TEXT_PRIMARY = "#f8fafc"
TEXT_SECONDARY = "#94a3b8"
TEXT_MUTED = "#64748b"
TEXT_DIM = "#475569"
BORDER = "#1e293b"
BORDER_LIGHT = "#334155"


# ═══════════════════════════════════════
# EXTENSION BRIDGE INIT (STARTUP)
# ═══════════════════════════════════════

def init_extension_bridge():
    """Initialize extension bridge at startup"""
    try:
        print("=" * 55)
        print("🚀 FB Empire Starting...")
        print("=" * 55)
        print("[STARTUP] Initializing Extension Bridge...")

        HybridFacebookUploader.init_bridge(port=8765)

        print("[STARTUP] ✅ Extension Bridge Ready")
        print("[STARTUP] WebSocket: ws://localhost:8765")
        print("[STARTUP] Waiting for extension...")
        print("=" * 55)
        return True

    except Exception as e:
        print(f"[STARTUP] ⚠️ Bridge init error: {e}")
        return False


# ═══════════════════════════════════════
# MAIN APP CLASS
# ═══════════════════════════════════════

class FBAutomationApp(ctk.CTk):

    def __init__(self):
        super().__init__()

        self.title(
            "FB Empire Auto-Bot | "
            "Premium HYBRID Edition [V10.2]"
        )
        self.geometry("1400x900")
        self.minsize(1200, 750)
        self.configure(fg_color=BG_MAIN)

        # ═══ Core Instances ═══
        self.downloader = Downloader()
        self.ai = AIWriter()
        self.thumbnail_gen = ThumbnailGenerator()

        # ═══ Extension Bridge ═══
        self.bridge = HybridFacebookUploader.get_bridge()

        # ═══ State Variables ═══
        self.status_labels = {}
        self._active_uploads = {}
        self._upload_lock = threading.Lock()
        self._auto_sync_active = False
        self._current_ws = None
        self._current_queue_tab = "pending"
        self._last_data_hash = None
        self._last_counts = {
            "pending": 0,
            "processing": 0,
            "done": 0,
        }
        self._current_editing_preset = (
            get_stealthmax_preset()
        )
        self._process_threads = {}
        self._process_stop_flags = {}
        self._process_pause_flags = {}
        self._selected_video_ids = set()
        self._video_checkboxes = {}
        self._selection_locked = False
        self._search_query = ""
        self._sort_mode = "recent"
        self._filter_mode = "active"
        self._current_view = "home"

        # Extension status
        self._extension_status = "checking"

        # ═══ Build UI ═══
        self._build_layout()
        self.show_home_screen()

        # ═══ Check extension after UI ready ═══
        self.after(2000, self._check_extension_status)

    # ═══════════════════════════════════════
    # EXTENSION STATUS CHECK
    # ═══════════════════════════════════════

    def _check_extension_status(self):
        """Check extension connection periodically"""
        try:
            if self.bridge and self.bridge.is_extension_connected():
                if self._extension_status != "connected":
                    self._extension_status = "connected"
                    self._update_extension_indicator()
                    print(
                        "[EXT] ✅ Extension connected!"
                    )
            else:
                if self._extension_status != "waiting":
                    self._extension_status = "waiting"
                    self._update_extension_indicator()
        except Exception:
            pass

        # Check every 3 seconds
        self.after(3000, self._check_extension_status)

    def _update_extension_indicator(self):
        """Update top-right extension indicator"""
        if not hasattr(self, 'ext_label'):
            return

        try:
            if self._extension_status == "connected":
                self.ext_label.configure(
                    text=" 🟢 EXTENSION READY ",
                    text_color=SUCCESS
                )
                self.ext_frame.configure(
                    fg_color=SUCCESS_BG
                )
            elif self._extension_status == "waiting":
                self.ext_label.configure(
                    text=" 🟡 WAITING FOR EXTENSION ",
                    text_color=WARNING
                )
                self.ext_frame.configure(
                    fg_color=WARNING_BG
                )
            else:
                self.ext_label.configure(
                    text=" 🔴 EXTENSION OFFLINE ",
                    text_color=DANGER
                )
                self.ext_frame.configure(
                    fg_color=DANGER_BG
                )
        except Exception:
            pass

    # ═══════════════════════════════════════
    # LAYOUT
    # ═══════════════════════════════════════

    def _build_layout(self):
        """Main layout"""

        # Sidebar
        self.sidebar = ctk.CTkFrame(
            self,
            fg_color=BG_SIDEBAR,
            width=220,
            corner_radius=0
        )
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        # Content wrapper
        self.content_wrapper = ctk.CTkFrame(
            self,
            fg_color=BG_MAIN,
            corner_radius=0
        )
        self.content_wrapper.pack(
            side="right", fill="both", expand=True
        )

        self._build_top_bar()

        # Main container
        self.container = ctk.CTkFrame(
            self.content_wrapper, fg_color="transparent"
        )
        self.container.pack(
            fill="both", expand=True,
            padx=30, pady=(20, 20)
        )

        self._build_status_bar()
        self._build_sidebar()

    def _build_sidebar(self):
        """Sidebar"""

        # Logo
        logo_frame = ctk.CTkFrame(
            self.sidebar,
            fg_color="transparent",
            height=90
        )
        logo_frame.pack(fill="x", pady=(20, 20))
        logo_frame.pack_propagate(False)

        ctk.CTkLabel(
            logo_frame, text="🚀",
            font=("Segoe UI", 32)
        ).pack(pady=(10, 0))

        ctk.CTkLabel(
            logo_frame, text="FB Empire",
            font=("Segoe UI", 16, "bold"),
            text_color=TEXT_PRIMARY
        ).pack()

        ctk.CTkLabel(
            logo_frame,
            text="v10.2 HYBRID 🛡️",
            font=("Segoe UI", 10),
            text_color=SUCCESS
        ).pack()

        # Divider
        ctk.CTkFrame(
            self.sidebar, fg_color=BORDER, height=1
        ).pack(fill="x", padx=20, pady=(5, 15))

        # Nav buttons
        self.nav_buttons = {}
        nav_items = [
            ("home",   "🏠", "Dashboard"),
            ("spaces", "📁", "Workspaces"),
        ]

        for view_id, icon, label in nav_items:
            bf = ctk.CTkFrame(
                self.sidebar,
                fg_color="transparent",
                height=45
            )
            bf.pack(fill="x", padx=12, pady=2)
            bf.pack_propagate(False)

            btn = ctk.CTkButton(
                bf,
                text=f"  {icon}   {label}",
                font=("Segoe UI", 13),
                anchor="w", height=42,
                fg_color="transparent",
                text_color=TEXT_SECONDARY,
                hover_color=BG_ELEVATED,
                corner_radius=8,
                command=lambda v=view_id: (
                    self._navigate_to(v)
                )
            )
            btn.pack(fill="x")
            self.nav_buttons[view_id] = btn

        # Spacer
        ctk.CTkFrame(
            self.sidebar, fg_color="transparent"
        ).pack(fill="both", expand=True)

        # Bottom divider
        ctk.CTkFrame(
            self.sidebar, fg_color=BORDER, height=1
        ).pack(fill="x", padx=20, pady=(0, 10))

        # New Workspace button
        ctk.CTkButton(
            self.sidebar,
            text="  ➕  New Workspace",
            font=("Segoe UI", 12, "bold"),
            height=42,
            fg_color=ACCENT,
            hover_color=ACCENT_HOVER,
            corner_radius=8,
            command=self.show_create_profile_screen
        ).pack(fill="x", padx=15, pady=(0, 15))

        self._update_nav_active("home")

    def _update_nav_active(self, view_id):
        for vid, btn in self.nav_buttons.items():
            if vid == view_id:
                btn.configure(
                    fg_color=ACCENT,
                    text_color="white"
                )
            else:
                btn.configure(
                    fg_color="transparent",
                    text_color=TEXT_SECONDARY
                )

    def _navigate_to(self, view_id):
        self._current_view = view_id
        self._update_nav_active(view_id)
        if view_id == "home":
            self.show_home_screen()
        elif view_id == "spaces":
            self.show_workspaces_screen()

    def _build_top_bar(self):
        """Top bar with extension status"""
        self.top_bar = ctk.CTkFrame(
            self.content_wrapper,
            fg_color=BG_SIDEBAR,
            height=60,
            corner_radius=0
        )
        self.top_bar.pack(fill="x", side="top")
        self.top_bar.pack_propagate(False)

        self.page_title = ctk.CTkLabel(
            self.top_bar, text="Dashboard",
            font=("Segoe UI", 20, "bold"),
            text_color=TEXT_PRIMARY
        )
        self.page_title.pack(side="left", padx=30)

        # Extension status indicator
        self.ext_frame = ctk.CTkFrame(
            self.top_bar,
            fg_color=WARNING_BG,
            corner_radius=20,
            height=30
        )
        self.ext_frame.pack(side="right", padx=30)

        self.ext_label = ctk.CTkLabel(
            self.ext_frame,
            text=" 🟡 CHECKING EXTENSION ",
            font=("Segoe UI", 11, "bold"),
            text_color=WARNING
        )
        self.ext_label.pack(padx=10, pady=5)

    def _build_status_bar(self):
        """Bottom status bar"""
        sb = ctk.CTkFrame(
            self.content_wrapper,
            fg_color=BG_SIDEBAR,
            height=32,
            corner_radius=0
        )
        sb.pack(fill="x", side="bottom")
        sb.pack_propagate(False)

        ctk.CTkLabel(
            sb,
            text="  ⚡ Ready  •  "
                 "Extension + Win32 Active",
            font=("Segoe UI", 11),
            text_color=TEXT_MUTED
        ).pack(side="left", padx=20)

        ctk.CTkLabel(
            sb, text="v10.2 HYBRID  ",
            font=("Segoe UI", 10),
            text_color=TEXT_DIM
        ).pack(side="right", padx=20)

    # ═══════════════════════════════════════
    # SCREEN METHODS
    # ═══════════════════════════════════════

    def clear_container(self):
        self._auto_sync_active = False
        self._last_data_hash = None
        for w in self.container.winfo_children():
            w.destroy()

    def show_home_screen(self):
        self.clear_container()
        self._update_nav_active("home")
        self.page_title.configure(text="Dashboard")
        show_home_screen(self)

    def show_workspaces_screen(self):
        self.clear_container()
        self._update_nav_active("spaces")
        self.page_title.configure(text="Workspaces")
        show_workspaces_screen(self)

    def show_create_profile_screen(self):
        self.clear_container()
        self.page_title.configure(
            text="Create New Workspace"
        )
        show_create_profile_screen(self)

    def show_workspace(self, workspace_name):
        """Individual workspace"""
        self.clear_container()
        self._current_ws = workspace_name
        self._selected_video_ids = set()
        self._video_checkboxes = {}
        self.page_title.configure(text=workspace_name)
        db.update_last_activity(workspace_name)

        # ═══ Header ═══
        header = ctk.CTkFrame(
            self.container, fg_color="transparent"
        )
        header.pack(fill="x", pady=(0, 15))

        ctk.CTkButton(
            header, text="← Workspaces",
            font=("Segoe UI", 12),
            height=36, width=140,
            fg_color=BG_CARD,
            hover_color=BG_ELEVATED,
            text_color=TEXT_SECONDARY,
            corner_radius=8,
            command=lambda: self._navigate_to("spaces")
        ).pack(side="left")

        title_frame = ctk.CTkFrame(
            header, fg_color="transparent"
        )
        title_frame.pack(side="left", padx=15)

        ctk.CTkLabel(
            title_frame,
            text=f"📁 {workspace_name}",
            font=("Segoe UI", 20, "bold"),
            text_color=TEXT_PRIMARY,
        ).pack(anchor="w")

        persona = db.get_workspace_persona(workspace_name)
        if persona:
            device = persona.get(
                'device_name',
                persona.get('model', '')
            )
            city = persona.get('city', '')
            ctk.CTkLabel(
                title_frame,
                text=f"📱 {device}  •  📍 {city}",
                font=("Segoe UI", 11),
                text_color=TEXT_SECONDARY,
            ).pack(anchor="w", pady=(2, 0))

        # ═══ Tabs ═══
        self.ws_tabs = ctk.CTkTabview(
            self.container,
            corner_radius=12,
            fg_color=BG_CARD,
            segmented_button_fg_color=BG_MAIN,
            segmented_button_selected_color=ACCENT,
            segmented_button_selected_hover_color=(
                ACCENT_HOVER
            ),
        )
        self.ws_tabs.pack(
            fill="both", expand=True, pady=(0, 15)
        )

        tab_input    = self.ws_tabs.add("📥 Add Videos")
        tab_queue    = self.ws_tabs.add(
            "⚙️ Process & Post"
        )
        tab_editing  = self.ws_tabs.add("🎬 Editing")
        tab_cal      = self.ws_tabs.add("📅 Calendar")
        tab_settings = self.ws_tabs.add("⚙️ Settings")

        # ═══ Build each tab ═══
        self._build_input_tab(tab_input, workspace_name)
        build_queue_tab(self, tab_queue, workspace_name)
        build_editing_tab(
            self, tab_editing, workspace_name
        )
        build_calendar_tab(self, tab_cal, workspace_name)
        build_settings_tab(
            self, tab_settings, workspace_name
        )

        # ═══ Terminal ═══
        term_frame = ctk.CTkFrame(
            self.container,
            fg_color=BG_CARD,
            corner_radius=10
        )
        term_frame.pack(fill="x", pady=(0, 0))

        term_header = ctk.CTkFrame(
            term_frame, fg_color="transparent"
        )
        term_header.pack(fill="x", padx=15, pady=(10, 5))

        ctk.CTkLabel(
            term_header,
            text="💻 Live Engine Logs",
            font=("Segoe UI", 12, "bold"),
            text_color=TEXT_PRIMARY,
        ).pack(side="left")

        ctk.CTkLabel(
            term_header,
            text="🛡️ EXTENSION + WIN32",
            font=("Segoe UI", 10, "bold"),
            text_color=SUCCESS,
        ).pack(side="right")

        self.terminal = ctk.CTkTextbox(
            term_frame, height=110,
            fg_color="#000000",
            text_color="#10b981",
            font=("Consolas", 11),
            corner_radius=8,
        )
        self.terminal.pack(
            fill="x", padx=15, pady=(0, 12)
        )
        self.terminal.insert(
            "end",
            "[*] Extension First Engine Ready "
            "(Chrome Extension + Win32 Mouse)\n"
        )

        # ═══ Auto sync ═══
        self._auto_sync_active = True
        self._start_smart_auto_sync(workspace_name)

    # ═══════════════════════════════════════
    # INPUT TAB
    # ═══════════════════════════════════════

    def _build_input_tab(self, parent, ws_name):
        """Add videos tab"""
        import pandas as pd
        from tkinter import filedialog

        wrapper = ctk.CTkScrollableFrame(
            parent, fg_color="transparent"
        )
        wrapper.pack(
            pady=20, padx=30, fill="both", expand=True
        )

        ctk.CTkLabel(
            wrapper,
            text="📥 Add Content to Queue",
            font=("Segoe UI", 22, "bold"),
            text_color=TEXT_PRIMARY,
        ).pack(anchor="w")

        ctk.CTkLabel(
            wrapper,
            text="Import videos from URLs, PC, or CSV",
            font=("Segoe UI", 12),
            text_color=TEXT_SECONDARY,
        ).pack(anchor="w", pady=(3, 20))

        # Single URL
        input_frame = ctk.CTkFrame(
            wrapper, fg_color=BG_CARD, corner_radius=12
        )
        input_frame.pack(fill="x", pady=(0, 15), ipady=15)

        ctk.CTkLabel(
            input_frame,
            text="🔗  Single Video URL",
            font=("Segoe UI", 14, "bold"),
            text_color=TEXT_PRIMARY,
        ).pack(anchor="w", padx=20, pady=(5, 8))

        self.input_url = ctk.CTkEntry(
            input_frame, height=45,
            font=("Segoe UI", 12),
            placeholder_text=(
                "https://www.youtube.com/watch?v=..."
            ),
            fg_color=BG_MAIN,
            border_color=BORDER_LIGHT,
        )
        self.input_url.pack(
            fill="x", padx=20, pady=(0, 10)
        )

        def add_url():
            url = self.input_url.get().strip()
            if url:
                db.add_video_to_queue(ws_name, url)
                self.input_url.delete(0, 'end')
                self.show_toast(
                    "Video added!", "success"
                )
                self.ui_log(
                    f"[+] Added: {url[:50]}..."
                )
            else:
                self.show_toast(
                    "Enter a URL!", "warning"
                )

        ctk.CTkButton(
            input_frame,
            text="➕ Add to Queue",
            font=("Segoe UI", 13, "bold"),
            height=44, width=200,
            fg_color=ACCENT,
            hover_color=ACCENT_HOVER,
            corner_radius=8,
            command=add_url
        ).pack(anchor="w", padx=20, pady=(5, 5))

        # Local Files
        local_frame = ctk.CTkFrame(
            wrapper, fg_color=BG_CARD, corner_radius=12
        )
        local_frame.pack(fill="x", pady=(0, 15), ipady=15)

        ctk.CTkLabel(
            local_frame,
            text="💻  Select Videos from PC",
            font=("Segoe UI", 14, "bold"),
            text_color=TEXT_PRIMARY,
        ).pack(anchor="w", padx=20, pady=(5, 5))

        ctk.CTkLabel(
            local_frame,
            text="Ctrl+Click for multiple. "
                 "Supported: .mp4 .mov .mkv .avi .webm",
            font=("Segoe UI", 11),
            text_color=TEXT_SECONDARY,
        ).pack(anchor="w", padx=20, pady=(0, 10))

        def select_local():
            files = filedialog.askopenfilenames(
                title="Select Video Files",
                filetypes=[
                    ("Video Files",
                     "*.mp4 *.mov *.mkv *.avi *.webm"),
                    ("All Files", "*.*")
                ]
            )
            if files:
                count = 0
                for fp in files:
                    if os.path.exists(fp):
                        db.add_video_to_queue(
                            ws_name, fp
                        )
                        count += 1
                self.show_toast(
                    f"Added {count} video(s)!",
                    "success"
                )
                self.ui_log(
                    f"[+] Added {count} local videos"
                )

        ctk.CTkButton(
            local_frame,
            text="📁 Browse Files",
            font=("Segoe UI", 13, "bold"),
            height=44, width=200,
            fg_color="#0d9488",
            hover_color="#0f766e",
            corner_radius=8,
            command=select_local
        ).pack(anchor="w", padx=20, pady=(5, 5))

        # Bulk Import
        bulk_frame = ctk.CTkFrame(
            wrapper, fg_color=BG_CARD, corner_radius=12
        )
        bulk_frame.pack(fill="x", pady=(0, 15), ipady=15)

        ctk.CTkLabel(
            bulk_frame,
            text="📑  Bulk Import (CSV / Excel)",
            font=("Segoe UI", 14, "bold"),
            text_color=TEXT_PRIMARY,
        ).pack(anchor="w", padx=20, pady=(5, 5))

        ctk.CTkLabel(
            bulk_frame,
            text="File must have a 'URL' column",
            font=("Segoe UI", 11),
            text_color=TEXT_SECONDARY,
        ).pack(anchor="w", padx=20, pady=(0, 10))

        def bulk_import():
            path = filedialog.askopenfilename(
                filetypes=[
                    ("CSV", "*.csv"),
                    ("Excel", "*.xlsx *.xls"),
                ]
            )
            if not path:
                return
            try:
                if path.lower().endswith('.csv'):
                    df = pd.read_csv(path)
                else:
                    df = pd.read_excel(path)

                url_col = None
                for col in df.columns:
                    if col.strip().lower() == 'url':
                        url_col = col
                        break

                if not url_col:
                    self.show_toast(
                        "Column 'URL' not found!",
                        "error"
                    )
                    return

                count = 0
                for url in df[url_col].dropna():
                    url_str = str(url).strip()
                    if url_str.lower() not in [
                        'nan', 'none', ''
                    ]:
                        db.add_video_to_queue(
                            ws_name, url_str
                        )
                        count += 1

                self.show_toast(
                    f"Imported {count} URLs!",
                    "success"
                )
            except Exception as e:
                self.show_toast(
                    f"Import failed: {e}", "error"
                )

        ctk.CTkButton(
            bulk_frame,
            text="📑 Import CSV/Excel",
            font=("Segoe UI", 13, "bold"),
            height=44, width=200,
            fg_color="#4f46e5",
            hover_color="#4338ca",
            corner_radius=8,
            command=bulk_import
        ).pack(anchor="w", padx=20, pady=(5, 5))

        ctk.CTkLabel(
            bulk_frame,
            text=(
                "💡 Format:  URL\n"
                "     https://youtube.com/...\n"
                "     https://tiktok.com/..."
            ),
            font=("Consolas", 10),
            text_color=TEXT_MUTED,
            justify="left",
        ).pack(anchor="w", padx=20, pady=(10, 0))

    # ═══════════════════════════════════════
    # AUTO SYNC
    # ═══════════════════════════════════════

    def _start_smart_auto_sync(self, ws_name):
        """Auto sync"""

        def sync_loop():
            if not self._auto_sync_active:
                return
            try:
                if self._current_ws != ws_name:
                    return
                if self._selection_locked:
                    self.after(3000, sync_loop)
                    return
                if hasattr(self, 'ws_tabs'):
                    try:
                        current_tab = self.ws_tabs.get()
                        if current_tab == (
                            "⚙️ Process & Post"
                        ):
                            new_hash = _compute_data_hash(
                                self, ws_name
                            )
                            new_counts = _compute_counts(
                                self, ws_name
                            )
                            if new_counts != (
                                self._last_counts
                            ):
                                self._update_tab_counts(
                                    new_counts
                                )
                                self._last_counts = (
                                    new_counts
                                )
                            if new_hash != (
                                self._last_data_hash
                            ):
                                self._last_data_hash = (
                                    new_hash
                                )
                                render_videos_by_category(
                                    self, ws_name
                                )
                    except Exception:
                        pass
            except Exception:
                pass

            if self._auto_sync_active:
                self.after(3000, sync_loop)

        self.after(3000, sync_loop)

    def _update_tab_counts(self, counts):
        if not hasattr(self, '_subtab_buttons'):
            return
        try:
            self._subtab_buttons["pending"].configure(
                text=f"⏳ Pending ({counts['pending']})"
            )
            self._subtab_buttons["processing"].configure(
                text=(
                    f"⚙️ Processing "
                    f"({counts['processing']})"
                )
            )
            self._subtab_buttons["done"].configure(
                text=f"✅ Done ({counts['done']})"
            )
        except Exception:
            pass

    # ═══════════════════════════════════════
    # UTILITY METHODS
    # ═══════════════════════════════════════

    def show_toast(self, message, toast_type="info"):
        try:
            ToastNotification(self, message, toast_type)
        except Exception:
            pass

    def _append_log(self, msg):
        if (hasattr(self, 'terminal') and
                self.terminal.winfo_exists()):
            self.terminal.insert("end", msg + "\n")
            self.terminal.see("end")

    def ui_log(self, msg):
        self.after(0, lambda: self._append_log(msg))
        print(msg)

    def update_video_ui_status(
        self, video_id, text, color=WARNING
    ):
        if (hasattr(self, 'status_labels') and
                video_id in self.status_labels):
            lbl = self.status_labels[video_id]
            try:
                if lbl.winfo_exists():
                    self.after(
                        0,
                        lambda: lbl.configure(
                            text=f" {text} ",
                            text_color=color
                        )
                    )
            except Exception:
                pass

    def _open_reports_folder(self):
        try:
            os.startfile(os.path.dirname(__file__))
        except Exception as e:
            self.show_toast(f"Error: {e}", "error")

    # ═══════════════════════════════════════
    # CLEANUP ON EXIT
    # ═══════════════════════════════════════

    def on_close(self):
        """Cleanup on exit"""
        try:
            self._auto_sync_active = False
            if self.bridge:
                self.bridge.stop()
                print("[EXIT] Bridge stopped")
        except Exception:
            pass
        self.destroy()


# ═══════════════════════════════════════
# ENTRY POINT
# ═══════════════════════════════════════

if __name__ == "__main__":
    # Initialize extension bridge FIRST
    init_extension_bridge()

    # Start app
    app = FBAutomationApp()

    # Handle window close
    app.protocol("WM_DELETE_WINDOW", app.on_close)

    app.mainloop()
    # Backward compatibility
HybridFacebookUploader = HybridUploader