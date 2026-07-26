"""
Universal Thumbnail Generator V3.0
30+ Professional Templates + Smart Frame Detection
"""
import os
import cv2
import subprocess
import random
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance


# ═══════════════════════════════════════════════════════════════
# 33 PROFESSIONAL TEMPLATES
# ═══════════════════════════════════════════════════════════════
TEMPLATE_CATALOG = {
    # VIRAL & REACTION
    "mrbeast_extreme": {
        "name": "🔥 MrBeast Extreme",
        "category": "Viral",
        "bg_style": "zoom_face",
        "text_color": "#FFD700",  # Gold
        "stroke_color": "#000000",
        "stroke_width": 8,
        "font_size_ratio": 0.15,
        "font_weight": "black",
        "text_position": "center",
        "emoji_style": "shock",
        "border": {"color": "#FF0000", "width": 15},
        "effects": ["face_zoom", "vignette", "high_contrast"],
        "text_examples": ["$10,000!", "SHOCKING!", "GONE WRONG!"],
    },
    "shock_awe": {
        "name": "😱 Shock & Awe",
        "category": "Viral",
        "bg_style": "brightness_boost",
        "text_color": "#FFFFFF",
        "stroke_color": "#FF0000",
        "stroke_width": 6,
        "font_size_ratio": 0.13,
        "font_weight": "bold",
        "text_position": "top",
        "emoji_style": "shock",
        "overlay": "red_circle_arrow",
        "effects": ["high_saturation"],
        "text_examples": ["YOU WON'T BELIEVE!", "SHOCKING TRUTH!"],
    },
    "money_reward": {
        "name": "💰 Money/Reward",
        "category": "Viral",
        "bg_style": "gold_tint",
        "text_color": "#00FF00",
        "stroke_color": "#000000",
        "stroke_width": 5,
        "font_size_ratio": 0.14,
        "font_weight": "bold",
        "text_position": "top",
        "emoji_style": "money",
        "overlay": "dollar_signs",
        "effects": ["gold_particles"],
        "text_examples": ["$1000 GIVEAWAY!", "FREE MONEY!"],
    },
    "challenge_mode": {
        "name": "🎯 Challenge Mode",
        "category": "Viral",
        "bg_style": "action",
        "text_color": "#FFFF00",
        "stroke_color": "#FF0000",
        "stroke_width": 6,
        "font_size_ratio": 0.13,
        "font_weight": "black",
        "text_position": "top",
        "emoji_style": "target",
        "overlay": "timer_countdown",
        "effects": ["motion_lines"],
        "text_examples": ["24 HOUR CHALLENGE!", "LAST TO LEAVE WINS!"],
    },
    "alert_warning": {
        "name": "🚨 Alert/Warning",
        "category": "Viral",
        "bg_style": "red_tint",
        "text_color": "#FFFFFF",
        "stroke_color": "#000000",
        "stroke_width": 5,
        "font_size_ratio": 0.12,
        "font_weight": "black",
        "text_position": "center",
        "emoji_style": "warning",
        "overlay": "warning_banner",
        "effects": ["red_glow"],
        "text_examples": ["WARNING!", "DO NOT TRY!"],
    },
    
    # TIKTOK & REELS
    "tiktok_gradient": {
        "name": "✨ TikTok Gradient",
        "category": "TikTok",
        "bg_style": "gradient_pink_purple",
        "text_color": "#FFFFFF",
        "stroke_color": "#000000",
        "stroke_width": 3,
        "font_size_ratio": 0.10,
        "font_weight": "bold",
        "text_position": "top",
        "emoji_style": "sparkle",
        "effects": ["gradient_overlay", "soft_glow"],
        "text_examples": ["POV: You Just Found This ✨", "Life Hack 💫"],
    },
    "aesthetic_vibes": {
        "name": "💫 Aesthetic Vibes",
        "category": "TikTok",
        "bg_style": "soft_blur",
        "text_color": "#FFFFFF",
        "stroke_color": "#000000",
        "stroke_width": 2,
        "font_size_ratio": 0.09,
        "font_weight": "light",
        "text_position": "bottom",
        "emoji_style": "aesthetic",
        "effects": ["soft_blur", "muted_colors"],
        "text_examples": ["that girl energy ✨", "main character moment"],
    },
    "y2k_neon": {
        "name": "🌈 Y2K Neon",
        "category": "TikTok",
        "bg_style": "neon_glow",
        "text_color": "#FF00FF",
        "stroke_color": "#00FFFF",
        "stroke_width": 4,
        "font_size_ratio": 0.12,
        "font_weight": "bold",
        "text_position": "center",
        "emoji_style": "neon",
        "effects": ["neon_glow", "chromatic_aberration"],
        "text_examples": ["Y2K VIBES 🌈", "RETRO CORE"],
    },
    "pov_style": {
        "name": "📱 POV Style",
        "category": "TikTok",
        "bg_style": "clean",
        "text_color": "#FFFFFF",
        "stroke_color": "#000000",
        "stroke_width": 3,
        "font_size_ratio": 0.09,
        "font_weight": "medium",
        "text_position": "top",
        "emoji_style": "modern",
        "prefix": "POV: ",
        "effects": ["clean"],
        "text_examples": ["POV: You Wake Up Rich", "POV: It's Monday"],
    },
    "viral_trends": {
        "name": "🔥 Viral Trends",
        "category": "TikTok",
        "bg_style": "bright_pop",
        "text_color": "#FFFF00",
        "stroke_color": "#FF00FF",
        "stroke_width": 4,
        "font_size_ratio": 0.11,
        "font_weight": "bold",
        "text_position": "center",
        "emoji_style": "fire",
        "effects": ["saturation_boost"],
        "text_examples": ["TRENDING NOW 🔥", "GOING VIRAL 💯"],
    },
    
    # NEWS & INFORMATION
    "breaking_news": {
        "name": "📰 Breaking News",
        "category": "News",
        "bg_style": "news_style",
        "text_color": "#FFFFFF",
        "stroke_color": "#000000",
        "stroke_width": 3,
        "font_size_ratio": 0.10,
        "font_weight": "bold",
        "text_position": "bottom",
        "emoji_style": "news",
        "overlay": "red_banner_top",
        "effects": ["news_ticker"],
        "text_examples": ["BREAKING: MAJOR UPDATE", "URGENT NEWS"],
    },
    "live_urgent": {
        "name": "🔴 Live/Urgent",
        "category": "News",
        "bg_style": "red_urgent",
        "text_color": "#FFFFFF",
        "stroke_color": "#000000",
        "stroke_width": 3,
        "font_size_ratio": 0.11,
        "font_weight": "bold",
        "text_position": "top",
        "emoji_style": "live",
        "overlay": "live_indicator",
        "effects": ["red_border"],
        "text_examples": ["🔴 LIVE NOW", "URGENT UPDATE"],
    },
    "data_stats": {
        "name": "📊 Data/Stats",
        "category": "News",
        "bg_style": "clean_data",
        "text_color": "#00FF00",
        "stroke_color": "#000000",
        "stroke_width": 3,
        "font_size_ratio": 0.13,
        "font_weight": "bold",
        "text_position": "center",
        "emoji_style": "data",
        "overlay": "chart_overlay",
        "effects": ["clean"],
        "text_examples": ["95% INCREASE!", "TOP 10 STATS"],
    },
    "interview_style": {
        "name": "🎤 Interview Style",
        "category": "News",
        "bg_style": "portrait",
        "text_color": "#FFFFFF",
        "stroke_color": "#000000",
        "stroke_width": 3,
        "font_size_ratio": 0.09,
        "font_weight": "medium",
        "text_position": "bottom",
        "emoji_style": "quote",
        "overlay": "quote_marks",
        "effects": ["subtle_vignette"],
        "text_examples": ['"THIS CHANGED MY LIFE"', '"THE TRUTH REVEALED"'],
    },
    
    # COMEDY & MEMES
    "meme_format": {
        "name": "😂 Meme Format",
        "category": "Comedy",
        "bg_style": "meme_classic",
        "text_color": "#FFFFFF",
        "stroke_color": "#000000",
        "stroke_width": 5,
        "font_size_ratio": 0.11,
        "font_weight": "impact",
        "text_position": "top_bottom",
        "emoji_style": "laugh",
        "effects": ["impact_style"],
        "text_examples": ["ME WHEN...", "WHEN YOU REALIZE..."],
    },
    "funny_reaction": {
        "name": "🤣 Funny Reaction",
        "category": "Comedy",
        "bg_style": "bright_fun",
        "text_color": "#FFFF00",
        "stroke_color": "#FF0000",
        "stroke_width": 5,
        "font_size_ratio": 0.13,
        "font_weight": "bold",
        "text_position": "center",
        "emoji_style": "laugh",
        "overlay": "laugh_emojis",
        "effects": ["saturation_boost"],
        "text_examples": ["I CAN'T STOP LAUGHING! 🤣", "SO FUNNY!"],
    },
    "comedy_show": {
        "name": "🎪 Comedy Show",
        "category": "Comedy",
        "bg_style": "colorful",
        "text_color": "#FF00FF",
        "stroke_color": "#FFFF00",
        "stroke_width": 5,
        "font_size_ratio": 0.12,
        "font_weight": "playful",
        "text_position": "center",
        "emoji_style": "playful",
        "effects": ["confetti"],
        "text_examples": ["COMEDY GOLD! 🎭", "TRY NOT TO LAUGH!"],
    },
    "prank_style": {
        "name": "😜 Prank Style",
        "category": "Comedy",
        "bg_style": "warning_yellow",
        "text_color": "#000000",
        "stroke_color": "#FFFF00",
        "stroke_width": 5,
        "font_size_ratio": 0.12,
        "font_weight": "bold",
        "text_position": "top",
        "emoji_style": "prank",
        "overlay": "prank_tape",
        "effects": ["warning_stripes"],
        "text_examples": ["EPIC PRANK! 😜", "THEY DIDN'T EXPECT THIS!"],
    },
    
    # FOOD & LIFESTYLE
    "recipe_card": {
        "name": "🍔 Recipe Card",
        "category": "Food",
        "bg_style": "warm_food",
        "text_color": "#FFFFFF",
        "stroke_color": "#8B4513",
        "stroke_width": 4,
        "font_size_ratio": 0.10,
        "font_weight": "elegant",
        "text_position": "bottom",
        "emoji_style": "food",
        "overlay": "recipe_frame",
        "effects": ["warm_tint", "food_saturation"],
        "text_examples": ["5-MIN RECIPE 🍝", "PERFECT DINNER 🍽️"],
    },
    "sweet_warm": {
        "name": "🍰 Sweet & Warm",
        "category": "Food",
        "bg_style": "pastel",
        "text_color": "#FFFFFF",
        "stroke_color": "#FF69B4",
        "stroke_width": 3,
        "font_size_ratio": 0.09,
        "font_weight": "cursive",
        "text_position": "center",
        "emoji_style": "sweet",
        "effects": ["pastel_filter"],
        "text_examples": ["Sweet Delights 🧁", "Home Baked ❤️"],
    },
    "asian_food": {
        "name": "🍜 Asian Food",
        "category": "Food",
        "bg_style": "asian_style",
        "text_color": "#FFD700",
        "stroke_color": "#FF0000",
        "stroke_width": 5,
        "font_size_ratio": 0.12,
        "font_weight": "bold",
        "text_position": "top",
        "emoji_style": "asian",
        "effects": ["red_gold_tint"],
        "text_examples": ["AUTHENTIC RECIPE 🍜", "SPICY & DELICIOUS! 🌶️"],
    },
    "healthy_fit": {
        "name": "🥗 Healthy Food",
        "category": "Food",
        "bg_style": "fresh_green",
        "text_color": "#FFFFFF",
        "stroke_color": "#228B22",
        "stroke_width": 3,
        "font_size_ratio": 0.10,
        "font_weight": "medium",
        "text_position": "bottom",
        "emoji_style": "healthy",
        "effects": ["fresh_green_tint"],
        "text_examples": ["HEALTHY & DELICIOUS 🥗", "FIT MEAL PREP 💪"],
    },
    
    # FITNESS & SPORTS
    "beast_mode": {
        "name": "💪 Beast Mode",
        "category": "Fitness",
        "bg_style": "dark_powerful",
        "text_color": "#FF0000",
        "stroke_color": "#000000",
        "stroke_width": 6,
        "font_size_ratio": 0.14,
        "font_weight": "black",
        "text_position": "center",
        "emoji_style": "power",
        "effects": ["dark_dramatic", "high_contrast"],
        "text_examples": ["BEAST MODE 💪", "NO EXCUSES! 🔥"],
    },
    "champion_style": {
        "name": "🏆 Champion",
        "category": "Fitness",
        "bg_style": "gold_champion",
        "text_color": "#FFD700",
        "stroke_color": "#000000",
        "stroke_width": 5,
        "font_size_ratio": 0.13,
        "font_weight": "bold",
        "text_position": "center",
        "emoji_style": "trophy",
        "effects": ["gold_shine"],
        "text_examples": ["CHAMPION MINDSET 🏆", "WINNERS ONLY!"],
    },
    "motivation": {
        "name": "🏃 Motivation",
        "category": "Fitness",
        "bg_style": "sky_blue",
        "text_color": "#FFFFFF",
        "stroke_color": "#0066CC",
        "stroke_width": 4,
        "font_size_ratio": 0.11,
        "font_weight": "bold",
        "text_position": "center",
        "emoji_style": "motivation",
        "effects": ["inspiring"],
        "text_examples": ["YOU CAN DO IT! 💪", "NEVER GIVE UP! 🏃"],
    },
    
    # EDUCATIONAL
    "tutorial_howto": {
        "name": "🎓 Tutorial/How-To",
        "category": "Education",
        "bg_style": "clean_bright",
        "text_color": "#FFFFFF",
        "stroke_color": "#0000FF",
        "stroke_width": 4,
        "font_size_ratio": 0.10,
        "font_weight": "bold",
        "text_position": "top",
        "emoji_style": "tutorial",
        "overlay": "numbered_steps",
        "effects": ["clean_bright"],
        "text_examples": ["HOW TO... IN 3 STEPS", "STEP BY STEP GUIDE 📚"],
    },
    "tips_tricks": {
        "name": "💡 Tips & Tricks",
        "category": "Education",
        "bg_style": "bright_ideas",
        "text_color": "#FFFF00",
        "stroke_color": "#000000",
        "stroke_width": 4,
        "font_size_ratio": 0.11,
        "font_weight": "bold",
        "text_position": "center",
        "emoji_style": "lightbulb",
        "effects": ["light_burst"],
        "text_examples": ["5 SECRET TIPS 💡", "MIND-BLOWING HACKS!"],
    },
    "deep_dive": {
        "name": "📚 Deep Dive",
        "category": "Education",
        "bg_style": "book_paper",
        "text_color": "#000000",
        "stroke_color": "#FFFFFF",
        "stroke_width": 3,
        "font_size_ratio": 0.09,
        "font_weight": "serif",
        "text_position": "center",
        "emoji_style": "book",
        "effects": ["paper_texture"],
        "text_examples": ["COMPLETE GUIDE", "THE FULL STORY"],
    },
    
    # CINEMATIC
    "movie_style": {
        "name": "🎬 Movie Style",
        "category": "Cinematic",
        "bg_style": "cinematic_dark",
        "text_color": "#FFFFFF",
        "stroke_color": "#000000",
        "stroke_width": 3,
        "font_size_ratio": 0.10,
        "font_weight": "serif",
        "text_position": "bottom",
        "emoji_style": "cinema",
        "effects": ["film_grain", "letterbox", "dark_cinematic"],
        "text_examples": ["THE UNTOLD STORY", "COMING SOON..."],
    },
    "mystery_thriller": {
        "name": "🌙 Mystery/Thriller",
        "category": "Cinematic",
        "bg_style": "dark_mystery",
        "text_color": "#FF0000",
        "stroke_color": "#000000",
        "stroke_width": 4,
        "font_size_ratio": 0.11,
        "font_weight": "bold",
        "text_position": "center",
        "emoji_style": "mystery",
        "effects": ["dark_shadow", "red_accent"],
        "text_examples": ["WHAT HAPPENED?", "THE DARK TRUTH..."],
    },
    
    # BUSINESS & TECH
    "corporate_business": {
        "name": "💼 Corporate",
        "category": "Business",
        "bg_style": "corporate_blue",
        "text_color": "#FFFFFF",
        "stroke_color": "#003366",
        "stroke_width": 3,
        "font_size_ratio": 0.09,
        "font_weight": "medium",
        "text_position": "bottom",
        "emoji_style": "business",
        "effects": ["professional_clean"],
        "text_examples": ["BUSINESS STRATEGY", "GROWTH HACKS 📈"],
    },
    "tech_gaming": {
        "name": "💻 Tech/Gaming",
        "category": "Business",
        "bg_style": "cyber_neon",
        "text_color": "#00FF00",
        "stroke_color": "#FF00FF",
        "stroke_width": 4,
        "font_size_ratio": 0.11,
        "font_weight": "tech",
        "text_position": "center",
        "emoji_style": "gaming",
        "effects": ["cyber_glow", "matrix"],
        "text_examples": ["LEVEL UP! 🎮", "GAMING SETUP 💻"],
    },
    
    # KIDS & FAMILY
    "kids_family": {
        "name": "👶 Kids/Family",
        "category": "Kids",
        "bg_style": "rainbow_bright",
        "text_color": "#FFFFFF",
        "stroke_color": "#FF00FF",
        "stroke_width": 5,
        "font_size_ratio": 0.13,
        "font_weight": "playful",
        "text_position": "center",
        "emoji_style": "kids",
        "effects": ["rainbow_border", "playful"],
        "text_examples": ["FUN FOR KIDS! 🌈", "FAMILY TIME! ❤️"],
    },
}


