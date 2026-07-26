import os
import re
import random
import string
import uuid
import subprocess
import shutil
import tempfile
import json
from datetime import datetime, timedelta

# ─────────────────────────────────────────────────────────────
# OPTIONAL IMPORTS
# ─────────────────────────────────────────────────────────────
try:
    import mutagen
    from mutagen.mp4 import MP4, MP4Tags
    MUTAGEN_AVAILABLE = True
except ImportError:
    MUTAGEN_AVAILABLE = False


# ═════════════════════════════════════════════════════════════
# REAL DEVICE DATABASE (100% Accurate Specs from Manufacturer)
# ═════════════════════════════════════════════════════════════
DEVICE_DATABASE = [
    # ═══ APPLE iPhones ═══
    {
        "make"           : "Apple",
        "model"          : "iPhone 15 Pro",
        "model_id"       : "iPhone16,1",
        "software"       : "17.1.2",
        "software_full"  : "iOS 17.1.2",
        "camera_app"     : "Camera 17.1.2",
        "encoder"        : "com.apple.avfoundation",
        "codec"          : "hvc1",  # HEVC
        "color_primaries": "bt2020",
        "handler"        : "Core Media Video",
    },
    {
        "make"           : "Apple",
        "model"          : "iPhone 15",
        "model_id"       : "iPhone15,4",
        "software"       : "17.1.1",
        "software_full"  : "iOS 17.1.1",
        "camera_app"     : "Camera 17.1.1",
        "encoder"        : "com.apple.avfoundation",
        "codec"          : "hvc1",
        "color_primaries": "bt709",
        "handler"        : "Core Media Video",
    },
    {
        "make"           : "Apple",
        "model"          : "iPhone 14 Pro Max",
        "model_id"       : "iPhone15,3",
        "software"       : "17.0.3",
        "software_full"  : "iOS 17.0.3",
        "camera_app"     : "Camera 17.0.3",
        "encoder"        : "com.apple.avfoundation",
        "codec"          : "hvc1",
        "color_primaries": "bt2020",
        "handler"        : "Core Media Video",
    },
    {
        "make"           : "Apple",
        "model"          : "iPhone 14",
        "model_id"       : "iPhone14,7",
        "software"       : "16.6.1",
        "software_full"  : "iOS 16.6.1",
        "camera_app"     : "Camera 16.6.1",
        "encoder"        : "com.apple.avfoundation",
        "codec"          : "hvc1",
        "color_primaries": "bt709",
        "handler"        : "Core Media Video",
    },
    {
        "make"           : "Apple",
        "model"          : "iPhone 13",
        "model_id"       : "iPhone14,5",
        "software"       : "16.5.1",
        "software_full"  : "iOS 16.5.1",
        "camera_app"     : "Camera 16.5.1",
        "encoder"        : "com.apple.avfoundation",
        "codec"          : "hvc1",
        "color_primaries": "bt709",
        "handler"        : "Core Media Video",
    },

    # ═══ SAMSUNG Galaxy ═══
    {
        "make"           : "samsung",
        "model"          : "SM-S918B",
        "device_name"    : "Galaxy S23 Ultra",
        "software"       : "S918BXXU3AWJ2",
        "software_full"  : "One UI 6.0 / Android 14",
        "camera_app"     : "Camera 14.0.15.13",
        "encoder"        : "OMX.qcom.video.encoder.avc",
        "codec"          : "avc1",  # H.264
        "color_primaries": "bt709",
        "handler"        : "SoundHandle",
    },
    {
        "make"           : "samsung",
        "model"          : "SM-S911B",
        "device_name"    : "Galaxy S23",
        "software"       : "S911BXXS3BWJ1",
        "software_full"  : "One UI 6.0 / Android 14",
        "camera_app"     : "Camera 14.0.15.13",
        "encoder"        : "OMX.qcom.video.encoder.avc",
        "codec"          : "avc1",
        "color_primaries": "bt709",
        "handler"        : "SoundHandle",
    },
    {
        "make"           : "samsung",
        "model"          : "SM-S908B",
        "device_name"    : "Galaxy S22 Ultra",
        "software"       : "S908BXXU4CWH5",
        "software_full"  : "One UI 5.1 / Android 13",
        "camera_app"     : "Camera 13.1.03.5",
        "encoder"        : "OMX.qcom.video.encoder.avc",
        "codec"          : "avc1",
        "color_primaries": "bt709",
        "handler"        : "SoundHandle",
    },
    {
        "make"           : "samsung",
        "model"          : "SM-G998B",
        "device_name"    : "Galaxy S21 Ultra",
        "software"       : "G998BXXU5DVLA",
        "software_full"  : "One UI 5.1 / Android 13",
        "camera_app"     : "Camera 13.1.00.75",
        "encoder"        : "OMX.Exynos.AVC.Encoder",
        "codec"          : "avc1",
        "color_primaries": "bt709",
        "handler"        : "SoundHandle",
    },

    # ═══ GOOGLE Pixel ═══
    {
        "make"           : "Google",
        "model"          : "Pixel 8 Pro",
        "model_id"       : "husky",
        "software"       : "UD1A.231105.004",
        "software_full"  : "Android 14",
        "camera_app"     : "GoogleCamera 9.2.113",
        "encoder"        : "OMX.google.h264.encoder",
        "codec"          : "avc1",
        "color_primaries": "bt709",
        "handler"        : "VideoHandle",
    },
    {
        "make"           : "Google",
        "model"          : "Pixel 7 Pro",
        "model_id"       : "cheetah",
        "software"       : "TQ3A.230901.001",
        "software_full"  : "Android 14",
        "camera_app"     : "GoogleCamera 9.1.098",
        "encoder"        : "OMX.google.h264.encoder",
        "codec"          : "avc1",
        "color_primaries": "bt709",
        "handler"        : "VideoHandle",
    },
    {
        "make"           : "Google",
        "model"          : "Pixel 7",
        "model_id"       : "panther",
        "software"       : "TQ3A.230805.001",
        "software_full"  : "Android 14",
        "camera_app"     : "GoogleCamera 9.0.115",
        "encoder"        : "OMX.google.h264.encoder",
        "codec"          : "avc1",
        "color_primaries": "bt709",
        "handler"        : "VideoHandle",
    },

    # ═══ OnePlus ═══
    {
        "make"           : "OnePlus",
        "model"          : "CPH2449",
        "device_name"    : "OnePlus 11",
        "software"       : "CPH2449_14.0.0.700",
        "software_full"  : "OxygenOS 14 / Android 14",
        "camera_app"     : "OnePlusCamera 5.0.18",
        "encoder"        : "OMX.qcom.video.encoder.avc",
        "codec"          : "avc1",
        "color_primaries": "bt709",
        "handler"        : "SoundHandle",
    },
]


