"""
Chrome Profile Cloner
Creates a clone of your existing Chrome profile
so bot can use it without affecting your normal browsing.
"""
import os
import shutil
import subprocess
import time
import psutil


class ChromeProfileCloner:
    def __init__(self):
        self.default_chrome_data = os.path.expandvars(
            r"%LOCALAPPDATA%\Google\Chrome\User Data"
        )
    
    def get_available_profiles(self):
        """Get list of Chrome profiles on system."""
        profiles = []
        if not os.path.exists(self.default_chrome_data):
            return profiles
        
        for item in os.listdir(self.default_chrome_data):
            full_path = os.path.join(
                self.default_chrome_data, item
            )
            if os.path.isdir(full_path):
                if (item.startswith("Profile") or 
                    item == "Default"):
                    profiles.append(item)
        return profiles
    
    def clone_profile(
        self, source_profile, dest_folder, 
        dest_name="Default", ui_log=print
    ):
        """
        Clone a Chrome profile to new location.
        
        Args:
            source_profile: e.g. "Default" or "Profile 1"
            dest_folder: e.g. "C:\\ChromeBot"
            dest_name: Usually "Default"
        
        Returns:
            Path to cloned profile
        """
        try:
            source_path = os.path.join(
                self.default_chrome_data, source_profile
            )
            
            if not os.path.exists(source_path):
                ui_log(
                    f"[-] Source not found: {source_path}"
                )
                return None
            
            ui_log(
                f"[*] Source: {source_path}"
            )
            
            # Create destination
            os.makedirs(dest_folder, exist_ok=True)
            dest_path = os.path.join(dest_folder, dest_name)
            
            # If exists, ask to overwrite
            if os.path.exists(dest_path):
                ui_log(
                    f"[!] Destination exists: {dest_path}"
                )
                ui_log(
                    f"[*] Removing old clone..."
                )
                try:
                    shutil.rmtree(dest_path)
                except Exception as e:
                    ui_log(f"[-] Remove failed: {e}")
                    return None
            
            ui_log(f"[*] Cloning to: {dest_path}")
            ui_log(f"[*] This may take a minute...")
            
            # Kill Chrome first (source profile)
            self._kill_source_chrome(source_path, ui_log)
            time.sleep(2)
            
            # Copy profile
            shutil.copytree(
                source_path,
                dest_path,
                ignore=shutil.ignore_patterns(
                    'Cache*', 'Code Cache', 'GPUCache',
                    'DawnCache', 'ShaderCache', '*.log',
                    'Crashpad', 'BrowserMetrics*',
                    'File System', 'Service Worker'
                )
            )
            
            ui_log(f"[+] ✅ Profile cloned successfully!")
            ui_log(f"[+] Use this path in tool:")
            ui_log(f"    {dest_path}")
            
            return dest_path
        
        except Exception as e:
            ui_log(f"[-] Clone failed: {e}")
            return None
    
    def _kill_source_chrome(self, source_path, ui_log):
        """Kill Chrome using source profile."""
        source_lower = os.path.normpath(source_path).lower()
        killed = 0
        
        try:
            for proc in psutil.process_iter(
                ['name', 'cmdline']
            ):
                try:
                    name = (proc.info['name'] or "").lower()
                    if 'chrome' not in name:
                        continue
                    
                    cmdline = proc.info.get('cmdline') or []
                    cmdline_str = ' '.join(cmdline).lower()
                    
                    if source_lower in cmdline_str:
                        proc.kill()
                        killed += 1
                except Exception:
                    continue
        except Exception:
            pass
        
        if killed > 0:
            ui_log(f"[*] Killed {killed} Chrome process(es)")
    
    def open_cloned_profile(
        self, profile_path, url=None, ui_log=print
    ):
        """Open Chrome with cloned profile for manual login."""
        try:
            base_name = os.path.basename(profile_path)
            parent_dir = os.path.dirname(profile_path)
            
            chrome_exe = self._find_chrome_exe()
            if not chrome_exe:
                ui_log("[-] Chrome.exe not found!")
                return False
            
            cmd = [
                chrome_exe,
                f"--user-data-dir={parent_dir}",
                f"--profile-directory={base_name}",
                "--no-first-run",
                "--no-default-browser-check"
            ]
            
            if url:
                cmd.append(url)
            else:
                cmd.append(
                    "https://business.facebook.com/latest/home"
                )
            
            subprocess.Popen(cmd)
            ui_log(
                f"[+] ✅ Chrome opened with cloned profile!"
            )
            return True
        except Exception as e:
            ui_log(f"[-] Open failed: {e}")
            return False
    
    def _find_chrome_exe(self):
        paths = [
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        ]
        for p in paths:
            if os.path.exists(p):
                return p
        return None


# Global instance
chrome_cloner = ChromeProfileCloner()