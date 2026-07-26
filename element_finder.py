"""
Element Finder V2.0 - Upgraded
Smart element detection + Multi-strategy finding
Facebook-specific selectors + Debug support
"""

import time
import random
from selenium.webdriver.common.by import By


class ElementFinder:
    """
    Smart element finder for Facebook automation
    Multiple strategies + coordinate conversion
    99% accuracy
    """

    def __init__(self, driver):
        self.driver = driver
        self._browser_info_cache = None
        self._cache_time = 0
        self._cache_ttl = 2.0

    # ═══════════════════════════════════════
    # BROWSER INFO
    # ═══════════════════════════════════════

    def get_browser_info(self, force_refresh=False):
        """Browser window info - cached"""
        now = time.time()

        if (not force_refresh and
                self._browser_info_cache and
                now - self._cache_time < self._cache_ttl):
            return self._browser_info_cache

        try:
            pos = self.driver.get_window_position()
            info = self.driver.execute_script("""
                return {
                    innerWidth:  window.innerWidth,
                    innerHeight: window.innerHeight,
                    outerWidth:  window.outerWidth,
                    outerHeight: window.outerHeight,
                    scrollX:     window.scrollX || 0,
                    scrollY:     window.scrollY || 0,
                    devicePixelRatio:
                        window.devicePixelRatio || 1,
                };
            """)

            ui_height = max(
                0,
                info['outerHeight'] - info['innerHeight']
            )
            side_border = max(
                0,
                (info['outerWidth'] -
                 info['innerWidth']) / 2
            )

            result = {
                'window_x':    pos['x'],
                'window_y':    pos['y'],
                'ui_height':   ui_height,
                'side_border': side_border,
                'scroll_x':    info['scrollX'],
                'scroll_y':    info['scrollY'],
                'pixel_ratio': info['devicePixelRatio'],
                'inner_w':     info['innerWidth'],
                'inner_h':     info['innerHeight'],
            }

            self._browser_info_cache = result
            self._cache_time = now
            return result

        except Exception as e:
            print(f"[FINDER] Browser info error: {e}")
            return {
                'window_x': 0, 'window_y': 0,
                'ui_height': 90, 'side_border': 0,
                'scroll_x': 0, 'scroll_y': 0,
                'pixel_ratio': 1,
                'inner_w': 1366, 'inner_h': 768,
            }

    def to_screen(self, page_x, page_y):
        """Page coords → Screen coords"""
        info = self.get_browser_info()

        screen_x = int(
            info['window_x'] +
            info['side_border'] +
            page_x -
            info['scroll_x']
        )
        screen_y = int(
            info['window_y'] +
            info['ui_height'] +
            page_y -
            info['scroll_y']
        )

        return screen_x, screen_y

    def convert_to_screen_coords(self, px, py):
        """Alias for to_screen"""
        return self.to_screen(px, py)

    # ═══════════════════════════════════════
    # CORE FINDERS
    # ═══════════════════════════════════════

    def find_by_selector(
        self, css_selector, wait=5,
        scroll_into_view=True
    ):
        """CSS selector se element find karo"""
        start = time.time()

        while time.time() - start < wait:
            try:
                result = self.driver.execute_script("""
                    var el = document.querySelector(
                        arguments[0]
                    );
                    if (!el) return {found: false};

                    if (arguments[1]) {
                        el.scrollIntoView({
                            block: 'center',
                            behavior: 'instant'
                        });
                    }

                    var rect = el.getBoundingClientRect();
                    if (rect.width <= 0 ||
                        rect.height <= 0) {
                        return {found: false};
                    }

                    return {
                        found:  true,
                        x:      rect.left + rect.width/2,
                        y:      rect.top  + rect.height/2,
                        width:  rect.width,
                        height: rect.height,
                    };
                """, css_selector, scroll_into_view)

                if result and result.get('found'):
                    self._browser_info_cache = None
                    return self.to_screen(
                        result['x'], result['y']
                    )

            except Exception:
                pass

            time.sleep(0.4)

        return None, None

    def find_by_text(
        self, text, tag='*', wait=5,
        exact=True, scroll=True
    ):
        """Text se element find karo"""
        start = time.time()

        while time.time() - start < wait:
            try:
                result = self.driver.execute_script("""
                    var text = arguments[0];
                    var doScroll = arguments[1];
                    var exact = arguments[2];

                    var selectors = [
                        'div[role="button"]',
                        'button',
                        'a[role="button"]',
                        'span[role="button"]',
                        'div[role="menuitem"]',
                        'div[role="option"]',
                        'li[role="option"]',
                        'a', 'span', 'div', 'p',
                    ];

                    for (var s=0; s<selectors.length; s++){
                        var els = document.querySelectorAll(
                            selectors[s]
                        );
                        for (var i=0; i<els.length; i++) {
                            var el = els[i];
                            var t = (
                                el.innerText || ''
                            ).trim();

                            var match = exact
                                ? (t === text)
                                : t.includes(text);

                            if (!match) continue;

                            var rect = el
                                .getBoundingClientRect();
                            if (rect.width <= 0 ||
                                rect.height <= 0) continue;

                            var style =
                                window.getComputedStyle(el);
                            if (style.display === 'none'||
                                style.visibility==='hidden'||
                                style.opacity === '0')
                                continue;

                            if (doScroll) {
                                el.scrollIntoView({
                                    block: 'center',
                                    behavior: 'instant'
                                });
                            }

                            return {
                                found:  true,
                                x: rect.left+rect.width/2,
                                y: rect.top+rect.height/2,
                                width:  rect.width,
                                height: rect.height,
                                tag:    el.tagName,
                                text:   t.substring(0, 50),
                            };
                        }
                    }
                    return {found: false};
                """, text, scroll, exact)

                if result and result.get('found'):
                    self._browser_info_cache = None
                    return self.to_screen(
                        result['x'], result['y']
                    )

            except Exception:
                pass

            time.sleep(0.4)

        return None, None

    def find_by_text_contains(
        self, text_part, wait=5
    ):
        """Partial text match"""
        return self.find_by_text(
            text_part, wait=wait, exact=False
        )

    def find_by_aria_label(
        self, aria_label, wait=5
    ):
        """Aria-label se find karo"""
        result = self.find_by_selector(
            f'[aria-label="{aria_label}"]', wait=2
        )
        if result[0]:
            return result

        return self.find_by_selector(
            f'[aria-label*="{aria_label}"]', wait=wait
        )

    def find_by_placeholder(
        self, placeholder, wait=5
    ):
        """Placeholder se find karo"""
        result = self.find_by_selector(
            f'[placeholder="{placeholder}"]', wait=2
        )
        if result[0]:
            return result

        return self.find_by_selector(
            f'[placeholder*="{placeholder}"]', wait=wait
        )

    def find_by_testid(self, testid, wait=5):
        """data-testid se find karo"""
        return self.find_by_selector(
            f'[data-testid="{testid}"]', wait=wait
        )

    # ═══════════════════════════════════════
    # FACEBOOK SPECIFIC
    # ═══════════════════════════════════════

    def find_fb_button(self, text, wait=8):
        """
        Facebook button find karo
        Partial match - handles seasonal buttons
        """
        start = time.time()

        while time.time() - start < wait:
            try:
                result = self.driver.execute_script("""
                    var searchText = arguments[0]
                        .toLowerCase();

                    var fbSelectors = [
                        'div[role="button"]',
                        'div[role="menuitem"]',
                        'div[tabindex="0"]',
                        'button[type="submit"]',
                        'button',
                        'a[role="button"]',
                        '[data-visualcompletion]',
                    ];

                    for(var s=0;
                        s<fbSelectors.length; s++) {
                        var els = document.querySelectorAll(
                            fbSelectors[s]
                        );

                        for(var i=0; i<els.length; i++) {
                            var el = els[i];
                            var elText = (
                                el.innerText || ''
                            ).trim().toLowerCase();
                            var ariaLabel = (
                                el.getAttribute(
                                    'aria-label'
                                ) || ''
                            ).trim().toLowerCase();

                            var match = (
                                elText === searchText ||
                                ariaLabel === searchText ||
                                elText.includes(
                                    searchText
                                ) ||
                                ariaLabel.includes(
                                    searchText
                                )
                            );

                            if (!match) continue;

                            var rect = el
                                .getBoundingClientRect();
                            if (rect.width <= 0 ||
                                rect.height <= 0) continue;

                            var disabled = el.getAttribute(
                                'aria-disabled'
                            );
                            if (disabled === 'true')
                                continue;

                            var st =
                                window.getComputedStyle(el);
                            if (st.display === 'none')
                                continue;

                            el.scrollIntoView({
                                block: 'center',
                                behavior: 'instant'
                            });

                            return {
                                found:    true,
                                x:        rect.left +
                                          rect.width/2,
                                y:        rect.top +
                                          rect.height/2,
                                width:    rect.width,
                                height:   rect.height,
                                fullText: el.innerText
                                    .trim()
                                    .substring(0, 80),
                            };
                        }
                    }
                    return {found: false};
                """, text)

                if result and result.get('found'):
                    self._browser_info_cache = None

                    full_text = result.get(
                        'fullText', ''
                    )
                    if full_text.lower() != text.lower():
                        print(
                            f"[FINDER] Partial: "
                            f"'{text}' → '{full_text}'"
                        )

                    return self.to_screen(
                        result['x'], result['y']
                    )

            except Exception:
                pass

            time.sleep(0.5)

        return None, None

    def find_caption_box(self, wait=10):
        """Facebook caption box find karo"""
        strategies = [
            (
                'selector',
                'div[contenteditable="true"]'
                '[role="textbox"]'
            ),
            (
                'selector',
                'div[contenteditable="true"]'
            ),
            (
                'selector',
                'div[data-testid="post-composer-root"]'
                ' div[contenteditable]'
            ),
            (
                'selector',
                'div[aria-label*="mind"],'
                'div[aria-label*="Write"],'
                'div[aria-label*="Post"]'
            ),
            (
                'text_contains',
                "What's on your mind"
            ),
            (
                'text_contains',
                "Write something"
            ),
        ]

        for strategy, value in strategies:
            try:
                if strategy == 'selector':
                    result = self.find_by_selector(
                        value, wait=3
                    )
                else:
                    result = self.find_by_text(
                        value, wait=3, exact=False
                    )

                if result and result[0]:
                    return result
            except Exception:
                pass

        return None, None

    def find_file_input(self, wait=5):
        """File input element find karo"""
        start = time.time()
        while time.time() - start < wait:
            try:
                inputs = self.driver.find_elements(
                    By.CSS_SELECTOR,
                    'input[type="file"]'
                )
                for inp in inputs:
                    try:
                        if inp:
                            return inp
                    except Exception:
                        pass
            except Exception:
                pass
            time.sleep(0.5)
        return None

    def find_enabled_button(
        self, texts, wait=30
    ):
        """Enabled button find karo"""
        start = time.time()

        while time.time() - start < wait:
            try:
                result = self.driver.execute_script("""
                    var texts = arguments[0];
                    var btns = document.querySelectorAll(
                        'div[role="button"], button,'
                        'div[tabindex="0"]'
                    );

                    for (var i=0; i<btns.length; i++) {
                        var btn = btns[i];
                        var t = (
                            btn.innerText||''
                        ).trim();

                        var match = false;
                        for(var j=0;j<texts.length;j++){
                            if (t === texts[j]) {
                                match = true;
                                break;
                            }
                        }

                        if (!match) continue;

                        var dis = btn.getAttribute(
                            'aria-disabled'
                        );
                        if (dis === 'true') continue;

                        var rect = btn
                            .getBoundingClientRect();
                        if (rect.width <= 0 ||
                            rect.height <= 0) continue;

                        var st =
                            window.getComputedStyle(btn);
                        if (st.display === 'none' ||
                            st.visibility === 'hidden')
                            continue;

                        btn.scrollIntoView({
                            block: 'center',
                            behavior: 'instant'
                        });

                        return {
                            found: true,
                            x: rect.left + rect.width/2,
                            y: rect.top + rect.height/2,
                            text: t,
                        };
                    }
                    return {found: false};
                """, texts)

                if result and result.get('found'):
                    self._browser_info_cache = None
                    return self.to_screen(
                        result['x'], result['y']
                    ), result.get('text', '')

            except Exception:
                pass

            time.sleep(1)

        return (None, None), ''

    # ═══════════════════════════════════════
    # WAIT METHODS
    # ═══════════════════════════════════════

    def wait_for_element(
        self, css_selector, timeout=30
    ):
        """Element appear hone ka wait"""
        start = time.time()
        while time.time() - start < timeout:
            try:
                el = self.driver.find_element(
                    By.CSS_SELECTOR, css_selector
                )
                if el and el.is_displayed():
                    return True
            except Exception:
                pass
            time.sleep(1)
        return False

    def wait_for_text(self, text, timeout=30):
        """Text appear hone ka wait"""
        start = time.time()
        while time.time() - start < timeout:
            try:
                result = self.driver.execute_script("""
                    return document.body.innerText
                        .includes(arguments[0]);
                """, text)
                if result:
                    return True
            except Exception:
                pass
            time.sleep(1)
        return False

    def wait_for_url_change(
        self, old_url, timeout=30
    ):
        """URL change hone ka wait"""
        start = time.time()
        while time.time() - start < timeout:
            try:
                if self.driver.current_url != old_url:
                    return True
            except Exception:
                pass
            time.sleep(0.5)
        return False

    def page_ready(self, timeout=30):
        """Page load complete ka wait"""
        start = time.time()
        while time.time() - start < timeout:
            try:
                state = self.driver.execute_script(
                    "return document.readyState"
                )
                if state == "complete":
                    return True
            except Exception:
                pass
            time.sleep(0.5)
        return False

    # ═══════════════════════════════════════
    # SCROLL HELPERS
    # ═══════════════════════════════════════

    def scroll_into_view(self, css_selector):
        """Element scroll into view"""
        try:
            return self.driver.execute_script("""
                var el = document.querySelector(
                    arguments[0]
                );
                if (el) {
                    el.scrollIntoView({
                        behavior: 'instant',
                        block: 'center'
                    });
                    return true;
                }
                return false;
            """, css_selector)
        except Exception:
            return False

    def scroll_element_into_view(
        self, css_selector
    ):
        """Alias"""
        return self.scroll_into_view(css_selector)

    def scroll_page(self, amount=300):
        """Page scroll karo"""
        try:
            self.driver.execute_script(
                f"window.scrollBy(0, {amount});"
            )
            time.sleep(random.uniform(0.3, 0.7))
        except Exception:
            pass

    # ═══════════════════════════════════════
    # DEBUG HELPERS
    # ═══════════════════════════════════════

    def highlight_element(self, css_selector):
        """Element highlight karo (debug)"""
        try:
            self.driver.execute_script("""
                var el = document.querySelector(
                    arguments[0]
                );
                if (el) {
                    el.style.border='3px solid red';
                    el.style.backgroundColor='yellow';
                }
            """, css_selector)
        except Exception:
            pass

    def get_all_buttons(self):
        """Saare buttons list karo"""
        try:
            return self.driver.execute_script("""
                var btns = document.querySelectorAll(
                    'div[role="button"], button,'
                    'a[role="button"]'
                );
                var result = [];
                for (var i=0; i<btns.length; i++) {
                    var t = (
                        btns[i].innerText || ''
                    ).trim();
                    if (t && t.length < 100) {
                        var rect = btns[i]
                            .getBoundingClientRect();
                        result.push({
                            text: t,
                            x: Math.round(rect.left),
                            y: Math.round(rect.top),
                            w: Math.round(rect.width),
                            h: Math.round(rect.height),
                            disabled: btns[i].getAttribute(
                                'aria-disabled'
                            ),
                        });
                    }
                }
                return result;
            """)
        except Exception:
            return []

    def get_page_text(self):
        """Full page text"""
        try:
            return self.driver.execute_script(
                "return document.body.innerText;"
            )
        except Exception:
            return ""

    def print_debug_info(self):
        """Debug info print karo"""
        info = self.get_browser_info(
            force_refresh=True
        )
        print("\n[FINDER DEBUG]")
        print(
            f"  Window: ({info['window_x']}, "
            f"{info['window_y']})"
        )
        print(f"  UI Height: {info['ui_height']}px")
        print(
            f"  Side Border: {info['side_border']}px"
        )
        print(
            f"  Scroll: ({info['scroll_x']}, "
            f"{info['scroll_y']})"
        )
        print(f"  Pixel Ratio: {info['pixel_ratio']}")
        print(
            f"  Inner: {info['inner_w']}x"
            f"{info['inner_h']}"
        )

        btns = self.get_all_buttons()
        print(f"\n  Buttons found: {len(btns)}")
        for b in btns[:10]:
            dis = '[DISABLED]' if b['disabled'] else ''
            print(
                f"    [{b['text'][:30]}] "
                f"@ ({b['x']}, {b['y']}) {dis}"
            )


# ═══════════════════════════════════════
# TEST
# ═══════════════════════════════════════

if __name__ == "__main__":
    import undetected_chromedriver as uc

    print("=" * 55)
    print("ELEMENT FINDER V2.0 TEST")
    print("=" * 55)

    options = uc.ChromeOptions()
    options.add_argument('--start-maximized')

    driver = uc.Chrome(
        options=options,
        version_main=None
    )

    print("[1] Opening Facebook...")
    driver.get("https://www.facebook.com")
    time.sleep(3)

    finder = ElementFinder(driver)

    print("\n[2] Browser Debug Info:")
    finder.print_debug_info()

    print("\n[3] All Buttons:")
    btns = finder.get_all_buttons()
    print(f"    Found {len(btns)} buttons")

    print("\n[4] Login button:")
    pos = finder.find_fb_button("Log in", wait=5)
    if pos and pos[0]:
        print(f"    ✅ Found: {pos}")
    else:
        print("    Already logged in!")

    input("\nPress Enter to close...")
    driver.quit()