# ═════════════════════════════════════════════════════════════
# USA CITIES DATABASE (15 Major Cities, Real GPS)
# ═════════════════════════════════════════════════════════════
USA_CITIES = [
    {"city": "New York",      "state": "NY", "lat": 40.7128,  "lon": -74.0060},
    {"city": "Los Angeles",   "state": "CA", "lat": 34.0522,  "lon": -118.2437},
    {"city": "Chicago",       "state": "IL", "lat": 41.8781,  "lon": -87.6298},
    {"city": "Houston",       "state": "TX", "lat": 29.7604,  "lon": -95.3698},
    {"city": "Phoenix",       "state": "AZ", "lat": 33.4484,  "lon": -112.0740},
    {"city": "Philadelphia",  "state": "PA", "lat": 39.9526,  "lon": -75.1652},
    {"city": "San Antonio",   "state": "TX", "lat": 29.4241,  "lon": -98.4936},
    {"city": "San Diego",     "state": "CA", "lat": 32.7157,  "lon": -117.1611},
    {"city": "Dallas",        "state": "TX", "lat": 32.7767,  "lon": -96.7970},
    {"city": "Miami",         "state": "FL", "lat": 25.7617,  "lon": -80.1918},
    {"city": "Seattle",       "state": "WA", "lat": 47.6062,  "lon": -122.3321},
    {"city": "Denver",        "state": "CO", "lat": 39.7392,  "lon": -104.9903},
    {"city": "Boston",        "state": "MA", "lat": 42.3601,  "lon": -71.0589},
    {"city": "Atlanta",       "state": "GA", "lat": 33.7490,  "lon": -84.3880},
    {"city": "Las Vegas",     "state": "NV", "lat": 36.1699,  "lon": -115.1398},
]


# ═════════════════════════════════════════════════════════════
# COLOR GRADE PRESETS
# ═════════════════════════════════════════════════════════════
COLOR_GRADES = {
    "None"      : "",
    "Warm"      : "eq=brightness=0.02:saturation=1.15:contrast=1.05,"
                  "colorbalance=rs=0.05:gs=0.0:bs=-0.03",
    "Cool"      : "eq=brightness=0.01:saturation=1.1:contrast=1.03,"
                  "colorbalance=rs=-0.03:gs=0.0:bs=0.06",
    "Cinematic" : "eq=brightness=-0.02:saturation=0.9:contrast=1.15,"
                  "colorbalance=rs=0.02:gs=-0.01:bs=-0.02,"
                  "vignette=PI/4",
    "Vintage"   : "eq=brightness=0.01:saturation=0.75:contrast=0.95,"
                  "colorbalance=rs=0.06:gs=0.02:bs=-0.06,"
                  "noise=alls=8:allf=t",
    "Vibrant"   : "eq=brightness=0.02:saturation=1.3:contrast=1.08",
}


# ═════════════════════════════════════════════════════════════
# PERSONA GENERATOR (NEW)
# ═════════════════════════════════════════════════════════════

def generate_workspace_persona() -> dict:
    """
    Generate a FIXED identity for a workspace.
    - Random device from real list
    - Random USA city
    - Locked - stays same for all videos of this workspace
    """
    device = random.choice(DEVICE_DATABASE)
    city   = random.choice(USA_CITIES)

    persona = {
        # Device info (LOCKED)
        "make"           : device["make"],
        "model"          : device["model"],
        "device_name"    : device.get(
            "device_name", device["model"]
        ),
        "software"       : device["software"],
        "software_full"  : device["software_full"],
        "camera_app"     : device["camera_app"],
        "encoder"        : device["encoder"],
        "codec"          : device["codec"],
        "color_primaries": device["color_primaries"],
        "handler"        : device["handler"],

        # Location info (LOCKED)
        "city"           : city["city"],
        "state"          : city["state"],
        "country"        : "USA",
        "gps_base_lat"   : city["lat"],
        "gps_base_lon"   : city["lon"],
        "gps_variance"   : 0.02,  # ~2km realistic movement

        # Metadata (LOCKED)
        "created_on"     : datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        ),
    }

    return persona


def get_persona_display_summary(persona: dict) -> str:
    """Get human-readable persona summary."""
    if not persona:
        return "No persona set"

    return (
        f"📱 {persona.get('device_name', 'Unknown')}\n"
        f"💾 {persona.get('software_full', 'Unknown')}\n"
        f"📸 {persona.get('camera_app', 'Unknown')}\n"
        f"📍 {persona.get('city', 'Unknown')}, "
        f"{persona.get('state', '')}, "
        f"{persona.get('country', 'USA')}"
    )


