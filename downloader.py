import os
import re
import time
import glob
import json
import random
import subprocess
import urllib.request
from urllib.parse import urlparse
import yt_dlp

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False


# ═══════════════════════════════════════════════════════════════
# USER AGENTS POOL
# ═══════════════════════════════════════════════════════════════
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) "
    "Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
]

MOBILE_USER_AGENTS = [
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_1 like Mac OS X) "
    "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 "
    "Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Linux; Android 13; SM-S918B) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) "
    "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 "
    "Mobile/15E148 Safari/604.1",
]


# ═══════════════════════════════════════════════════════════════
# LOGGER
# ═══════════════════════════════════════════════════════════════
class MyLogger:
    def __init__(self, log_func):
        self.log_func = log_func

    def debug(self, msg):
        msg = msg.strip()
        if msg and not msg.startswith("[debug]"):
            self.log_func(f"    [YTDLP] {msg}")

    def info(self, msg):
        msg = msg.strip()
        if msg:
            self.log_func(f"    [INFO] {msg}")

    def warning(self, msg):
        msg = msg.strip()
        if msg:
            self.log_func(f"    ⚠️  [WARN] {msg}")

    def error(self, msg):
        msg = msg.strip()
        if msg:
            self.log_func(f"    ❌ [ERROR] {msg}")


# ═══════════════════════════════════════════════════════════════
# HUMAN BEHAVIOR
# ═══════════════════════════════════════════════════════════════
class HumanBehavior:
    def __init__(self):
        self.session_downloads = 0
        self.session_start = time.time()
        self.last_download_time = 0
        self.consecutive_downloads = 0
        self.error_count = 0

    def get_smart_delay(self, platform="Other", is_bulk=False):
        platform_delays = {
            "YouTube":   (3, 8),
            "TikTok":    (5, 12),
            "Instagram": (8, 20),
            "Facebook":  (10, 25),
            "Twitter/X": (10, 30),
            "Pinterest": (3, 8),
            "Vimeo":     (3, 8),
            "Other":     (5, 15),
        }
        base_min, base_max = platform_delays.get(platform, (5, 15))

        if is_bulk:
            base_min = int(base_min * 1.5)
            base_max = int(base_max * 1.5)

        if self.consecutive_downloads > 5:
            base_min = int(base_min * 1.5)
            base_max = int(base_max * 2)

        if self.consecutive_downloads > 10:
            base_min = int(base_min * 2)
            base_max = int(base_max * 2.5)

        if self.error_count > 0:
            base_min += (self.error_count * 5)
            base_max += (self.error_count * 10)

        return base_min, base_max

    def apply_random_wait(self, platform="Other", ui_log=print, is_bulk=False):
        min_w, max_w = self.get_smart_delay(platform, is_bulk)
        weight_choice = random.random()

        if weight_choice < 0.2:
            wait = random.uniform(min_w, min_w + 3)
        elif weight_choice < 0.7:
            wait = random.uniform(
                min_w + (max_w - min_w) * 0.3,
                min_w + (max_w - min_w) * 0.7
            )
        else:
            wait = random.uniform(
                min_w + (max_w - min_w) * 0.6, max_w
            )

        wait = round(wait, 1)
        ui_log(f"\n[⏱️] 🧑 Human-like wait: {wait}s (Platform: {platform})")

        if wait > 8:
            remaining = wait
            while remaining > 0:
                if remaining > 5:
                    ui_log(f"[⏱️] ⏳ {int(remaining)}s remaining...")
                    time.sleep(min(5, remaining))
                    remaining -= 5
                else:
                    time.sleep(remaining)
                    remaining = 0
        else:
            time.sleep(wait)

        ui_log(f"[⏱️] ✅ Wait complete\n")

    def register_download(self, success=True):
        self.session_downloads += 1
        self.last_download_time = time.time()
        if success:
            self.consecutive_downloads += 1
            self.error_count = max(0, self.error_count - 1)
        else:
            self.error_count += 1
            self.consecutive_downloads = 0

    def should_take_break(self):
        return self.consecutive_downloads >= 15

    def take_break(self, ui_log=print):
        break_time = random.randint(60, 180)
        ui_log(f"\n[🛌] Human break: {break_time}s")
        remaining = break_time
        while remaining > 0:
            if remaining > 30:
                ui_log(f"[🛌] {remaining}s remaining...")
                time.sleep(30)
                remaining -= 30
            else:
                time.sleep(remaining)
                remaining = 0
        self.consecutive_downloads = 0
        ui_log(f"[🛌] ✅ Break complete!\n")