# ═══════════════════════════════════════════════════════════════
# EMOJI PACKS BY STYLE
# ═══════════════════════════════════════════════════════════════
EMOJI_PACKS = {
    "shock": ["😱", "🤯", "😳", "😲", "🙀"],
    "money": ["💰", "💵", "💸", "🤑", "💎"],
    "target": ["🎯", "🏆", "⏰", "🔥", "💯"],
    "warning": ["🚨", "⚠️", "❗", "🔴", "⛔"],
    "sparkle": ["✨", "💫", "⭐", "🌟", "💖"],
    "aesthetic": ["✨", "🌸", "☁️", "🌙", "💭"],
    "neon": ["🌈", "💜", "💙", "💚", "🩷"],
    "modern": ["📱", "💫", "🎯", "✅", "🔥"],
    "fire": ["🔥", "💯", "⚡", "🚀", "💥"],
    "news": ["📰", "🎤", "📢", "🔔", "📣"],
    "live": ["🔴", "📺", "🎙️", "⚡", "🚨"],
    "data": ["📊", "📈", "💹", "🔢", "💡"],
    "quote": ["💬", "🗣️", "❝", "❞", "📝"],
    "laugh": ["😂", "🤣", "😆", "😹", "🤪"],
    "playful": ["🎪", "🎭", "🤡", "🎨", "🎬"],
    "prank": ["😜", "🤪", "😎", "🃏", "🎉"],
    "food": ["🍔", "🍕", "🍝", "🍰", "🥘"],
    "sweet": ["🧁", "🍰", "🍪", "🍩", "🍫"],
    "asian": ["🍜", "🍱", "🍣", "🥢", "🌶️"],
    "healthy": ["🥗", "🥑", "🍎", "💚", "🌱"],
    "power": ["💪", "🔥", "⚡", "🦾", "💥"],
    "trophy": ["🏆", "🥇", "👑", "🌟", "💎"],
    "motivation": ["💪", "🚀", "🎯", "⭐", "🔥"],
    "tutorial": ["🎓", "📚", "✏️", "📝", "💡"],
    "lightbulb": ["💡", "✨", "🔑", "⚡", "🎯"],
    "book": ["📚", "📖", "✍️", "🎓", "📝"],
    "cinema": ["🎬", "🎥", "🎞️", "🎦", "📽️"],
    "mystery": ["🌙", "🔍", "🕵️", "🗝️", "❓"],
    "business": ["💼", "📈", "💰", "🎯", "📊"],
    "gaming": ["🎮", "🕹️", "👾", "⚔️", "🏆"],
    "kids": ["🌈", "🎈", "🎨", "🧸", "⭐"],
}