# ═════════════════════════════════════════════════════════════
# UTILITY HELPERS
# ═════════════════════════════════════════════════════════════

def generate_random_string(length=8) -> str:
    chars = string.ascii_letters + string.digits
    return ''.join(random.choice(chars) for _ in range(length))


def generate_realistic_date(days_back=30) -> str:
    """
    Realistic creation time - within last 30 days.
    Business hours weighted (real users record more during day).
    """
    now = datetime.now()

    # Random day in last 30 days
    day_offset = random.randint(0, days_back)

    # Business hours weighted (8am-11pm most likely)
    hour = random.choices(
        range(24),
        weights=[
            1, 1, 1, 1, 1, 1,  # 12am-6am (rare)
            2, 3, 5, 6, 7, 8,  # 6am-12pm (increasing)
            9, 9, 8, 8, 7, 7,  # 12pm-6pm (peak)
            8, 8, 7, 6, 4, 2   # 6pm-12am (evening)
        ]
    )[0]

    delta = timedelta(
        days    = day_offset,
        hours   = now.hour - hour,
        minutes = random.randint(0, 59),
        seconds = random.randint(0, 59),
    )

    result = now - delta
    return result.strftime("%Y-%m-%dT%H:%M:%SZ")


def generate_persona_gps(persona: dict) -> tuple:
    """
    Generate GPS coords within persona's city area.
    Small realistic variation (~2km).
    """
    base_lat = persona.get("gps_base_lat", 40.7128)
    base_lon = persona.get("gps_base_lon", -74.0060)
    variance = persona.get("gps_variance", 0.02)

    lat = base_lat + random.uniform(-variance, variance)
    lon = base_lon + random.uniform(-variance, variance)

    return round(lat, 6), round(lon, 6)


# ═════════════════════════════════════════════════════════════
# FFMPEG CHECK
# ═════════════════════════════════════════════════════════════

def check_ffmpeg(ui_log=print) -> bool:
    try:
        result = subprocess.run(
            ["ffmpeg", "-version"],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0:
            version = result.stdout.split('\n')[0]
            ui_log(f"[*] FFmpeg OK: {version[:70]}")
            return True
        return False
    except FileNotFoundError:
        ui_log("[-] FFmpeg NOT FOUND! Install from ffmpeg.org")
        return False
    except Exception as e:
        ui_log(f"[-] FFmpeg error: {e}")
        return False


# ═════════════════════════════════════════════════════════════
# VIDEO PROBE
# ═════════════════════════════════════════════════════════════

def probe_video_info(input_path: str, ui_log=print) -> dict:
    ui_log(f"[*] Probing: {os.path.basename(input_path)}")
    try:
        cmd = [
            "ffprobe", "-v", "error",
            "-select_streams", "v:0",
            "-show_entries",
            "stream=width,height,r_frame_rate,duration",
            "-of", "default=noprint_wrappers=1:nokey=0",
            input_path
        ]
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=20
        )
        if result.returncode != 0:
            return {}

        info = {}
        for line in result.stdout.strip().splitlines():
            if "=" in line:
                key, val = line.split("=", 1)
                info[key.strip()] = val.strip()

        width   = int(info.get("width",  1920))
        height  = int(info.get("height", 1080))
        fps_raw = info.get("r_frame_rate", "30/1")

        try:
            num, den = fps_raw.split("/")
            fps = round(int(num) / int(den), 2)
        except Exception:
            fps = 30.0

        duration = float(info.get("duration", 0) or 0)
        ui_log(
            f"    ✅ {width}x{height} @ {fps}fps "
            f"| {duration:.1f}s"
        )
        return {
            "width": width, "height": height,
            "fps": fps, "duration": duration
        }
    except Exception as e:
        ui_log(f"[-] Probe error: {e}")
        return {}


# ═════════════════════════════════════════════════════════════
# ANTI-DETECT FILTER BUILDERS (SAFE VERSIONS)
# ═════════════════════════════════════════════════════════════

def build_dct_hash_breaker() -> str:
    """Technique 1: Light noise breaks perceptual hash"""
    strength = random.randint(1, 2)
    return f"noise=alls={strength}:allf=t"


def build_micro_rotation(angle: float = None) -> str:
    """Technique 2: Micro Rotation - invisible"""
    if angle is None:
        angle = round(random.uniform(0.05, 0.2), 3)
    rad = angle * 3.14159 / 180
    return f"rotate={rad}:fillcolor=black@0:bilinear=1"


def build_rgb_micro_shift() -> str:
    """Technique 3: RGB Channel Micro Shift"""
    r_shift = random.choice([-1, 0, 1])
    g_shift = random.choice([-1, 0, 1])
    b_shift = random.choice([-1, 0, 1])
    return (
        f"colorchannelmixer="
        f"rr=1:rg={r_shift*0.004}:rb=0:"
        f"gr=0:gg=1:gb={g_shift*0.004}:"
        f"br={b_shift*0.004}:bg=0:bb=1"
    )


def build_border_injection(width: int, height: int) -> str:
    """Technique 4: 1-2px Border Injection"""
    px = random.randint(1, 2)
    return (
        f"pad={width + px*2}:{height + px*2}:{px}:{px}:black"
    )


def build_film_grain(intensity: int = 3) -> str:
    """Technique 5: Film Grain (Natural Camera Noise)"""
    strength = max(1, min(10, intensity))
    return f"noise=alls={strength}:allf=t+u"