# ═══════════════════════════════════════════════════════════════
# UNIVERSAL DOWNLOADER V2.3
# ═══════════════════════════════════════════════════════════════
class Downloader:
    """Universal Downloader with cookie file support."""

    IMAGE_EXTS = {
        '.jpg', '.jpeg', '.png', '.gif', '.webp',
        '.bmp', '.svg', '.heic', '.heif'
    }

    VIDEO_EXTS = {
        '.mp4', '.mov', '.mkv', '.avi', '.webm',
        '.flv', '.wmv', '.m4v', '.3gp'
    }

    def __init__(self, base_download_path="downloads"):
        self.base_download_path = os.path.join(
            os.path.dirname(__file__), base_download_path
        )
        self.human = HumanBehavior()
        
        # Cookies folder
        self.cookies_dir = os.path.join(
            os.path.dirname(__file__), "cookies"
        )
        os.makedirs(self.cookies_dir, exist_ok=True)

    # ═══════════════════════════════════════════════════════════
    # COOKIE FILE LOADER
    # ═══════════════════════════════════════════════════════════
    def _get_cookie_file(self, platform):
        """
        Get cookie file path for platform.
        Looks in ./cookies/ folder.
        
        Expected files:
        - cookies/instagram_cookies.txt
        - cookies/facebook_cookies.txt
        - cookies/tiktok_cookies.txt
        - cookies/twitter_cookies.txt
        - cookies/youtube_cookies.txt
        """
        cookie_files = {
            "Instagram": "instagram_cookies.txt",
            "Facebook":  "facebook_cookies.txt",
            "TikTok":    "tiktok_cookies.txt",
            "Twitter/X": "twitter_cookies.txt",
            "YouTube":   "youtube_cookies.txt",
        }

        filename = cookie_files.get(platform)
        if not filename:
            return None

        cookie_path = os.path.join(self.cookies_dir, filename)

        if os.path.exists(cookie_path):
            return cookie_path

        return None

    # ═══════════════════════════════════════════════════════════
    # UTILITIES
    # ═══════════════════════════════════════════════════════════
    @staticmethod
    def _get_random_user_agent(mobile=False):
        if mobile:
            return random.choice(MOBILE_USER_AGENTS)
        return random.choice(USER_AGENTS)

    @staticmethod
    def _sanitize_filename(name):
        name = re.sub(r'[\\/:*?"<>|]', '_', name)
        name = re.sub(r'[\s_]+', '_', name).strip('_')
        return name[:180]

    @staticmethod
    def _is_direct_image_url(url):
        parsed = urlparse(url.lower())
        path = parsed.path
        return any(path.endswith(ext) for ext in Downloader.IMAGE_EXTS)

    @staticmethod
    def _is_direct_video_url(url):
        parsed = urlparse(url.lower())
        path = parsed.path
        return any(path.endswith(ext) for ext in Downloader.VIDEO_EXTS)

    def detect_platform(self, url):
        url_lower = url.lower()
        if "youtube.com" in url_lower or "youtu.be" in url_lower:
            return "YouTube"
        elif "tiktok.com" in url_lower:
            return "TikTok"
        elif "instagram.com" in url_lower:
            return "Instagram"
        elif "facebook.com" in url_lower or "fb.watch" in url_lower:
            return "Facebook"
        elif "twitter.com" in url_lower or "x.com" in url_lower:
            return "Twitter/X"
        elif "vimeo.com" in url_lower:
            return "Vimeo"
        elif "reddit.com" in url_lower:
            return "Reddit"
        elif "pinterest.com" in url_lower or "pin.it" in url_lower:
            return "Pinterest"
        elif "tenor.com" in url_lower:
            return "Tenor GIF"
        elif "giphy.com" in url_lower:
            return "Giphy"
        elif "imgur.com" in url_lower:
            return "Imgur"
        else:
            return "Other"

    def detect_content_type(self, url):
        if self._is_direct_image_url(url):
            return 'image'
        if self._is_direct_video_url(url):
            return 'video'

        url_lower = url.lower()

        if "instagram.com" in url_lower:
            if "/reel" in url_lower or "/tv/" in url_lower:
                return 'video'
            elif "/p/" in url_lower:
                return 'auto'
            elif "/stories/" in url_lower:
                return 'auto'

        if "youtube.com" in url_lower or "youtu.be" in url_lower:
            return 'video'
        if "tiktok.com" in url_lower:
            return 'video'
        if "twitter.com" in url_lower or "x.com" in url_lower:
            return 'auto'
        if "facebook.com" in url_lower:
            if "/watch" in url_lower or "fb.watch" in url_lower:
                return 'video'
            return 'auto'
        if "tenor.com" in url_lower or "giphy.com" in url_lower:
            return 'image'
        if "pinterest.com" in url_lower or "pin.it" in url_lower:
            return 'image'

        return 'auto'

    # ═══════════════════════════════════════════════════════════
    # MAIN DOWNLOAD
    # ═══════════════════════════════════════════════════════════
    def download_video(
        self, url, workspace_name="Default",
        ui_log=print, progress_hook=None, skip_wait=False,
    ):
        safe_ws = str(workspace_name).strip().replace(" ", "_").replace("/", "_")

        ui_log(f"\n{'='*55}")
        ui_log(f"[*] 📥 UNIVERSAL DOWNLOADER V2.3")
        ui_log(f"[*] 🍪 Cookie File Support: ENABLED")
        ui_log(f"[*] 🧑 Human Behavior: ENABLED")
        ui_log(f"{'='*55}")
        ui_log(f"[*] URL      : {url[:80]}")
        ui_log(f"[*] Workspace: {safe_ws}")

        platform = self.detect_platform(url)
        content_type = self.detect_content_type(url)

        ui_log(f"[*] Platform : {platform}")
        ui_log(f"[*] Type     : {content_type.upper()}")
        ui_log(f"[*] Session  : {self.human.session_downloads} downloads")

        if not skip_wait and self.human.session_downloads > 0:
            if self.human.should_take_break():
                self.human.take_break(ui_log)
            self.human.apply_random_wait(platform, ui_log)

        base_dir = os.path.join(self.base_download_path, safe_ws)
        video_dir = os.path.join(base_dir, "raw_videos")
        image_dir = os.path.join(base_dir, "raw_images")
        os.makedirs(video_dir, exist_ok=True)
        os.makedirs(image_dir, exist_ok=True)

        try:
            if content_type == 'image' and self._is_direct_image_url(url):
                result = self._download_direct_image(
                    url, image_dir, platform, ui_log
                )
            elif content_type == 'video' and self._is_direct_video_url(url):
                result = self._download_direct_video(
                    url, video_dir, platform, ui_log, progress_hook
                )
            else:
                result = self._download_with_ytdlp(
                    url, video_dir, image_dir, platform,
                    content_type, ui_log, progress_hook
                )

            self.human.register_download(success=result.get('status', False))
            return result

        except Exception:
            self.human.register_download(success=False)
            raise

    # ═══════════════════════════════════════════════════════════
    # YT-DLP DOWNLOADER
    # ═══════════════════════════════════════════════════════════
    def _download_with_ytdlp(
        self, url, video_dir, image_dir, platform,
        content_type, ui_log, progress_hook
    ):
        ydl_opts = self._build_ydl_opts(
            video_dir, platform, progress_hook, ui_log
        )

        title = "Unknown"
        video_id = "unknown"
        file_path = None

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ui_log("[*] 🔍 Fetching metadata...")

                try:
                    info_only = ydl.extract_info(url, download=False)
                    if info_only:
                        title = info_only.get("title", "Unknown")
                        video_id = info_only.get("id", "unknown")
                        duration = info_only.get("duration", 0) or 0

                        entries = info_only.get("entries", None)
                        if entries is not None:
                            entry_count = len(list(entries)) if entries else 0
                            ui_log(f"[+] 📚 Found {entry_count} items")

                        ui_log(f"\n[+] 📺 Title: {title}")
                        if duration:
                            ui_log(
                                f"[+] ⏱️  {int(duration)//60}:"
                                f"{int(duration)%60:02d}"
                            )

                        vcodec = info_only.get("vcodec", "")
                        is_image = (
                            vcodec == "none" or
                            info_only.get("ext", "") in
                            [e.lstrip('.') for e in self.IMAGE_EXTS]
                        )

                        if is_image:
                            ui_log("[*] 🖼️ Detected as IMAGE")
                            content_type = 'image'

                        self._log_quality_info(info_only, ui_log)

                except Exception as info_err:
                    ui_log(f"[!] Metadata warning: {info_err}")

                time.sleep(random.uniform(1, 3))
                ui_log(f"\n[*] ⬇️  Downloading...")

                if content_type == 'image':
                    ydl_opts["outtmpl"] = os.path.join(
                        image_dir, "%(id)s_%(title).80s.%(ext)s"
                    )
                    ydl_opts["format"] = "best"
                    ydl_opts["postprocessors"] = []
                    ydl_opts["merge_output_format"] = None
                    ydl.params.update(ydl_opts)

                dl_info = ydl.extract_info(url, download=True)

                if dl_info:
                    title = dl_info.get("title", title)
                    video_id = dl_info.get("id", video_id)

                    if 'entries' in dl_info and dl_info['entries']:
                        files = []
                        for entry in dl_info['entries']:
                            if entry:
                                try:
                                    p = ydl.prepare_filename(entry)
                                    if os.path.exists(p):
                                        files.append(p)
                                except Exception:
                                    pass

                        if files:
                            file_path = files[0]
                            ui_log(f"[+] Downloaded {len(files)} files")
                    else:
                        try:
                            prepared = ydl.prepare_filename(dl_info)
                            base = os.path.splitext(prepared)[0]

                            for ext in ['.mp4', '.jpg', '.png', '.webp',
                                          '.gif', '.mkv', '.webm']:
                                test_path = base + ext
                                if os.path.exists(test_path):
                                    file_path = test_path
                                    break

                            if not file_path and os.path.exists(prepared):
                                file_path = prepared
                        except Exception as path_err:
                            ui_log(f"[!] Path fallback: {path_err}")

                if not file_path:
                    search_dir = image_dir if content_type == 'image' else video_dir
                    file_path = self._find_downloaded_file(
                        search_dir, video_id, title, ui_log
                    )

        except yt_dlp.utils.DownloadError as de:
            err = str(de)
            ui_log(f"\n⚠️  Failed: {err[:150]}")

            if platform == "Instagram":
                ui_log("\n[*] 🔄 Trying instaloader fallback...")
                return self._download_instagram_alt(
                    url, image_dir, video_dir, ui_log
                )

            self._log_download_error_hint(err, platform, ui_log)
            return {"status": False, "error": err}

        except Exception as e:
            import traceback
            ui_log(f"\n❌ ERROR: {type(e).__name__}: {e}")
            ui_log(traceback.format_exc())
            return {"status": False, "error": str(e)}

        if not file_path or not os.path.exists(file_path):
            for search_dir in [video_dir, image_dir]:
                file_path = self._find_downloaded_file(
                    search_dir, video_id, title, ui_log
                )
                if file_path:
                    break

        if not file_path or not os.path.exists(file_path):
            ui_log(f"[-] ❌ File not found!")
            return {"status": False, "error": "File not found"}

        return self._build_success_result(
            file_path, title, video_id, platform, ui_log
        )

    # ═══════════════════════════════════════════════════════════
    # DIRECT IMAGE
    # ═══════════════════════════════════════════════════════════
    def _download_direct_image(self, url, image_dir, platform, ui_log):
        ui_log(f"\n[*] 🖼️  Direct image download...")

        if not REQUESTS_AVAILABLE:
            return {"status": False, "error": "requests not installed"}

        try:
            parsed = urlparse(url)
            filename = os.path.basename(parsed.path)
            if not filename or '.' not in filename:
                filename = f"image_{int(time.time())}.jpg"

            filename = self._sanitize_filename(filename)

            if not any(filename.lower().endswith(ext) for ext in self.IMAGE_EXTS):
                filename += ".jpg"

            file_path = os.path.join(image_dir, filename)

            headers = {
                "User-Agent": self._get_random_user_agent(),
                "Accept": "image/webp,image/apng,image/*,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9",
            }

            ui_log(f"[*] Downloading: {url[:60]}...")
            response = requests.get(url, headers=headers, stream=True, timeout=30)
            response.raise_for_status()

            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)

            size_mb = os.path.getsize(file_path) / (1024 * 1024)

            resolution = "Unknown"
            if PIL_AVAILABLE:
                try:
                    with Image.open(file_path) as img:
                        w, h = img.size
                        resolution = f"{w}x{h}"
                except Exception:
                    pass

            ui_log(f"\n[+] ✅ IMAGE DOWNLOADED!")
            ui_log(f"[+] 💾 Size: {size_mb:.2f} MB | 📐 {resolution}")

            return {
                "status": True,
                "file_path": file_path,
                "title": filename,
                "video_id": filename,
                "size_mb": round(size_mb, 2),
                "platform": platform,
                "content_type": "image",
            }

        except Exception as e:
            ui_log(f"[-] Failed: {e}")
            return {"status": False, "error": str(e)}

    # ═══════════════════════════════════════════════════════════
    # DIRECT VIDEO
    # ═══════════════════════════════════════════════════════════
    def _download_direct_video(
        self, url, video_dir, platform, ui_log, progress_hook
    ):
        ui_log(f"\n[*] 🎬 Direct video download...")

        if not REQUESTS_AVAILABLE:
            return {"status": False, "error": "requests not installed"}

        try:
            parsed = urlparse(url)
            filename = os.path.basename(parsed.path)
            if not filename or '.' not in filename:
                filename = f"video_{int(time.time())}.mp4"

            filename = self._sanitize_filename(filename)
            file_path = os.path.join(video_dir, filename)

            headers = {
                "User-Agent": self._get_random_user_agent(),
                "Accept": "*/*",
            }

            response = requests.get(url, headers=headers, stream=True, timeout=60)
            response.raise_for_status()

            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)

            size_mb = os.path.getsize(file_path) / (1024 * 1024)
            resolution = self._get_resolution(file_path, ui_log)

            ui_log(f"\n[+] ✅ Downloaded: {size_mb:.2f} MB")

            return {
                "status": True,
                "file_path": file_path,
                "title": filename,
                "video_id": filename,
                "size_mb": round(size_mb, 2),
                "platform": platform,
                "content_type": "video",
            }

        except Exception as e:
            ui_log(f"[-] Failed: {e}")
            return {"status": False, "error": str(e)}

    # ═══════════════════════════════════════════════════════════
    # INSTAGRAM ALTERNATIVE
    # ═══════════════════════════════════════════════════════════
    def _download_instagram_alt(self, url, image_dir, video_dir, ui_log):
        try:
            import instaloader
            ui_log("[*] Using instaloader...")

            match = re.search(r'/(?:p|reel|reels|tv)/([^/?]+)', url)
            if not match:
                return {"status": False, "error": "Invalid Instagram URL"}

            shortcode = match.group(1)

            L = instaloader.Instaloader(
                download_pictures=True,
                download_videos=True,
                download_video_thumbnails=False,
                download_geotags=False,
                download_comments=False,
                save_metadata=False,
                compress_json=False,
                dirname_pattern=image_dir,
                filename_pattern="{shortcode}",
                user_agent=self._get_random_user_agent(mobile=True),
            )

            post = instaloader.Post.from_shortcode(L.context, shortcode)
            L.download_post(post, target=image_dir)

            for f in os.listdir(image_dir):
                if shortcode in f and not f.endswith(('.txt', '.json.xz')):
                    fp = os.path.join(image_dir, f)
                    size_mb = os.path.getsize(fp) / (1024 * 1024)
                    is_video = f.endswith('.mp4')

                    ui_log(f"[+] ✅ Downloaded: {f}")

                    return {
                        "status": True,
                        "file_path": fp,
                        "title": post.caption[:100] if post.caption else shortcode,
                        "video_id": shortcode,
                        "size_mb": round(size_mb, 2),
                        "platform": "Instagram",
                        "content_type": "video" if is_video else "image",
                    }

            return {"status": False, "error": "File not found"}

        except ImportError:
            ui_log("[-] instaloader not installed")
            return {"status": False, "error": "instaloader not installed"}
        except Exception as e:
            ui_log(f"[-] Instaloader error: {e}")

            ui_log("\n" + "="*55)
            ui_log("🔑 INSTAGRAM NEEDS COOKIES FILE!")
            ui_log("="*55)
            ui_log("")
            ui_log("HOW TO FIX:")
            ui_log("")
            ui_log("1️⃣  Install Chrome extension:")
            ui_log("    'Get cookies.txt LOCALLY'")
            ui_log("    (From Chrome Web Store)")
            ui_log("")
            ui_log("2️⃣  Open Instagram in Chrome (logged in)")
            ui_log("")
            ui_log("3️⃣  Click extension icon → Export")
            ui_log("")
            ui_log("4️⃣  Save file as:")
            ui_log(f"    {os.path.join(self.cookies_dir, 'instagram_cookies.txt')}")
            ui_log("")
            ui_log("5️⃣  Try downloading again!")
            ui_log("="*55 + "\n")

            return {"status": False, "error": str(e)}

    # ═══════════════════════════════════════════════════════════
    # YT-DLP OPTIONS (WITH COOKIE FILE!)
    # ═══════════════════════════════════════════════════════════
    def _build_ydl_opts(self, out_dir, platform, progress_hook, ui_log):
        is_mobile = platform in ("Instagram", "TikTok", "Facebook")
        user_agent = self._get_random_user_agent(mobile=is_mobile)

        http_headers = {
            "User-Agent": user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "DNT": "1",
            "Upgrade-Insecure-Requests": "1",
        }

        opts = {
            "format": (
                "bestvideo[ext=mp4][height>=1440]+bestaudio[ext=m4a]/"
                "bestvideo[ext=mp4][height>=1080]+bestaudio[ext=m4a]/"
                "bestvideo[ext=mp4][height>=720]+bestaudio[ext=m4a]/"
                "bestvideo+bestaudio/best"
            ),
            "merge_output_format": "mp4",
            "outtmpl": os.path.join(out_dir, "%(id)s_%(title).80s.%(ext)s"),
            "noplaylist": True,
            "windowsfilenames": True,
            "restrictfilenames": False,
            "retries": 5,
            "fragment_retries": 5,
            "http_headers": http_headers,
            "sleep_interval": random.uniform(2, 4),
            "max_sleep_interval": random.uniform(5, 8),
            "sleep_interval_requests": random.uniform(1, 3),
            "postprocessors": [{
                "key": "FFmpegVideoConvertor",
                "preferedformat": "mp4",
            }],
            "logger": MyLogger(ui_log),
            "quiet": False,
            "verbose": False,
            "geo_bypass": True,
            "geo_bypass_country": "US",
            "nocheckcertificate": False,
        }

        if progress_hook:
            opts["progress_hooks"] = [progress_hook]

        # ══════════════════════════════════════════════
        # 🍪 LOAD COOKIES FROM FILE (if available)
        # ══════════════════════════════════════════════
        cookie_file = self._get_cookie_file(platform)
        if cookie_file:
            opts["cookiefile"] = cookie_file
            ui_log(f"[🍪] ✅ Using cookies: {os.path.basename(cookie_file)}")
        else:
            if platform in ("Instagram", "Facebook", "TikTok", "Twitter/X"):
                ui_log(f"[⚠️] No cookies file for {platform}")
                ui_log(f"[💡] Save cookies to: cookies/{platform.lower()}_cookies.txt")

        # Platform-specific
        if platform == "TikTok":
            opts["http_headers"]["Referer"] = "https://www.tiktok.com/"
            opts["format"] = "bestvideo[ext=mp4]+bestaudio/bestvideo+bestaudio/best"

        elif platform == "Instagram":
            opts["http_headers"]["Referer"] = "https://www.instagram.com/"
            opts["format"] = "best"
            opts["postprocessors"] = []
            opts["sleep_interval"] = random.uniform(3, 6)

        elif platform == "Facebook":
            opts["http_headers"]["Referer"] = "https://www.facebook.com/"
            opts["format"] = "best[ext=mp4]/best"
            opts["sleep_interval"] = random.uniform(3, 6)

        elif platform == "Twitter/X":
            opts["http_headers"]["Referer"] = "https://twitter.com/"
            opts["format"] = "best"
            opts["postprocessors"] = []

        elif platform in ("Tenor GIF", "Giphy"):
            opts["format"] = "best"
            opts["postprocessors"] = []

        elif platform == "Pinterest":
            opts["http_headers"]["Referer"] = "https://www.pinterest.com/"
            opts["format"] = "best"

        elif platform == "YouTube":
            opts["sleep_interval"] = random.uniform(1, 2)

        return opts

    # ═══════════════════════════════════════════════════════════
    # FILE FINDER
    # ═══════════════════════════════════════════════════════════
    def _find_downloaded_file(self, directory, video_id, title, ui_log):
        ui_log("[*] 🔍 Searching...")
        all_exts = list(self.VIDEO_EXTS) + list(self.IMAGE_EXTS)

        if video_id and video_id != "unknown":
            for ext in all_exts:
                pattern = os.path.join(directory, f"*{video_id}*{ext}")
                matches = glob.glob(pattern)
                if matches:
                    return max(matches, key=os.path.getmtime)

        if title:
            safe_title = self._sanitize_filename(title)
            for ext in all_exts:
                exact = os.path.join(directory, f"{safe_title}{ext}")
                if os.path.exists(exact):
                    return exact

                pattern = os.path.join(directory, f"{safe_title[:50]}*{ext}")
                matches = glob.glob(pattern)
                if matches:
                    return max(matches, key=os.path.getmtime)

        all_files = []
        for ext in all_exts:
            all_files.extend(glob.glob(os.path.join(directory, f"*{ext}")))

        if all_files:
            now = time.time()
            recent = [f for f in all_files if (now - os.path.getmtime(f)) < 300]
            if recent:
                return max(recent, key=os.path.getmtime)

        return None

    def _build_success_result(self, file_path, title, video_id, platform, ui_log):
        size_mb = os.path.getsize(file_path) / (1024 * 1024)
        ext = os.path.splitext(file_path)[1].lower()
        is_image = ext in self.IMAGE_EXTS
        content_type = "image" if is_image else "video"

        if is_image and PIL_AVAILABLE:
            try:
                with Image.open(file_path) as img:
                    w, h = img.size
                    resolution = f"{w}x{h}"
            except Exception:
                resolution = "Unknown"
        else:
            resolution = self._get_resolution(file_path, ui_log)

        ui_log(f"\n{'='*55}")
        ui_log(f"[+] ✅ DOWNLOAD COMPLETE!")
        ui_log(f"{'='*55}")
        ui_log(f"[+] 📺 Title: {title}")
        ui_log(f"[+] 🎯 Type: {content_type.upper()}")
        ui_log(f"[+] 💾 Size: {size_mb:.2f} MB")
        ui_log(f"[+] 📐 Res: {resolution}")
        ui_log(f"[+] 📁 Path: {file_path}")

        return {
            "status": True,
            "file_path": file_path,
            "title": title,
            "video_id": video_id,
            "size_mb": round(size_mb, 2),
            "platform": platform,
            "content_type": content_type,
        }

    def _log_quality_info(self, info, ui_log):
        try:
            formats = info.get("formats", [])
            if not formats:
                return

            heights = sorted(set(
                f.get("height", 0) for f in formats if f.get("height")
            ))

            if heights:
                ui_log(f"\n[*] 📊 Available Qualities:")
                for h in reversed(heights[-6:]):
                    marker = " ← BEST" if h == heights[-1] else ""
                    ui_log(f"    ✅ {h}p{marker}")
        except Exception:
            pass

    def _get_resolution(self, file_path, ui_log):
        try:
            result = subprocess.run(
                [
                    "ffprobe", "-v", "error",
                    "-select_streams", "v:0",
                    "-show_entries", "stream=width,height",
                    "-of", "csv=s=x:p=0",
                    file_path,
                ],
                capture_output=True, text=True, timeout=10,
            )
            if result.returncode == 0:
                return result.stdout.strip() or "Unknown"
        except Exception:
            pass
        return "Unknown"

    def _log_download_error_hint(self, error, platform, ui_log):
        err_lower = error.lower()

        if "login" in err_lower or "cookies" in err_lower or "empty media" in err_lower:
            ui_log("\n" + "="*55)
            ui_log(f"🔑 {platform.upper()} NEEDS COOKIES!")
            ui_log("="*55)
            ui_log("")
            ui_log("STEPS TO FIX:")
            ui_log("")
            ui_log("1️⃣  Install Chrome Extension:")
            ui_log("    Search: 'Get cookies.txt LOCALLY'")
            ui_log("    Install from Chrome Web Store")
            ui_log("")
            ui_log(f"2️⃣  Login to {platform} in Chrome")
            ui_log("")
            ui_log("3️⃣  Click extension → Export cookies")
            ui_log("")
            ui_log("4️⃣  Save file here:")
            filename = f"{platform.lower().replace('/', '').replace(' ', '_')}_cookies.txt"
            cookie_path = os.path.join(self.cookies_dir, filename)
            ui_log(f"    {cookie_path}")
            ui_log("")
            ui_log("5️⃣  Try again!")
            ui_log("="*55)
        elif "private" in err_lower:
            ui_log("💡 Private content. Use public URLs.")
        elif "403" in err_lower or "forbidden" in err_lower:
            ui_log(
                f"💡 {platform} blocked (403).\n"
                f"   Wait 30+ min or use VPN"
            )
        elif "429" in err_lower or "rate" in err_lower:
            ui_log("💡 Rate limited! Take a break (30-60 min).")
        elif "404" in err_lower:
            ui_log("💡 Not found. Check URL.")
        elif "ffmpeg" in err_lower:
            ui_log("💡 FFmpeg missing. Install from ffmpeg.org")
        else:
            ui_log(f"💡 Try: pip install -U yt-dlp instaloader")


# ═══════════════════════════════════════════════════════════════
# STANDALONE TEST
# ═══════════════════════════════════════════════════════════════
if __name__ == "__main__":
    print("=" * 55)
    print("Universal Downloader V2.3 - Cookie File Support")
    print("=" * 55)
    print()
    print("✅ Uses cookie files from cookies/ folder")
    print("✅ Works with logged-in Instagram/FB/TikTok")
    print("✅ Human-like behavior")
    print("✅ Videos + Images + Reels")
    print()
    print("📁 Cookies folder location:")
    dl = Downloader()
    print(f"   {dl.cookies_dir}")
    print()
    print("💡 To use with Instagram:")
    print("   1. Install Chrome extension: 'Get cookies.txt LOCALLY'")
    print("   2. Login to Instagram in Chrome")
    print("   3. Export cookies → save as instagram_cookies.txt")
    print("   4. Put in cookies/ folder")
    print()

    test_url = input("Enter URL: ").strip()
    if test_url:
        result = dl.download_video(test_url, "Test", ui_log=print)
        print(f"\n{'='*55}")
        for k, v in result.items():
            print(f"  {k}: {v}")