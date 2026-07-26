import os
import time
import random


class AIWriter:
    """
    AI-powered title and hashtag generator.
    - Uses OpenAI GPT if API key is configured
    - Falls back to smart local generation if not
    - Includes retry logic and rate limit handling
    """

    # FIX 5: Rich local fallback templates
    _FALLBACK_EMOJIS = [
        "🔥", "😱", "🤩", "💯", "🚀",
        "😂", "❤️", "👀", "⚡", "🎯",
        "🙌", "😍", "💥", "🤯", "✨",
    ]

    _FALLBACK_HASHTAGS = [
        "#viral #trending #foryou #fyp #funny",
        "#viral #reels #amazing #wow #mustwatch",
        "#trending #foryoupage #fun #omg #relatable",
        "#viral #lol #hilarious #dailyvideo #watchthis",
        "#foryou #trending #reels #epic #sharethis",
    ]

    _POWER_WORDS = [
        "You Won't Believe", "This Is Insane",
        "Nobody Expected This", "Wait For It",
        "This Changed Everything", "Gone Wrong",
        "Shocking Moment", "Must Watch",
        "Unbelievable", "Mind Blowing",
    ]

    def __init__(self, api_key: str = None):
        """
        Initialize AIWriter.
        FIX 1: Load API key from env variable first,
                then parameter, then config file.
        """
        # Priority: env var → parameter → config file → None
        resolved_key = (
            os.environ.get("OPENAI_API_KEY")
            or (api_key if api_key and api_key != "YOUR_OPENAI_API_KEY" else None)
            or self._load_key_from_file()
        )

        self.client = None
        if resolved_key:
            try:
                from openai import OpenAI
                self.client = OpenAI(api_key=resolved_key)
                self._api_key_set = True
            except ImportError:
                print(
                    "[-] openai package not installed.\n"
                    "    Run: pip install openai\n"
                    "    Falling back to local title generation."
                )
                self._api_key_set = False
            except Exception as e:
                print(f"[-] OpenAI init failed: {e}")
                self._api_key_set = False
        else:
            self._api_key_set = False

    # ─────────────────────────────────────────────
    # FIX 1: Load key from config file
    # ─────────────────────────────────────────────
    @staticmethod
    def _load_key_from_file() -> str | None:
        """Try to load API key from a local config file."""
        config_path = os.path.join(
            os.path.dirname(__file__), "openai_key.txt"
        )
        if os.path.exists(config_path):
            try:
                key = open(config_path).read().strip()
                if key and key != "YOUR_OPENAI_API_KEY":
                    return key
            except Exception:
                pass
        return None

    # ─────────────────────────────────────────────
    # FIX 2 + 3: API call with retry + rate limit
    # ─────────────────────────────────────────────
    def _call_api(
        self,
        messages: list,
        max_tokens: int = 150,
        temperature: float = 0.7,
        retries: int = 3,
        ui_log=print,
    ) -> str | None:
        """
        Call OpenAI API with automatic retry and rate limit handling.
        Returns response text or None on failure.
        """
        if not self.client:
            return None

        for attempt in range(1, retries + 1):
            try:
                response = self.client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
                return response.choices[0].message.content.strip()

            except Exception as e:
                err_type = type(e).__name__
                err_msg  = str(e).lower()

                # FIX 3: Rate limit → wait and retry
                if "ratelimit" in err_type.lower() or "rate limit" in err_msg:
                    wait = 20 * attempt
                    ui_log(
                        f"[!] OpenAI Rate Limit hit. "
                        f"Waiting {wait}s before retry {attempt}/{retries}..."
                    )
                    time.sleep(wait)
                    continue

                # Quota exceeded → no point retrying
                elif "quota" in err_msg or "billing" in err_msg:
                    ui_log(
                        "[-] OpenAI quota exceeded or billing issue.\n"
                        "    Check: https://platform.openai.com/account/usage"
                    )
                    return None

                # Auth error → no point retrying
                elif "auth" in err_msg or "api key" in err_msg or "401" in err_msg:
                    ui_log(
                        "[-] OpenAI API key invalid or unauthorized.\n"
                        "    Set your key in: openai_key.txt"
                    )
                    return None

                # Network error → retry
                elif attempt < retries:
                    wait = 3 * attempt
                    ui_log(
                        f"[!] API call failed ({err_type}). "
                        f"Retry {attempt}/{retries} in {wait}s..."
                    )
                    time.sleep(wait)

                else:
                    ui_log(
                        f"[-] API call failed after {retries} attempts: "
                        f"{err_type}: {e}"
                    )
                    return None

        return None

    # ─────────────────────────────────────────────
    # FIX 5: Smart local title generator
    # ─────────────────────────────────────────────
    def _local_rewrite_title(self, original_title: str) -> str:
        """
        Generate a catchy title locally (no API needed).
        Uses power words, random emojis, and hashtags.
        """
        # Pick random elements
        emoji1   = random.choice(self._FALLBACK_EMOJIS)
        emoji2   = random.choice(self._FALLBACK_EMOJIS)
        power    = random.choice(self._POWER_WORDS)
        hashtags = random.choice(self._FALLBACK_HASHTAGS)

        # Clean original title
        clean = original_title.strip()
        if len(clean) > 60:
            clean = clean[:57] + "..."

        # Random template
        templates = [
            f"{emoji1} {power}! {clean} {emoji2}\n{hashtags}",
            f"{clean} {emoji1} | {power}!\n{hashtags}",
            f"{power}: {clean} {emoji1}{emoji2}\n{hashtags}",
            f"{emoji1} {clean} — You NEED to see this!\n{hashtags}",
            f"Wait for it... {clean} {emoji1}\n{hashtags}",
        ]
        return random.choice(templates)

    def _local_generate_hashtags(self, topic: str) -> str:
        """Generate hashtags locally based on topic keywords."""
        base = random.choice(self._FALLBACK_HASHTAGS)

        # Add topic-based tags
        words = topic.lower().split()[:3]
        topic_tags = " ".join(
            f"#{w.replace(' ', '').replace('-', '')}"
            for w in words
            if len(w) > 3
        )
        return f"{base} {topic_tags}".strip()

    # ─────────────────────────────────────────────
    # PUBLIC: Rewrite Title
    # ─────────────────────────────────────────────
    def rewrite_title(
        self, original_title: str, ui_log=print
    ) -> str:
        """
        Rewrite video title to be viral for Facebook.
        Uses OpenAI if available, otherwise local fallback.
        """
        ui_log("[*] Generating viral title...")

        if not self.client:
            ui_log(
                "[!] OpenAI not configured. "
                "Using local title generator."
            )
            result = self._local_rewrite_title(original_title)
            ui_log(f"[+] Local Title: {result[:60]}...")
            return result

        prompt = (
            f"Rewrite this video title for a viral Facebook post.\n"
            f"Rules:\n"
            f"- Make it catchy and emotional\n"
            f"- Add 3 relevant emojis\n"
            f"- Add 5 popular hashtags at the end\n"
            f"- Keep total under 200 characters\n"
            f"- Do NOT add quotes or explanations\n"
            f"Original: {original_title}"
        )

        messages = [
            {
                "role": "system",
                "content": (
                    "You are an expert viral social media copywriter "
                    "specializing in Facebook video content. "
                    "You write short, punchy, emotional titles that "
                    "get maximum engagement."
                ),
            },
            {"role": "user", "content": prompt},
        ]

        # FIX 2+3: Call with retry
        result = self._call_api(
            messages,
            max_tokens=150,
            temperature=0.8,
            retries=3,
            ui_log=ui_log,
        )

        if result:
            ui_log(f"[+] AI Title: {result[:70]}...")
            return result
        else:
            # Graceful fallback
            ui_log("[!] AI failed. Using local fallback title.")
            return self._local_rewrite_title(original_title)

    # ─────────────────────────────────────────────
    # PUBLIC: Generate Hashtags
    # ─────────────────────────────────────────────
    def generate_hashtags(
        self, topic: str, ui_log=print
    ) -> str:
        """
        Generate trending hashtags for a topic.
        Uses OpenAI if available, otherwise local fallback.
        """
        ui_log("[*] Generating hashtags...")

        if not self.client:
            result = self._local_generate_hashtags(topic)
            ui_log(f"[+] Local Hashtags: {result}")
            return result

        prompt = (
            f"Generate 8 popular Facebook hashtags for a video about: "
            f"'{topic}'.\n"
            f"Rules:\n"
            f"- Only return hashtags separated by spaces\n"
            f"- No explanations, no numbering\n"
            f"- Mix broad and specific tags\n"
            f"- Start each with #"
        )

        messages = [
            {"role": "user", "content": prompt}
        ]

        result = self._call_api(
            messages,
            max_tokens=80,
            temperature=0.5,
            retries=2,
            ui_log=ui_log,
        )

        if result:
            ui_log(f"[+] Hashtags: {result[:80]}")
            return result
        else:
            return self._local_generate_hashtags(topic)

    # ─────────────────────────────────────────────
    # FIX 4: Combined title + hashtags in ONE call
    # ─────────────────────────────────────────────
    def rewrite_title_with_hashtags(
        self, original_title: str, ui_log=print
    ) -> tuple[str, str]:
        """
        Generate both viral title AND hashtags in a single API call.
        FIX 4: Saves API cost vs calling both separately.
        Returns (title, hashtags) tuple.
        """
        ui_log("[*] Generating title + hashtags (single API call)...")

        if not self.client:
            title    = self._local_rewrite_title(original_title)
            hashtags = self._local_generate_hashtags(original_title)
            return title, hashtags

        prompt = (
            f"For this video title: '{original_title}'\n\n"
            f"Return EXACTLY in this format (2 lines only):\n"
            f"TITLE: [viral title with 2-3 emojis, under 150 chars]\n"
            f"TAGS: [8-10 hashtags separated by spaces]\n\n"
            f"No other text."
        )

        messages = [
            {
                "role": "system",
                "content": (
                    "You are a viral Facebook content expert. "
                    "Always respond in the exact format requested."
                ),
            },
            {"role": "user", "content": prompt},
        ]

        result = self._call_api(
            messages,
            max_tokens=200,
            temperature=0.8,
            retries=3,
            ui_log=ui_log,
        )

        if result:
            try:
                lines    = result.strip().splitlines()
                title    = ""
                hashtags = ""
                for line in lines:
                    if line.upper().startswith("TITLE:"):
                        title = line.split(":", 1)[1].strip()
                    elif line.upper().startswith("TAGS:"):
                        hashtags = line.split(":", 1)[1].strip()

                if title and hashtags:
                    ui_log(f"[+] AI Title   : {title[:60]}...")
                    ui_log(f"[+] AI Hashtags: {hashtags[:60]}...")
                    return title, hashtags
            except Exception as parse_err:
                ui_log(f"[!] Parse error: {parse_err}. Using raw result.")
                return result, self._local_generate_hashtags(original_title)

        # Fallback
        title    = self._local_rewrite_title(original_title)
        hashtags = self._local_generate_hashtags(original_title)
        return title, hashtags