def build_micro_warp(width: int, height: int) -> str:
    """Technique 7: Perspective Micro Warp - SAFE"""
    shift = random.randint(1, 3)
    x0 = 0;     y0 = random.randint(0, shift)
    x1 = width; y1 = random.randint(0, shift)
    x2 = 0;     y2 = height - random.randint(0, shift)
    x3 = width; y3 = height - random.randint(0, shift)
    return (
        f"perspective="
        f"x0={x0}:y0={y0}:"
        f"x1={x1}:y1={y1}:"
        f"x2={x2}:y2={y2}:"
        f"x3={x3}:y3={y3}:"
        f"interpolation=linear"
    )


def build_vignette(intensity: float = 0.3) -> str:
    """Technique 8: Vignette Effect"""
    angle = round(random.uniform(0.2, 0.5), 2)
    return f"vignette=PI/{round(1/angle, 1)}"


def build_blur_logo_filter(
    position: str, width: int, height: int, ui_log=print
) -> str:
    """Logo blur overlay filter."""
    logo_w = max(100, int(width  * 0.15)) & ~1
    logo_h = max(50,  int(height * 0.08)) & ~1
    margin = 10

    positions = {
        "Top-Left"    : (margin, margin),
        "Top-Right"   : (width  - logo_w - margin, margin),
        "Bottom-Left" : (margin, height - logo_h - margin),
        "Bottom-Right": (
            width  - logo_w - margin,
            height - logo_h - margin
        ),
    }

    if position not in positions:
        return ""

    x, y = positions[position]
    return (
        f"split=2[base][blur_in];"
        f"[blur_in]crop={logo_w}:{logo_h}:{x}:{y},"
        f"boxblur=10:3[blurred];"
        f"[base][blurred]overlay={x}:{y}"
    )


def build_sharpen_filter(amount: float = 0.5) -> str:
    """Unsharp mask for sharpening."""
    return f"unsharp=5:5:{amount}:5:5:0"


def build_zoom_effect(duration: float = 10.0) -> str:
    """Subtle slow zoom in effect."""
    return (
        f"zoompan=z='min(zoom+0.0005,1.05)':"
        f"d={int(duration*25)}:s=hd1080"
    )


# ═════════════════════════════════════════════════════════════
# AUDIO FILTERS
# ═════════════════════════════════════════════════════════════

def build_audio_phase_shift() -> str:
    """Technique 10: Audio Phase Shift"""
    delay_ms = random.randint(1, 3)
    return f"adelay={delay_ms}|{delay_ms},aresample=async=1"


def build_dynamic_range_shift() -> str:
    """Technique 11: Dynamic Range Shift"""
    attack = round(random.uniform(0.3, 0.8), 2)
    decay  = round(random.uniform(0.8, 1.5), 2)
    return (
        f"compand="
        f"attacks={attack}:"
        f"decays={decay}:"
        f"points=-80/-80|-12/-12|0/-3|20/0:"
        f"soft-knee=6:"
        f"gain=0:"
        f"volume=-90:"
        f"delay=0"
    )


def build_silence_padding() -> str:
    """Technique 12: Silence Padding"""
    delay_ms = random.randint(100, 300)
    return f"adelay={delay_ms}|{delay_ms}"


def build_harmonic_micro() -> str:
    """Technique 13: Micro Volume Variation"""
    micro = round(random.uniform(1.001, 1.004), 4)
    return f"volume={micro}"


def build_audio_filters(
    volume: float = 1.0,
    speed: float  = 1.03,
    pitch_shift: float = 0.5,
    phase_shift: bool = True,
    dynamic_range: bool = True,
    silence_pad: bool = False,
    harmonic: bool = True,
    bass_boost: bool = False,
    fade: bool = False,
    remove_audio: bool = False,
    duration: float = 0,
) -> str:
    """Build complete audio filter chain."""

    if remove_audio:
        return "anull"

    a_filters = []

    atempo = round(speed, 3)
    if atempo != 1.0:
        atempo = max(0.5, min(2.0, atempo))
        a_filters.append(f"atempo={atempo}")

    vol = round(max(0.1, min(3.0, volume)), 2)
    if vol != 1.0:
        a_filters.append(f"volume={vol}")

    if bass_boost:
        a_filters.append(
            "equalizer=f=100:width_type=o:width=2:g=3"
        )

    if phase_shift:
        a_filters.append(build_audio_phase_shift())

    if dynamic_range:
        a_filters.append(build_dynamic_range_shift())

    if harmonic:
        a_filters.append(build_harmonic_micro())

    if silence_pad:
        a_filters.append(build_silence_padding())

    if fade and duration > 2:
        fade_dur = min(1.0, duration * 0.05)
        a_filters.append(
            f"afade=t=in:st=0:d={fade_dur},"
            f"afade=t=out:st={duration - fade_dur}"
            f":d={fade_dur}"
        )

    return ",".join(a_filters) if a_filters else "anull"


# ═════════════════════════════════════════════════════════════
# METADATA SPOOFING - USES PERSONA (REALISTIC ONLY!)
# ═════════════════════════════════════════════════════════════

