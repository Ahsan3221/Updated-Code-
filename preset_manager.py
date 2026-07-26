import os
import json
import shutil
from datetime import datetime
from video_editor import (
    get_stealthmax_preset,
    get_balanced_preset,
    get_visual_preset,
    BUILTIN_PRESETS,
)

# ─────────────────────────────────────────────────────────────
# PRESET MANAGER
# ─────────────────────────────────────────────────────────────

class PresetManager:
    """
    Manages video editing presets.
    - Built-in presets (StealthMax, Balanced, Visual)
    - User custom presets (save/load/delete/rename)
    - Import/Export presets as JSON
    """

    PRESETS_DIR = os.path.join(
        os.path.dirname(__file__), "presets"
    )
    PRESETS_FILE = os.path.join(
        os.path.dirname(__file__), "presets", "user_presets.json"
    )

    # ─────────────────────────────────────────────────────────
    # INIT
    # ─────────────────────────────────────────────────────────
    def __init__(self):
        os.makedirs(self.PRESETS_DIR, exist_ok=True)
        self._user_presets = {}
        self._load_from_disk()

    # ─────────────────────────────────────────────────────────
    # DISK I/O
    # ─────────────────────────────────────────────────────────
    def _load_from_disk(self):
        """Load user presets from JSON file."""
        if not os.path.exists(self.PRESETS_FILE):
            self._user_presets = {}
            return

        try:
            with open(self.PRESETS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            self._user_presets = data if isinstance(data, dict) else {}
        except Exception as e:
            print(f"[!] Preset load error: {e}")
            self._user_presets = {}

    def _save_to_disk(self) -> bool:
        """Save user presets to JSON file."""
        try:
            # Write to temp first then rename (atomic write)
            tmp_path = self.PRESETS_FILE + ".tmp"
            with open(tmp_path, "w", encoding="utf-8") as f:
                json.dump(
                    self._user_presets, f,
                    indent=4, ensure_ascii=False
                )
            # Backup old file
            if os.path.exists(self.PRESETS_FILE):
                bak = self.PRESETS_FILE.replace(
                    ".json", "_bak.json"
                )
                shutil.copy2(self.PRESETS_FILE, bak)

            os.replace(tmp_path, self.PRESETS_FILE)
            return True

        except Exception as e:
            print(f"[-] Preset save error: {e}")
            return False

    # ─────────────────────────────────────────────────────────
    # GET PRESETS
    # ─────────────────────────────────────────────────────────
    def get_all_preset_names(self) -> list:
        """
        Returns all preset names.
        Built-in first, then user presets.
        """
        builtin = list(BUILTIN_PRESETS.keys())
        user    = list(self._user_presets.keys())
        return builtin + user

    def get_preset(self, name: str) -> dict:
        """
        Get preset by name.
        Returns StealthMax if not found.
        """
        # Check built-in first
        if name in BUILTIN_PRESETS:
            return BUILTIN_PRESETS[name]()

        # Check user presets
        if name in self._user_presets:
            preset = self._user_presets[name].copy()
            preset["name"] = name
            return preset

        # Fallback
        print(f"[!] Preset '{name}' not found. Using StealthMax.")
        return get_stealthmax_preset()

    def get_builtin_names(self) -> list:
        """Get list of built-in preset names."""
        return list(BUILTIN_PRESETS.keys())

    def get_user_preset_names(self) -> list:
        """Get list of user-created preset names."""
        return list(self._user_presets.keys())

    def is_builtin(self, name: str) -> bool:
        """Check if preset is built-in."""
        return name in BUILTIN_PRESETS

    # ─────────────────────────────────────────────────────────
    # SAVE / UPDATE
    # ─────────────────────────────────────────────────────────
    def save_preset(
        self, name: str, preset_data: dict,
        overwrite: bool = True
    ) -> tuple:
        """
        Save a user preset.
        Returns (success: bool, message: str)
        """
        name = name.strip()

        # Validate name
        if not name:
            return False, "Preset name cannot be empty!"

        if len(name) > 50:
            return False, "Name too long (max 50 chars)!"

        # Prevent overwriting built-ins
        if name in BUILTIN_PRESETS:
            return False, f"'{name}' is a built-in preset. Use a different name!"

        # Check existing
        if name in self._user_presets and not overwrite:
            return False, f"Preset '{name}' already exists!"

        # Clean preset data (remove name key, store separately)
        clean_data = {
            k: v for k, v in preset_data.items()
            if k != "name"
        }

        # Add metadata
        clean_data["_created_on"] = (
            self._user_presets.get(name, {}).get(
                "_created_on",
                datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            )
        )
        clean_data["_updated_on"] = (
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )

        self._user_presets[name] = clean_data

        if self._save_to_disk():
            return True, f"✅ Preset '{name}' saved!"
        else:
            return False, "Failed to save to disk!"

    def update_preset(
        self, name: str, preset_data: dict
    ) -> tuple:
        """Update existing preset."""
        if name not in self._user_presets:
            return False, f"Preset '{name}' not found!"
        return self.save_preset(name, preset_data, overwrite=True)

    # ─────────────────────────────────────────────────────────
    # DELETE
    # ─────────────────────────────────────────────────────────
    def delete_preset(self, name: str) -> tuple:
        """
        Delete a user preset.
        Returns (success: bool, message: str)
        """
        if name in BUILTIN_PRESETS:
            return False, f"Cannot delete built-in preset '{name}'!"

        if name not in self._user_presets:
            return False, f"Preset '{name}' not found!"

        del self._user_presets[name]

        if self._save_to_disk():
            return True, f"🗑️ Preset '{name}' deleted!"
        else:
            return False, "Failed to update disk!"

    # ─────────────────────────────────────────────────────────
    # RENAME
    # ─────────────────────────────────────────────────────────
    def rename_preset(
        self, old_name: str, new_name: str
    ) -> tuple:
        """
        Rename a user preset.
        Returns (success: bool, message: str)
        """
        new_name = new_name.strip()

        if old_name in BUILTIN_PRESETS:
            return False, "Cannot rename built-in preset!"

        if old_name not in self._user_presets:
            return False, f"Preset '{old_name}' not found!"

        if not new_name:
            return False, "New name cannot be empty!"

        if new_name in BUILTIN_PRESETS:
            return False, f"'{new_name}' is a built-in name!"

        if new_name in self._user_presets:
            return False, f"Preset '{new_name}' already exists!"

        # Rename
        self._user_presets[new_name] = self._user_presets.pop(
            old_name
        )
        self._user_presets[new_name]["_updated_on"] = (
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )

        if self._save_to_disk():
            return True, f"✅ Renamed to '{new_name}'!"
        else:
            return False, "Failed to save!"

    # ─────────────────────────────────────────────────────────
    # DUPLICATE
    # ─────────────────────────────────────────────────────────
    def duplicate_preset(
        self, name: str, new_name: str = None
    ) -> tuple:
        """
        Duplicate any preset (built-in or user).
        Returns (success: bool, message: str)
        """
        preset = self.get_preset(name)

        if new_name is None:
            new_name = f"{name} (Copy)"

        # Make name unique
        base_name = new_name
        counter   = 1
        while new_name in self._user_presets:
            new_name = f"{base_name} {counter}"
            counter += 1

        return self.save_preset(new_name, preset, overwrite=False)

    # ─────────────────────────────────────────────────────────
    # IMPORT / EXPORT
    # ─────────────────────────────────────────────────────────
    def export_preset(
        self, name: str, export_path: str
    ) -> tuple:
        """
        Export a preset to a JSON file.
        Returns (success: bool, message: str)
        """
        preset = self.get_preset(name)
        preset["name"] = name

        try:
            with open(export_path, "w", encoding="utf-8") as f:
                json.dump(preset, f, indent=4, ensure_ascii=False)
            return True, f"✅ Exported to {os.path.basename(export_path)}"
        except Exception as e:
            return False, f"Export failed: {e}"

    def import_preset(
        self, import_path: str, overwrite: bool = False
    ) -> tuple:
        """
        Import a preset from JSON file.
        Returns (success: bool, message: str, preset_name: str)
        """
        try:
            with open(import_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            if not isinstance(data, dict):
                return False, "Invalid preset file format!", ""

            name = data.get("name", "").strip()
            if not name:
                # Use filename as name
                name = os.path.splitext(
                    os.path.basename(import_path)
                )[0]

            # Validate preset has required keys
            required = ["speed", "crop_percent"]
            for key in required:
                if key not in data:
                    return (
                        False,
                        f"Invalid preset: missing '{key}' field!",
                        ""
                    )

            success, msg = self.save_preset(
                name, data, overwrite=overwrite
            )
            return success, msg, name

        except json.JSONDecodeError:
            return False, "Invalid JSON file!", ""
        except Exception as e:
            return False, f"Import failed: {e}", ""

    def export_all_presets(self, export_path: str) -> tuple:
        """Export ALL user presets to one JSON file."""
        try:
            with open(export_path, "w", encoding="utf-8") as f:
                json.dump(
                    self._user_presets, f,
                    indent=4, ensure_ascii=False
                )
            count = len(self._user_presets)
            return True, f"✅ Exported {count} presets!"
        except Exception as e:
            return False, f"Export failed: {e}"

    def import_all_presets(
        self, import_path: str, overwrite: bool = False
    ) -> tuple:
        """Import ALL presets from a bulk JSON file."""
        try:
            with open(import_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            if not isinstance(data, dict):
                return False, "Invalid file format!", 0

            imported = 0
            skipped  = 0

            for name, preset_data in data.items():
                if name.startswith("_"):
                    continue
                if name in self._user_presets and not overwrite:
                    skipped += 1
                    continue
                if name in BUILTIN_PRESETS:
                    skipped += 1
                    continue

                self._user_presets[name] = preset_data
                imported += 1

            self._save_to_disk()
            return (
                True,
                f"✅ Imported {imported} presets "
                f"({skipped} skipped)!",
                imported
            )

        except Exception as e:
            return False, f"Import failed: {e}", 0

    # ─────────────────────────────────────────────────────────
    # PRESET SUMMARY
    # ─────────────────────────────────────────────────────────
    def get_preset_summary(self, name: str) -> str:
        """
        Get human-readable summary of preset settings.
        Used for UI tooltips/previews.
        """
        try:
            p = self.get_preset(name)

            # Anti-detect count
            anti_detect_keys = [
                "metadata_spoof", "micro_rotation", "dct_hash_break",
                "rgb_micro_shift", "audio_phase_shift",
                "dynamic_range_shift", "harmonic_micro",
                "film_grain", "border_injection", "micro_warp",
                "auto_trim_edges"
            ]
            ad_count = sum(
                1 for k in anti_detect_keys if p.get(k, False)
            )

            lines = [
                f"📋 {name}",
                f"{'─'*35}",
                f"🛡️ Anti-Detect : {ad_count}/11 ON",
                f"⚡ Speed       : {p.get('speed', 1.03)}x",
                f"✂️  Crop        : {p.get('crop_percent', 96)}%"
                f" [{p.get('crop_position','Center')}]",
                f"🎨 Color Grade : {p.get('color_grade','None')}",
                f"🔊 Volume      : "
                f"{int(p.get('volume', 1.0) * 100)}%",
                f"🔄 Mirror      : "
                f"{'ON' if p.get('mirror_flip') else 'OFF'}",
                f"🎬 Vignette    : "
                f"{'ON' if p.get('vignette') else 'OFF'}",
                f"🔍 Sharpen     : "
                f"{'ON' if p.get('sharpen') else 'OFF'}",
            ]

            # Created/updated dates
            if name in self._user_presets:
                created = self._user_presets[name].get(
                    "_created_on", ""
                )
                updated = self._user_presets[name].get(
                    "_updated_on", ""
                )
                if created:
                    lines.append(f"📅 Created : {created[:10]}")
                if updated:
                    lines.append(f"🔄 Updated : {updated[:10]}")
            else:
                lines.append("⭐ Built-in Preset")

            return "\n".join(lines)

        except Exception as e:
            return f"Preview error: {e}"

    # ─────────────────────────────────────────────────────────
    # RESET
    # ─────────────────────────────────────────────────────────
    def reset_all_user_presets(self) -> tuple:
        """Delete ALL user presets (keep built-ins)."""
        count = len(self._user_presets)
        self._user_presets = {}
        if self._save_to_disk():
            return True, f"✅ Deleted {count} user presets!"
        return False, "Failed!"

    # ─────────────────────────────────────────────────────────
    # STATS
    # ─────────────────────────────────────────────────────────
    def get_stats(self) -> dict:
        """Get preset statistics."""
        return {
            "builtin_count" : len(BUILTIN_PRESETS),
            "user_count"    : len(self._user_presets),
            "total_count"   : (
                len(BUILTIN_PRESETS) + len(self._user_presets)
            ),
            "preset_names"  : self.get_all_preset_names(),
        }


# ─────────────────────────────────────────────────────────────
# GLOBAL SINGLETON
# ─────────────────────────────────────────────────────────────
preset_manager = PresetManager()


# ─────────────────────────────────────────────────────────────
# STANDALONE TEST
# ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 50)
    print("Preset Manager Test")
    print("=" * 50)

    pm = PresetManager()

    # Show stats
    stats = pm.get_stats()
    print(f"\n📊 Stats:")
    print(f"   Built-in : {stats['builtin_count']}")
    print(f"   User     : {stats['user_count']}")
    print(f"   Total    : {stats['total_count']}")

    # Show all presets
    print(f"\n📋 All Presets:")
    for name in pm.get_all_preset_names():
        tag = "⭐ BUILT-IN" if pm.is_builtin(name) else "👤 USER"
        print(f"   {tag}: {name}")

    # Test save
    print(f"\n💾 Testing save...")
    from video_editor import get_stealthmax_preset
    test_preset = get_stealthmax_preset()
    test_preset["speed"] = 1.05
    test_preset["color_grade"] = "Warm"

    ok, msg = pm.save_preset("My Test Preset", test_preset)
    print(f"   Save: {msg}")

    # Test summary
    print(f"\n📄 Preset Summary:")
    print(pm.get_preset_summary("StealthMax v2.0"))

    # Test load
    print(f"\n📥 Testing load...")
    loaded = pm.get_preset("My Test Preset")
    print(f"   Speed: {loaded.get('speed')}")
    print(f"   Grade: {loaded.get('color_grade')}")

    # Test delete
    print(f"\n🗑️ Testing delete...")
    ok, msg = pm.delete_preset("My Test Preset")
    print(f"   Delete: {msg}")

    print(f"\n✅ All tests passed!")