# ═══════════════════════════════════════════════════════════════
# THUMBNAIL GENERATOR
# ═══════════════════════════════════════════════════════════════
class ThumbnailGenerator:
    """
    Universal Thumbnail Generator V3.0
    Features:
    - 33 professional templates
    - Smart frame detection with AI scoring
    - Face detection
    - Automatic best-frame selection
    - Multiple variations per video
    - Workspace-specific styles
    """
    
    def __init__(self, output_dir="downloads"):
        self.output_dir = output_dir
        self.templates = TEMPLATE_CATALOG
        
        # Try loading face cascade for face detection
        try:
            self.face_cascade = cv2.CascadeClassifier(
                cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
            )
            self.face_detection_available = True
        except Exception:
            self.face_detection_available = False

    # ═══════════════════════════════════════════════════════════
    # PUBLIC API
    # ═══════════════════════════════════════════════════════════
    def get_all_templates(self):
        """Get list of all template IDs and names."""
        return {tid: t["name"] for tid, t in self.templates.items()}
    
    def get_templates_by_category(self):
        """Group templates by category."""
        categories = {}
        for tid, template in self.templates.items():
            cat = template.get("category", "Other")
            if cat not in categories:
                categories[cat] = []
            categories[cat].append({
                "id": tid,
                "name": template["name"]
            })
        return categories

    def generate_thumbnail(
        self,
        video_path,
        text="Wait for it 😱",
        time_mark=None,
        ui_log=print,
        template_id="mrbeast_extreme",
        num_variations=3,
        auto_text=True,
    ):
        """
        Generate professional thumbnail(s) from video.
        
        Args:
            video_path: Path to source video
            text: Custom text (or None for auto-generated)
            time_mark: Specific timestamp (or None for smart detection)
            ui_log: Logging function
            template_id: Template to use (from TEMPLATE_CATALOG)
            num_variations: Number of variations to generate (1-5)
            auto_text: Auto-generate viral text
        
        Returns:
            Best thumbnail path (or None on failure)
        """
        if not os.path.exists(video_path):
            ui_log(f"[-] Video not found: {video_path}")
            return None

        # Validate template
        if template_id not in self.templates:
            ui_log(f"[!] Unknown template: {template_id}, using default")
            template_id = "mrbeast_extreme"
        
        template = self.templates[template_id]
        
        ui_log(f"\n{'='*55}")
        ui_log(f"[*] 🎨 THUMBNAIL GENERATOR V3.0")
        ui_log(f"[*] Template: {template['name']}")
        ui_log(f"[*] Variations: {num_variations}")
        ui_log(f"{'='*55}")

        # Get video info
        base_dir = os.path.dirname(video_path) or "."
        filename = os.path.basename(video_path).split('.')[0]

        # Extract candidate frames
        ui_log(f"[*] 🎬 Analyzing video for best frames...")
        candidate_frames = self._extract_smart_frames(
            video_path, base_dir, filename, ui_log,
            num_frames=15 if not time_mark else 1,
            specific_time=time_mark
        )
        
        if not candidate_frames:
            ui_log("[-] No frames extracted!")
            return None
        
        # Score and rank frames
        ui_log(f"[*] 📊 Scoring {len(candidate_frames)} frames...")
        scored_frames = self._score_frames(candidate_frames, ui_log)
        
        # Get top frames
        top_frames = scored_frames[:num_variations]
        ui_log(f"[+] ✅ Top {len(top_frames)} frames selected")
        
        # Generate variations
        variations = []
        for i, (frame_path, score) in enumerate(top_frames):
            ui_log(f"\n[*] 🎨 Generating variation {i+1}/{len(top_frames)}...")
            
            # Get text (auto or custom)
            if auto_text and (text == "Wait for it 😱" or not text):
                text_to_use = self._generate_viral_text(template)
            else:
                text_to_use = text
            
            # Generate thumbnail
            thumb_path = os.path.join(
                base_dir,
                f"{filename}_thumb_{i+1}.jpg"
            )
            
            result = self._create_thumbnail(
                frame_path, thumb_path, text_to_use,
                template, ui_log
            )
            
            if result:
                variations.append({
                    "path": result,
                    "score": score,
                    "text": text_to_use,
                })
                ui_log(f"[+] Variation {i+1}: {os.path.basename(result)}")
        
        # Cleanup candidate frames
        for fp, _ in candidate_frames:
            try:
                if os.path.exists(fp):
                    os.remove(fp)
            except Exception:
                pass
        
        if not variations:
            ui_log("[-] All variations failed!")
            return None
        
        # Return best variation
        best = variations[0]
        ui_log(f"\n{'='*55}")
        ui_log(f"[+] ✅ THUMBNAIL COMPLETE!")
        ui_log(f"[+] 🏆 Best: {os.path.basename(best['path'])}")
        ui_log(f"[+] 📊 Score: {best['score']:.1f}/100")
        ui_log(f"[+] 📝 Text: {best['text']}")
        ui_log(f"[+] 🎨 Variations: {len(variations)}")
        ui_log(f"{'='*55}")
        
        return best["path"]

    # ═══════════════════════════════════════════════════════════
    # SMART FRAME EXTRACTION
    # ═══════════════════════════════════════════════════════════
    def _extract_smart_frames(
        self, video_path, base_dir, filename, ui_log,
        num_frames=15, specific_time=None
    ):
        """Extract multiple candidate frames using OpenCV."""
        candidates = []
        
        try:
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                ui_log("[-] Failed to open video")
                return []
            
            fps = cap.get(cv2.CAP_PROP_FPS) or 30
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            duration = total_frames / fps
            
            ui_log(f"    Video: {duration:.1f}s @ {fps:.0f}fps")
            
            # Determine frame timestamps
            if specific_time:
                # Convert timestamp to seconds
                parts = specific_time.split(":")
                if len(parts) == 3:
                    secs = (int(parts[0]) * 3600 +
                            int(parts[1]) * 60 +
                            int(parts[2]))
                else:
                    secs = float(specific_time)
                timestamps = [secs]
            else:
                # Smart selection: skip first 10% and last 10%
                start = duration * 0.1
                end = duration * 0.9
                if end - start < 1:
                    start, end = 0, duration
                
                # Distribute frames evenly
                timestamps = [
                    start + (end - start) * i / (num_frames - 1)
                    for i in range(num_frames)
                ] if num_frames > 1 else [duration / 2]
            
            # Extract frames
            for i, ts in enumerate(timestamps):
                frame_num = int(ts * fps)
                cap.set(cv2.CAP_PROP_POS_FRAMES, frame_num)
                ret, frame = cap.read()
                
                if ret and frame is not None:
                    frame_path = os.path.join(
                        base_dir,
                        f"{filename}_candidate_{i}.jpg"
                    )
                    cv2.imwrite(frame_path, frame,
                                [cv2.IMWRITE_JPEG_QUALITY, 95])
                    candidates.append((frame_path, ts))
            
            cap.release()
            ui_log(f"    ✅ Extracted {len(candidates)} candidate frames")
        
        except Exception as e:
            ui_log(f"    ❌ Frame extraction error: {e}")
            # Fallback to ffmpeg
            return self._extract_frames_ffmpeg(
                video_path, base_dir, filename, ui_log
            )
        
        return candidates

    def _extract_frames_ffmpeg(
        self, video_path, base_dir, filename, ui_log
    ):
        """Fallback: extract single frame using ffmpeg."""
        try:
            frame_path = os.path.join(
                base_dir, f"{filename}_candidate_0.jpg"
            )
            cmd = [
                "ffmpeg", "-y", "-ss", "00:00:03",
                "-i", video_path, "-vframes", "1",
                "-q:v", "2", frame_path
            ]
            subprocess.run(cmd, capture_output=True, timeout=30)
            if os.path.exists(frame_path):
                return [(frame_path, 3.0)]
        except Exception:
            pass
        return []

    # ═══════════════════════════════════════════════════════════
    # FRAME SCORING (AI)
    # ═══════════════════════════════════════════════════════════
    def _score_frames(self, candidates, ui_log):
        """Score frames based on multiple criteria."""
        scored = []
        
        for frame_path, timestamp in candidates:
            score = self._calculate_frame_score(frame_path, ui_log)
            scored.append((frame_path, score))
        
        # Sort by score descending
        scored.sort(key=lambda x: x[1], reverse=True)
        
        # Log top 3
        for i, (fp, s) in enumerate(scored[:3]):
            ui_log(f"    #{i+1}: {os.path.basename(fp)} = {s:.1f}/100")
        
        return scored

    def _calculate_frame_score(self, frame_path, ui_log):
        """Calculate quality score for a frame (0-100)."""
        try:
            # Load with OpenCV
            img = cv2.imread(frame_path)
            if img is None:
                return 0
            
            # 1. Brightness score (avoid too dark/bright)
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            brightness = np.mean(gray)
            if brightness < 30:  # Too dark
                bright_score = 0
            elif brightness > 220:  # Too bright
                bright_score = 30
            elif 80 <= brightness <= 180:  # Ideal
                bright_score = 100
            else:
                bright_score = 60
            
            # 2. Sharpness (Laplacian variance)
            laplacian = cv2.Laplacian(gray, cv2.CV_64F).var()
            if laplacian < 50:  # Very blurry
                sharp_score = 0
            elif laplacian > 500:  # Very sharp
                sharp_score = 100
            else:
                sharp_score = (laplacian / 500) * 100
            
            # 3. Face detection
            face_score = 0
            if self.face_detection_available:
                faces = self.face_cascade.detectMultiScale(
                    gray, scaleFactor=1.1, minNeighbors=5,
                    minSize=(50, 50)
                )
                if len(faces) > 0:
                    # Bonus for faces
                    face_score = 100
                    # Extra bonus for larger faces (closer)
                    largest_face = max(faces, key=lambda f: f[2] * f[3])
                    face_area = largest_face[2] * largest_face[3]
                    img_area = img.shape[0] * img.shape[1]
                    face_ratio = face_area / img_area
                    if face_ratio > 0.05:  # Face is significant
                        face_score = 100
                    else:
                        face_score = 70
            
            # 4. Color variety (unique colors count)
            small = cv2.resize(img, (50, 50))
            unique_colors = len(np.unique(
                small.reshape(-1, 3), axis=0
            ))
            color_score = min(100, (unique_colors / 500) * 100)
            
            # 5. Contrast (standard deviation)
            contrast = np.std(gray)
            if contrast < 20:  # Low contrast
                contrast_score = 30
            elif contrast > 80:  # High contrast
                contrast_score = 100
            else:
                contrast_score = 60 + (contrast - 20) * 0.66
            
            # Weighted total
            total = (
                bright_score   * 0.15 +
                sharp_score    * 0.25 +
                face_score     * 0.30 +
                color_score    * 0.15 +
                contrast_score * 0.15
            )
            
            return round(total, 1)
        
        except Exception as e:
            return 30  # Default average score

    # ═══════════════════════════════════════════════════════════
    # AUTO TEXT GENERATION
    # ═══════════════════════════════════════════════════════════
    def _generate_viral_text(self, template):
        """Generate viral text based on template examples."""
        examples = template.get("text_examples", ["Watch This! 🔥"])
        return random.choice(examples)

    # ═══════════════════════════════════════════════════════════
    # THUMBNAIL CREATION (WITH TEMPLATE)
    # ═══════════════════════════════════════════════════════════
    def _create_thumbnail(
        self, frame_path, output_path, text,
        template, ui_log
    ):
        """Create thumbnail with template applied."""
        try:
            # Load image
            img = Image.open(frame_path).convert("RGB")
            width, height = img.size
            
            # Apply background effects
            img = self._apply_bg_effects(img, template, ui_log)
            
            # Detect face for text placement
            face_bbox = self._detect_face_pil(img)
            
            # Add overlays (borders, banners, etc.)
            img = self._add_overlays(img, template, ui_log)
            
            # Add text
            img = self._add_text(
                img, text, template, face_bbox, ui_log
            )
            
            # Save
            img.save(output_path, quality=95, optimize=True)
            return output_path
        
        except Exception as e:
            ui_log(f"[-] Thumbnail creation error: {e}")
            import traceback
            ui_log(traceback.format_exc())
            return None

    def _apply_bg_effects(self, img, template, ui_log):
        """Apply background effects based on template."""
        effects = template.get("effects", [])
        bg_style = template.get("bg_style", "")
        
        # High contrast
        if "high_contrast" in effects:
            enhancer = ImageEnhance.Contrast(img)
            img = enhancer.enhance(1.3)
        
        # Saturation boost
        if "saturation_boost" in effects or "food_saturation" in effects:
            enhancer = ImageEnhance.Color(img)
            img = enhancer.enhance(1.4)
        
        # Vignette
        if "vignette" in effects:
            img = self._apply_vignette(img)
        
        # Dark cinematic
        if "dark_cinematic" in effects or "dark_dramatic" in effects:
            enhancer = ImageEnhance.Brightness(img)
            img = enhancer.enhance(0.7)
            enhancer = ImageEnhance.Contrast(img)
            img = enhancer.enhance(1.2)
        
        # Soft blur (for aesthetic)
        if "soft_blur" in effects:
            img = img.filter(ImageFilter.GaussianBlur(radius=2))
            enhancer = ImageEnhance.Brightness(img)
            img = enhancer.enhance(1.1)
        
        # Warm tint (food)
        if "warm_tint" in effects:
            r, g, b = img.split()
            r = r.point(lambda i: min(255, i + 20))
            img = Image.merge("RGB", (r, g, b))
        
        # Red tint
        if "red_tint" in effects:
            r, g, b = img.split()
            r = r.point(lambda i: min(255, i + 30))
            g = g.point(lambda i: max(0, i - 20))
            b = b.point(lambda i: max(0, i - 20))
            img = Image.merge("RGB", (r, g, b))
        
        # Fresh green
        if "fresh_green_tint" in effects:
            r, g, b = img.split()
            g = g.point(lambda i: min(255, i + 20))
            img = Image.merge("RGB", (r, g, b))
        
        # Neon glow
        if "neon_glow" in effects:
            enhancer = ImageEnhance.Color(img)
            img = enhancer.enhance(1.5)
            enhancer = ImageEnhance.Contrast(img)
            img = enhancer.enhance(1.2)
        
        return img

    def _apply_vignette(self, img):
        """Add vignette effect (dark corners)."""
        width, height = img.size
        overlay = Image.new("RGBA", (width, height),
                            (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)
        
        # Create radial gradient
        for i in range(min(width, height) // 3):
            alpha = int(150 * (i / (min(width, height) // 3)))
            draw.ellipse(
                [i, i, width - i, height - i],
                outline=(0, 0, 0, alpha)
            )
        
        img = img.convert("RGBA")
        img = Image.alpha_composite(img, overlay)
        return img.convert("RGB")

    def _detect_face_pil(self, img):
        """Detect face position for text placement."""
        if not self.face_detection_available:
            return None
        
        try:
            # Convert PIL to CV2
            cv_img = cv2.cvtColor(
                np.array(img), cv2.COLOR_RGB2BGR
            )
            gray = cv2.cvtColor(cv_img, cv2.COLOR_BGR2GRAY)
            faces = self.face_cascade.detectMultiScale(
                gray, 1.1, 5, minSize=(50, 50)
            )
            
            if len(faces) > 0:
                # Return largest face
                largest = max(faces, key=lambda f: f[2] * f[3])
                x, y, w, h = largest
                return (x, y, x + w, y + h)
        except Exception:
            pass
        
        return None

    def _add_overlays(self, img, template, ui_log):
        """Add overlays like borders, banners, etc."""
        border = template.get("border")
        overlay = template.get("overlay")
        
        # Border
        if border:
            width, height = img.size
            new_img = Image.new(
                "RGB",
                (width + border["width"] * 2,
                 height + border["width"] * 2),
                border["color"]
            )
            new_img.paste(img, (border["width"], border["width"]))
            img = new_img
        
        # Red banner top (for news)
        if overlay == "red_banner_top":
            width, height = img.size
            banner_height = int(height * 0.08)
            draw = ImageDraw.Draw(img)
            draw.rectangle(
                [0, 0, width, banner_height],
                fill="#CC0000"
            )
        
        # Warning stripes
        if overlay == "warning_stripes":
            width, height = img.size
            draw = ImageDraw.Draw(img)
            for i in range(0, width, 40):
                draw.polygon(
                    [(i, 0), (i + 20, 0),
                     (i + 40, 30), (i + 20, 30)],
                    fill="#FFFF00"
                )
        
        return img

    def _add_text(
        self, img, text, template, face_bbox, ui_log
    ):
        """Add text with template styling."""
        width, height = img.size
        draw = ImageDraw.Draw(img)
        
        # Add prefix if defined
        prefix = template.get("prefix", "")
        if prefix and not text.startswith(prefix):
            text = f"{prefix}{text}"
        
        # Font settings
        font_size = int(height * template.get(
            "font_size_ratio", 0.10
        ))
        font_size = max(24, min(120, font_size))
        
        # Load font
        font = self._load_font(
            font_size, template.get("font_weight", "bold")
        )
        
        # Get text dimensions
        try:
            bbox = draw.textbbox((0, 0), text, font=font)
            txt_w = bbox[2] - bbox[0]
            txt_h = bbox[3] - bbox[1]
        except Exception:
            txt_w = len(text) * font_size * 0.6
            txt_h = font_size
        
        # Determine position (avoid face)
        position = template.get("text_position", "center")
        x, y = self._calculate_text_position(
            width, height, txt_w, txt_h,
            position, face_bbox
        )
        
        # Draw text stroke
        stroke_color = template.get("stroke_color", "#000000")
        stroke_width = template.get("stroke_width", 5)
        
        for dx in range(-stroke_width, stroke_width + 1):
            for dy in range(-stroke_width, stroke_width + 1):
                if dx != 0 or dy != 0:
                    draw.text(
                        (x + dx, y + dy), text,
                        font=font, fill=stroke_color
                    )
        
        # Main text
        text_color = template.get("text_color", "#FFFF00")
        draw.text((x, y), text, font=font, fill=text_color)
        
        return img

    def _calculate_text_position(
        self, width, height, txt_w, txt_h,
        position, face_bbox
    ):
        """Calculate text position avoiding faces."""
        # Default positions
        positions_map = {
            "top": (
                (width - txt_w) / 2,
                height * 0.05
            ),
            "center": (
                (width - txt_w) / 2,
                (height - txt_h) / 2
            ),
            "bottom": (
                (width - txt_w) / 2,
                height * 0.85 - txt_h
            ),
            "top_left": (width * 0.05, height * 0.05),
            "top_right": (
                width - txt_w - width * 0.05,
                height * 0.05
            ),
            "bottom_left": (
                width * 0.05,
                height * 0.85 - txt_h
            ),
            "bottom_right": (
                width - txt_w - width * 0.05,
                height * 0.85 - txt_h
            ),
        }
        
        x, y = positions_map.get(
            position,
            positions_map["center"]
        )
        
        # Check face overlap
        if face_bbox:
            fx1, fy1, fx2, fy2 = face_bbox
            text_bottom = y + txt_h
            text_right = x + txt_w
            
            # If text overlaps face, reposition
            if (y < fy2 and text_bottom > fy1 and
                    x < fx2 and text_right > fx1):
                # Move text above or below face
                if fy1 > height / 2:
                    # Face in bottom, put text on top
                    y = height * 0.05
                else:
                    # Face on top, put text on bottom
                    y = height * 0.85 - txt_h
        
        return int(x), int(y)

    def _load_font(self, size, weight="bold"):
        """Load appropriate font."""
        # Windows fonts
        font_paths = {
            "black":    ["arialbd.ttf", "impact.ttf"],
            "bold":     ["arialbd.ttf", "calibrib.ttf"],
            "medium":   ["arial.ttf", "calibri.ttf"],
            "light":    ["ariali.ttf", "calibril.ttf"],
            "serif":    ["timesbd.ttf", "georgia.ttf"],
            "impact":   ["impact.ttf", "arialbd.ttf"],
            "elegant":  ["georgia.ttf", "timesbd.ttf"],
            "playful":  ["comic.ttf", "arialbd.ttf"],
            "cursive":  ["scriptbl.ttf", "georgia.ttf"],
            "tech":     ["consolab.ttf", "cour.ttf"],
        }
        
        preferred = font_paths.get(weight, ["arialbd.ttf"])
        
        for font_name in preferred:
            try:
                return ImageFont.truetype(font_name, size)
            except Exception:
                continue
        
        # Fallback to Linux/Mac
        for path in [
            "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
            "/System/Library/Fonts/Helvetica.ttc",
        ]:
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                continue
        
        # Ultimate fallback
        return ImageFont.load_default()


# ═══════════════════════════════════════════════════════════════
# STANDALONE TEST
# ═══════════════════════════════════════════════════════════════
if __name__ == "__main__":
    print("=" * 55)
    print("Universal Thumbnail Generator V3.0")
    print("=" * 55)
    print(f"Total Templates: {len(TEMPLATE_CATALOG)}")
    print()
    
    gen = ThumbnailGenerator()
    
    # Show categories
    print("📋 Available Categories:")
    for cat, temps in gen.get_templates_by_category().items():
        print(f"\n{cat}:")
        for t in temps:
            print(f"  - {t['name']}")
    
    print()
    video = input("Enter video path: ").strip()
    if video and os.path.exists(video):
        template = input(
            "Template ID (default: mrbeast_extreme): "
        ).strip() or "mrbeast_extreme"
        
        result = gen.generate_thumbnail(
            video,
            template_id=template,
            num_variations=3,
            auto_text=True,
        )
        if result:
            print(f"\n✅ Success: {result}")