def build_metadata_from_persona(persona: dict) -> dict:
    """
    Build REALISTIC metadata using workspace persona.
    Only fields that REAL phone videos contain.
    NO title, artist, album, track, genre etc!
    """
    if not persona:
        # Fallback if no persona
        persona = generate_workspace_persona()

    # Generate realistic GPS within persona's city
    lat, lon = generate_persona_gps(persona)

    # Realistic creation time
    creation_time = generate_realistic_date(30)

    # Build minimal, REAL phone-like metadata
    metadata = {
        # ═══ DEVICE INFO (from persona - LOCKED) ═══
        "make"             : persona["make"],
        "model"            : persona["model"],

        # Software / OS info
        "com.apple.quicktime.software"
            if persona["make"] == "Apple"
            else "software": persona["software"],

        # ═══ TIMESTAMPS (realistic) ═══
        "creation_time"    : creation_time,
        "date"             : creation_time,

        # ═══ LOCATION (real phone format) ═══
        # ISO 6709 format: "+40.7128-074.0060+000/"
        "location"         : f"+{lat:.4f}{lon:+.4f}+000/",
        "com.apple.quicktime.location.ISO6709"
            if persona["make"] == "Apple"
            else "location-eng": f"+{lat:.4f}{lon:+.4f}+000/",
    }

    # ═══ Apple-specific tags ═══
    if persona["make"] == "Apple":
        metadata.update({
            "com.apple.quicktime.make"    : persona["make"],
            "com.apple.quicktime.model"   : persona["model"],
            "com.apple.quicktime.creationdate": creation_time,
        })

    # ═══ Android-specific tags ═══
    else:
        metadata.update({
            "handler_name"    : persona.get(
                "handler", "SoundHandle"
            ),
            "encoder"         : persona["encoder"],
        })

    return metadata


def apply_mutagen_metadata(
    file_path: str, metadata: dict, persona: dict, ui_log=print
) -> bool:
    """Apply persona metadata using mutagen (MP4 level)."""
    if not MUTAGEN_AVAILABLE:
        ui_log(
            "[!] mutagen not installed. Skipping deep metadata."
        )
        return False

    try:
        video = MP4(file_path)

        # Only realistic tags - no title/artist/album!
        # Real phones don't set these

        # Clear any existing fake tags first
        for tag in [
            "\xa9nam", "\xa9ART", "\xa9alb",
            "\xa9wrt", "\xa9gen", "cprt", "trkn"
        ]:
            if tag in video:
                del video[tag]

        # Set only real phone tags
        creation_date = metadata.get(
            "creation_time",
            datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
        )

        try:
            video["\xa9day"] = [creation_date[:10]]
        except Exception:
            pass

        try:
            video["\xa9too"] = [
                persona.get("camera_app", "Camera")
            ]
        except Exception:
            pass

        video.save()
        ui_log(
            "[+] ✅ Persona metadata applied (realistic only)"
        )
        return True

    except Exception as e:
        ui_log(f"[-] Mutagen error: {e}")
        return False


# ═════════════════════════════════════════════════════════════
# GOP & ENCODING RANDOMIZER
# ═════════════════════════════════════════════════════════════

def get_random_encoding_params() -> dict:
    """Randomize encoding parameters."""
    return {
        "crf"   : random.randint(18, 23),
        "gop"   : random.randint(60, 150),
        "bf"    : random.randint(2, 4),
        "refs"  : random.randint(1, 4),
        "subq"  : random.randint(6, 9),
        "preset": random.choice(["medium", "slow", "fast"]),
    }


# ═════════════════════════════════════════════════════════════
# TRIM HELPER
# ═════════════════════════════════════════════════════════════

def parse_time_to_seconds(time_str: str) -> float:
    """Parse HH:MM:SS or MM:SS to seconds."""
    try:
        parts = str(time_str).strip().split(":")
        if len(parts) == 3:
            return (
                int(parts[0]) * 3600 +
                int(parts[1]) * 60 +
                float(parts[2])
            )
        elif len(parts) == 2:
            return int(parts[0]) * 60 + float(parts[1])
        else:
            return float(parts[0])
    except Exception:
        return 0.0


# ═════════════════════════════════════════════════════════════
# MAIN PROCESSING FUNCTION
# ═════════════════════════════════════════════════════════════

def make_video_unique(
    input_path : str,
    output_path: str,
    ui_log      = print,
    preset     : dict = None,
    persona    : dict = None,
) -> bool:
    """
    Anti-Detect Video Processing Pipeline V3.0
    Uses WORKSPACE PERSONA for consistent identity.
    """
    import time

    ui_log(f"\n{'='*55}")
    ui_log(f"[*] 🎬 VIDEO PROCESSING V3.0 - Persona Mode")
    ui_log(f"{'='*55}")

    if preset is None:
        preset = get_stealthmax_preset()
        ui_log("[*] Using StealthMax Default Preset")
    else:
        ui_log(
            f"[*] Using Preset: "
            f"{preset.get('name','Custom')}"
        )

    # Load or generate persona
    if persona is None:
        persona = generate_workspace_persona()
        ui_log("[!] No persona provided - generated random")
    else:
        ui_log(
            f"[*] Using Workspace Persona: "
            f"{persona.get('device_name', 'Unknown')}"
        )

    if not check_ffmpeg(ui_log):
        return False

    if not os.path.exists(input_path):
        ui_log(f"[-] Input not found: {input_path}")
        return False

    size_mb = os.path.getsize(input_path) / (1024 * 1024)
    ui_log(
        f"[+] Input : {os.path.basename(input_path)} "
        f"({size_mb:.1f}MB)"
    )

    vid_info = probe_video_info(input_path, ui_log)
    src_w    = vid_info.get("width",    1920)
    src_h    = vid_info.get("height",   1080)
    src_dur  = vid_info.get("duration", 0.0)
    src_fps  = vid_info.get("fps",      30.0)

    out_dir = os.path.dirname(output_path)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)

    # Build metadata from persona
    metadata = build_metadata_from_persona(persona)

    ui_log(
        f"[+] 📱 Device : {persona['make']} "
        f"{persona.get('device_name', persona['model'])}"
    )
    ui_log(
        f"[+] 💾 Software: {persona.get('software_full', 'N/A')}"
    )
    ui_log(
        f"[+] 📍 Location: {persona.get('city', 'N/A')}, "
        f"{persona.get('state', '')}, USA"
    )
    lat, lon = generate_persona_gps(persona)
    ui_log(f"[+] 🌐 GPS Coord: {lat}, {lon}")

    enc = get_random_encoding_params()
    if preset.get("crf_override"):
        enc["crf"] = preset["crf_override"]
    ui_log(
        f"[+] 🎬 Encoding: CRF={enc['crf']} GOP={enc['gop']} "
        f"refs={enc['refs']} preset={enc['preset']}"
    )

    # ════════════════════════════════════════════════════════
    # BUILD VIDEO FILTER CHAIN
    # ════════════════════════════════════════════════════════
    ui_log(f"\n[*] 🔧 Building filter chain...")

    simple_filters   = []
    has_logo_blur    = False
    logo_blur_filter = ""

    # Speed
    speed = float(preset.get("speed", 1.03))
    pts_v = round(1.0 / speed, 4)
    if speed != 1.0:
        simple_filters.append(f"setpts={pts_v}*PTS")
        ui_log(f"    ➕ Speed: {speed}x")

    # Trim
    trim_start = parse_time_to_seconds(
        preset.get("trim_start", "00:00:00")
    )
    trim_end = parse_time_to_seconds(
        preset.get("trim_end", "00:00:00")
    )

    if preset.get("auto_trim_edges", True):
        auto_trim  = round(random.uniform(0.4, 0.8), 1)
        trim_start = max(trim_start, auto_trim)
        ui_log(f"    ➕ Auto Edge Trim: {auto_trim}s")

    # Crop
    crop_pct = float(preset.get("crop_percent", 96)) / 100.0
    crop_pos = preset.get("crop_position", "Center")

    crop_w = int(src_w * crop_pct) & ~1
    crop_h = int(src_h * crop_pct) & ~1
    cx_max = src_w - crop_w
    cy_max = src_h - crop_h

    if crop_pos == "Center":
        crop_x = cx_max // 2; crop_y = cy_max // 2
    elif crop_pos == "Top":
        crop_x = cx_max // 2; crop_y = 0
    elif crop_pos == "Bottom":
        crop_x = cx_max // 2; crop_y = cy_max
    elif crop_pos == "Left":
        crop_x = 0;           crop_y = cy_max // 2
    elif crop_pos == "Right":
        crop_x = cx_max;      crop_y = cy_max // 2
    else:
        crop_x = cx_max // 2; crop_y = cy_max // 2

    simple_filters.append(
        f"crop={crop_w}:{crop_h}:{crop_x}:{crop_y}"
    )
    ui_log(
        f"    ➕ Crop: {crop_pct*100:.0f}% [{crop_pos}]"
        f" → {crop_w}x{crop_h}"
    )

    # Micro Rotation
    if preset.get("micro_rotation", True):
        simple_filters.append(build_micro_rotation())
        ui_log(f"    ➕ Micro Rotation")

    # Mirror Flip
    if preset.get("mirror_flip", False):
        simple_filters.append("hflip")
        ui_log(f"    ➕ Mirror Flip")

    # Color Grade
    grade = preset.get("color_grade", "None")
    if grade and grade != "None" and grade in COLOR_GRADES:
        grade_filter = COLOR_GRADES[grade]
        if grade_filter:
            simple_filters.append(grade_filter)
            ui_log(f"    ➕ Color Grade: {grade}")
    else:
        brightness = float(preset.get("brightness", 0.01))
        contrast   = float(preset.get("contrast",   1.01))
        saturation = float(preset.get("saturation", 1.01))
        simple_filters.append(
            f"eq=brightness={brightness}:"
            f"saturation={saturation}:"
            f"contrast={contrast}"
        )
        ui_log(
            f"    ➕ Color Tweak "
            f"(b={brightness} s={saturation} c={contrast})"
        )

    # RGB Micro Shift
    if preset.get("rgb_micro_shift", True):
        simple_filters.append(build_rgb_micro_shift())
        ui_log(f"    ➕ RGB Micro Shift")

    # DCT Hash Breaker (safe noise)
    if preset.get("dct_hash_break", True):
        simple_filters.append(build_dct_hash_breaker())
        ui_log(f"    ➕ Hash Breaker")

    # Film Grain
    if preset.get("film_grain", True):
        grain_intensity = int(
            preset.get("grain_intensity", 3)
        )
        simple_filters.append(
            build_film_grain(grain_intensity)
        )
        ui_log(f"    ➕ Film Grain: {grain_intensity}/10")

    # Vignette
    if preset.get("vignette", False):
        simple_filters.append(build_vignette())
        ui_log(f"    ➕ Vignette")

    # Sharpen
    if preset.get("sharpen", False):
        sharp_amount = float(
            preset.get("sharpen_amount", 0.5)
        )
        simple_filters.append(
            build_sharpen_filter(sharp_amount)
        )
        ui_log(f"    ➕ Sharpen: {sharp_amount}")

    # Zoom
    if preset.get("zoom_effect", False):
        simple_filters.append(build_zoom_effect(src_dur))
        ui_log(f"    ➕ Zoom Effect")

    # Micro Warp
    if preset.get("micro_warp", True):
        simple_filters.append(
            build_micro_warp(crop_w, crop_h)
        )
        ui_log(f"    ➕ Micro Warp")

    # Border Injection
    if preset.get("border_injection", True):
        simple_filters.append(
            build_border_injection(crop_w, crop_h)
        )
        ui_log(f"    ➕ Border Injection")

    # Logo Blur
    blur_pos = preset.get("blur_logo_pos", "None")
    if blur_pos and blur_pos not in ("None", "", None):
        logo_blur_filter = build_blur_logo_filter(
            blur_pos, crop_w, crop_h, ui_log
        )
        if logo_blur_filter:
            has_logo_blur = True
            ui_log(f"    ➕ Logo Blur: {blur_pos}")

    # Build final video filter string
    if has_logo_blur:
        pre_filters = ",".join(simple_filters)
        if pre_filters:
            video_filter_complex = (
                f"{pre_filters},{logo_blur_filter}"
            )
        else:
            video_filter_complex = logo_blur_filter
        use_filter_complex = True
    else:
        video_filter_str   = ",".join(simple_filters)
        use_filter_complex = False

    # Audio Filter Chain
    audio_filter = build_audio_filters(
        volume        = float(preset.get("volume", 1.0)),
        speed         = speed,
        pitch_shift   = float(
            preset.get("audio_pitch", 0.5)
        ),
        phase_shift   = preset.get(
            "audio_phase_shift", True
        ),
        dynamic_range = preset.get(
            "dynamic_range_shift", True
        ),
        silence_pad   = preset.get(
            "silence_padding", False
        ),
        harmonic      = preset.get("harmonic_micro", True),
        bass_boost    = preset.get("bass_boost", False),
        fade          = preset.get("fade_in_out", False),
        remove_audio  = preset.get("remove_audio", False),
        duration      = src_dur,
    )
    ui_log(f"    ➕ Audio Chain built")

    # Metadata flags (from persona!)
    meta_flags = []
    if preset.get("metadata_spoof", True):
        for k, v in metadata.items():
            meta_flags += ["-metadata", f"{k}={v}"]
        ui_log(
            f"    ➕ Persona Metadata: {len(metadata)} fields"
        )

    # ════════════════════════════════════════════════════════
    # TEMP FILES
    # ════════════════════════════════════════════════════════
    tmp_dir     = tempfile.gettempdir()
    rand_tag    = generate_random_string(8)
    safe_input  = os.path.join(
        tmp_dir, f"fba_in_{rand_tag}.mp4"
    )
    safe_output = os.path.join(
        tmp_dir, f"fba_out_{rand_tag}.mp4"
    )

    try:
        shutil.copy2(input_path, safe_input)
        ui_log(f"[+] Temp input ready")
    except Exception as e:
        ui_log(f"[-] Temp copy failed: {e}")
        return False

    # ════════════════════════════════════════════════════════
    # BUILD FFMPEG COMMAND
    # ════════════════════════════════════════════════════════
    cmd = [
        "ffmpeg", "-y", "-hide_banner",
        "-loglevel", "warning", "-nostdin"
    ]

    if trim_start > 0:
        cmd += ["-ss", str(trim_start)]

    cmd += ["-i", safe_input]

    if trim_end > 0 and src_dur > 0:
        effective_dur = src_dur - trim_start - trim_end
        if effective_dur > 1:
            cmd += ["-t", str(effective_dur)]

    if use_filter_complex:
        cmd += ["-filter_complex", video_filter_complex]
    elif video_filter_str:
        cmd += ["-vf", video_filter_str]

    if audio_filter and audio_filter != "anull":
        cmd += ["-af", audio_filter]

    cmd += meta_flags

    cmd += [
        "-c:v"     , "libx264",
        "-crf"     , str(enc["crf"]),
        "-preset"  , enc["preset"],
        "-g"       , str(enc["gop"]),
        "-bf"      , str(enc["bf"]),
        "-refs"    , str(enc["refs"]),
        "-subq"    , str(enc["subq"]),
        "-c:a"     , "aac",
        "-b:a"     , "192k",
        "-movflags", "+faststart",
        "-threads" , "0",
        safe_output
    ]

    # ════════════════════════════════════════════════════════
    # RUN FFMPEG
    # ════════════════════════════════════════════════════════
    ui_log(f"\n[*] 🚀 Running FFmpeg pipeline...")
    start_time = datetime.now()

    try:
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        ui_log(f"    ⏳ Processing... (PID: {process.pid})")

        stderr_lines  = []
        frame_pattern = re.compile(
            r"frame=\s*(\d+).*fps=\s*([\d.]+)"
            r".*time=([\d:.]+)"
        )

        for line in process.stderr:
            line = line.strip()
            if not line:
                continue
            stderr_lines.append(line)
            match = frame_pattern.search(line)
            if match:
                ui_log(
                    f"    ⚙️  frame={match.group(1)} "
                    f"fps={match.group(2)} "
                    f"time={match.group(3)}"
                )
            elif any(kw in line.lower() for kw in [
                "error", "invalid", "failed", "cannot"
            ]):
                ui_log(f"    ⚠️  {line[:120]}")

        process.wait()
        elapsed = (
            datetime.now() - start_time
        ).total_seconds()
        ui_log(f"\n    ⏱️  FFmpeg took: {elapsed:.1f}s")
        ui_log(f"    📊 Exit code : {process.returncode}")

        if (process.returncode == 0
                and os.path.exists(safe_output)):
            out_size = (
                os.path.getsize(safe_output) / (1024*1024)
            )
            if out_size < 0.1:
                ui_log(
                    f"[-] Output too small "
                    f"({out_size:.3f}MB)"
                )
                return False

            ui_log(
                f"    ✅ FFmpeg SUCCESS: {out_size:.2f}MB"
            )

            try:
                if os.path.exists(output_path):
                    os.remove(output_path)
                shutil.move(safe_output, output_path)
            except Exception as e:
                ui_log(f"[-] Move failed: {e}")
                try:
                    shutil.copy2(safe_output, output_path)
                except Exception as e2:
                    ui_log(
                        f"[-] Copy fallback failed: {e2}"
                    )
                    return False

            if not os.path.exists(output_path):
                ui_log("[-] Output missing after move!")
                return False

            # Deep Metadata Poisoning (persona-based)
            ui_log(
                f"\n[*] 🔐 Applying Deep Persona Metadata..."
            )
            if preset.get("metadata_spoof", True):
                if MUTAGEN_AVAILABLE:
                    apply_mutagen_metadata(
                        output_path, metadata,
                        persona, ui_log
                    )
                else:
                    ui_log("[!] pip install mutagen")

            final_size = (
                os.path.getsize(output_path) / (1024*1024)
            )
            ui_log(f"\n{'='*55}")
            ui_log(f"[+] ✅ PROCESSING COMPLETE!")
            ui_log(
                f"[+] 📁 {os.path.basename(output_path)}"
            )
            ui_log(f"[+] 💾 Size    : {final_size:.2f} MB")
            ui_log(
                f"[+] 📱 Device  : "
                f"{persona['make']} "
                f"{persona.get('device_name', persona['model'])}"
            )
            ui_log(
                f"[+] 📍 Location: "
                f"{persona.get('city', '?')}, "
                f"{persona.get('state', '')}, USA"
            )
            ui_log(f"{'='*55}")
            return True

        else:
            ui_log(
                f"\n[-] ❌ FFmpeg FAILED "
                f"(exit={process.returncode})"
            )
            if stderr_lines:
                for ln in stderr_lines[-8:]:
                    ui_log(f"    {ln[:130]}")
            return False

    except FileNotFoundError:
        ui_log("[-] FFmpeg not found!")
        return False
    except Exception as e:
        import traceback
        ui_log(
            f"\n[-] ❌ Exception: {type(e).__name__}: {e}"
        )
        ui_log(traceback.format_exc())
        return False

    finally:
        for f in [safe_input, safe_output]:
            if os.path.exists(f):
                try:
                    os.remove(f)
                except Exception:
                    pass


# ═════════════════════════════════════════════════════════════
# PRESETS
# ═════════════════════════════════════════════════════════════

def get_stealthmax_preset() -> dict:
    return {
        "name"                : "StealthMax v2.0",
        "metadata_spoof"      : True,
        "micro_rotation"      : True,
        "dct_hash_break"      : True,
        "rgb_micro_shift"     : True,
        "audio_phase_shift"   : True,
        "dynamic_range_shift" : True,
        "harmonic_micro"      : True,
        "film_grain"          : True,
        "grain_intensity"     : 3,
        "border_injection"    : True,
        "micro_warp"          : True,
        "auto_trim_edges"     : True,
        "silence_padding"     : False,
        "speed"               : 1.03,
        "crop_percent"        : 96,
        "crop_position"       : "Center",
        "mirror_flip"         : False,
        "color_grade"         : "None",
        "brightness"          : 0.01,
        "contrast"            : 1.01,
        "saturation"          : 1.01,
        "vignette"            : False,
        "sharpen"             : False,
        "sharpen_amount"      : 0.5,
        "zoom_effect"         : False,
        "volume"              : 1.0,
        "audio_pitch"         : 0.5,
        "bass_boost"          : False,
        "fade_in_out"         : False,
        "remove_audio"        : False,
        "trim_start"          : "00:00:00",
        "trim_end"            : "00:00:00",
        "blur_logo_pos"       : "None",
        "crf_override"        : None,
        "text_overlay"        : False,
        "overlay_text"        : "",
        "overlay_position"    : "Bottom",
        "overlay_color"       : "White",
    }


def get_balanced_preset() -> dict:
    p = get_stealthmax_preset()
    p.update({
        "name"           : "Balanced",
        "micro_warp"     : False,
        "silence_padding": False,
        "grain_intensity": 2,
        "color_grade"    : "Warm",
        "sharpen"        : True,
        "sharpen_amount" : 0.3,
        "fade_in_out"    : True,
        "crf_override"   : 20,
    })
    return p


def get_visual_preset() -> dict:
    p = get_stealthmax_preset()
    p.update({
        "name"                : "Visual Quality",
        "micro_rotation"      : False,
        "micro_warp"          : False,
        "dct_hash_break"      : False,
        "film_grain"          : False,
        "border_injection"    : False,
        "silence_padding"     : False,
        "dynamic_range_shift" : False,
        "harmonic_micro"      : False,
        "color_grade"         : "Cinematic",
        "vignette"            : True,
        "sharpen"             : True,
        "sharpen_amount"      : 0.7,
        "fade_in_out"         : True,
        "crf_override"        : 18,
        "grain_intensity"     : 1,
    })
    return p


BUILTIN_PRESETS = {
    "StealthMax v2.0": get_stealthmax_preset,
    "Balanced"       : get_balanced_preset,
    "Visual Quality" : get_visual_preset,
}


def make_video_unique_legacy(
    input_path   : str,
    output_path  : str,
    ui_log        = print,
    mirror       : bool = False,
    blur_logo_pos: str  = None,
) -> bool:
    """Legacy wrapper for backward compatibility."""
    preset = get_stealthmax_preset()
    preset["mirror_flip"]   = mirror
    preset["blur_logo_pos"] = blur_logo_pos or "None"
    return make_video_unique(
        input_path, output_path, ui_log, preset
    )


if __name__ == "__main__":
    print("=" * 55)
    print("Video Editor V3.0 - Persona System")
    print("=" * 55)
    print(f"FFmpeg     : {check_ffmpeg()}")
    print(f"Mutagen    : {MUTAGEN_AVAILABLE}")
    print(f"Devices    : {len(DEVICE_DATABASE)}")
    print(f"USA Cities : {len(USA_CITIES)}")

    # Test persona generation
    print("\n" + "=" * 55)
    print("Sample Persona Generated:")
    print("=" * 55)
    test_persona = generate_workspace_persona()
    print(get_persona_display_summary(test_persona))