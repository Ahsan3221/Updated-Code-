(() => {
'use strict';

// ═══════════════════════════════════════════════════════
// FB HELPER - STEALTH SCANNER V3.0
// ═══════════════════════════════════════════════════════
// READ-ONLY passive scanner
// - No DOM modification
// - No click simulation from JS
// - Silent error handling
// - Minimal fingerprint
// - Random observer delays
// ═══════════════════════════════════════════════════════

const DEBUG = false;
const log = (...x) => { if (DEBUG) console.log('[FB]', ...x); };

// ═══════════════════════════════════════════════════════
// TARGET DEFINITIONS
// ═══════════════════════════════════════════════════════

const FB_TARGETS = {

    // ═══ POST CREATION (Business Suite) ═══

    // Old create_post - kept for backward compatibility
    // But smart_post_button is preferred for BS
    create_post: {
        textPatterns: [
            'create post', 'create a post',
            'write something', "what's on your mind",
            'share what', 'create reel'
        ],
        ariaPatterns: [
            'create a post', 'create post',
            'make a post', 'new post',
            'write a post', 'compose'
        ],
        selectors: [
            'div[role="button"][aria-label*="post" i]',
            'div[role="button"][aria-label*="create" i]',
            'div[data-testid*="composer"]',
            'div[data-testid*="create"]'
        ],
        svgPaths: ['pencil', 'edit', 'compose'],
        position: { maxY: 0.3, maxX: 0.5 },
        priority: [
            'selectors', 'ariaPatterns',
            'textPatterns', 'svgPaths', 'position'
        ]
    },

    // NEW: Smart post button (icon + sibling based)
    // Text changes seasonally, so we find by:
    // 1. Sibling of "Create Reel" (which is stable)
    // 2. Position (first in action row, top area)
    // 3. Icon detection (pencil/paper SVG)
    smart_post_button: {
        textPatterns: [
            'make a post', 'create post', 'create a post',
            'post for', 'share post', 'new post'
        ],
        ariaPatterns: [
            'create post', 'make post', 'new post'
        ],
        selectors: [
            'div[role="button"][aria-label*="post" i]:not([aria-label*="reel" i]):not([aria-label*="story" i]):not([aria-label*="ad" i])'
        ],
        siblingOf: 'create reel',
        position: { maxY: 0.4, maxX: 0.6 },
        priority: [
            'siblingOf', 'ariaPatterns',
            'textPatterns', 'selectors', 'position'
        ]
    },

    // Add photo/video button (STABLE TEXT)
    add_photo_video: {
        textPatterns: [
            'add photo/video', 'photo/video',
            'photo or video', 'add photos/videos',
            'add media'
        ],
        ariaPatterns: [
            'add photo', 'photo video',
            'add media'
        ],
        selectors: [
            'div[role="button"][aria-label*="photo" i]',
            'div[role="button"][aria-label*="video" i]',
            'div[role="button"][aria-label*="media" i]'
        ],
        svgPaths: ['camera', 'image', 'photo', 'video'],
        position: { minY: 0.3 },
        priority: [
            'textPatterns', 'ariaPatterns',
            'selectors', 'svgPaths'
        ]
    },

    // Caption/description box
    caption_box: {
        textPatterns: [
            'write something',
            "what's on your mind",
            'say something about this',
            'add a description'
        ],
        ariaPatterns: [
            'write something',
            "what's on your mind",
            'create a public post', 'description'
        ],
        selectors: [
            'div[contenteditable="true"][role="textbox"]',
            'div[contenteditable="true"][aria-label*="mind" i]',
            'div[contenteditable="true"][aria-label*="write" i]',
            'div[contenteditable="true"][aria-label*="description" i]',
            'div[contenteditable="true"]'
        ],
        position: {},
        priority: [
            'selectors', 'ariaPatterns', 'textPatterns'
        ]
    },

    // NEW: Reel description box (Create step)
    reel_description: {
        textPatterns: [
            'let viewers know',
            'about your reel'
        ],
        ariaPatterns: [
            'description', 'add a description',
            'reel description'
        ],
        selectors: [
            'div[contenteditable="true"][aria-label*="description" i]',
            'div[contenteditable="true"][role="textbox"]',
            'textarea[placeholder*="viewers" i]',
            'div[contenteditable="true"]'
        ],
        position: { maxY: 0.7 },
        priority: [
            'ariaPatterns', 'selectors',
            'textPatterns', 'position'
        ]
    },

    // ═══ PUBLISH / SHARE / NEXT BUTTONS ═══

    // Generic share button (for posts)
    share_button: {
        textPatterns: ['share', 'post', 'publish'],
        ariaPatterns: ['share', 'publish', 'post'],
        selectors: [
            'div[role="button"][aria-label="Share"]',
            'div[role="button"][aria-label="Post"]',
            'div[role="button"][aria-label="Publish"]'
        ],
        position: { minY: 0.7, minX: 0.5 },
        priority: [
            'selectors', 'textPatterns', 'position'
        ],
        mustBeEnabled: true
    },

    // NEW: Publish button (for POSTS - not reels)
    publish_button: {
        textPatterns: ['publish'],
        ariaPatterns: ['publish'],
        selectors: [
            'div[role="button"][aria-label="Publish"]',
            'button[aria-label="Publish"]'
        ],
        position: { minY: 0.85, minX: 0.5 },
        priority: [
            'ariaPatterns', 'textPatterns',
            'selectors', 'position'
        ],
        mustBeEnabled: true
    },

    // NEW: Share button (for REELS - final step)
    reel_share_button: {
        textPatterns: ['share'],
        ariaPatterns: ['share'],
        selectors: [
            'div[role="button"][aria-label="Share"]',
            'button[aria-label="Share"]'
        ],
        position: { minY: 0.85, minX: 0.7 },
        priority: [
            'ariaPatterns', 'textPatterns',
            'selectors', 'position'
        ],
        mustBeEnabled: true
    },

    // Next button (multi-step composer)
    next_button: {
        textPatterns: ['next'],
        ariaPatterns: ['next'],
        selectors: [
            'div[role="button"][aria-label="Next"]',
            'button[aria-label="Next"]'
        ],
        position: { minY: 0.85, minX: 0.7 },
        priority: [
            'ariaPatterns', 'selectors',
            'textPatterns', 'position'
        ],
        mustBeEnabled: true
    },

    // ═══ POPUPS / DISMISS BUTTONS ═══

    // Generic maybe later (works for most popups)
    maybe_later: {
        textPatterns: [
            'maybe later', 'not now', 'skip',
            'no thanks', 'dismiss'
        ],
        ariaPatterns: [
            'maybe later', 'dismiss', 'close'
        ],
        selectors: [
            'div[role="button"][aria-label*="later" i]',
            'div[role="button"][aria-label="Close"]'
        ],
        position: {},
        priority: [
            'textPatterns', 'selectors', 'ariaPatterns'
        ]
    },

    // NEW: Boost popup specific "Maybe later"
    boost_maybe_later: {
        textPatterns: ['maybe later'],
        ariaPatterns: ['maybe later'],
        selectors: [
            'div[role="dialog"] div[role="button"]'
        ],
        insideDialog: true,
        priority: [
            'textPatterns', 'ariaPatterns',
            'selectors'
        ]
    },

    // NEW: Switched to page popup close (X button)
    switched_popup_close: {
        textPatterns: [],
        ariaPatterns: ['close', 'dismiss'],
        selectors: [
            'div[aria-label="Close"][role="button"]',
            'div[role="button"][aria-label*="close" i]'
        ],
        position: { maxY: 0.95, maxX: 0.5 },
        priority: [
            'ariaPatterns', 'selectors', 'position'
        ]
    },

    // ═══ PROFILE / PAGE SWITCHING ═══

    // Profile switcher (top-right corner)
    profile_switcher: {
        textPatterns: [],
        ariaPatterns: [
            'your profile', 'account controls',
            'account', 'profile menu',
            'switch profile'
        ],
        selectors: [
            'div[role="button"][aria-label*="profile" i]',
            'div[role="button"][aria-label*="account" i]'
        ],
        position: { maxY: 0.1, minX: 0.85 },
        priority: [
            'position', 'ariaPatterns', 'selectors'
        ]
    },

    // Alias for profile_switcher (kept for compatibility)
    profile_menu_link: {
        textPatterns: [],
        ariaPatterns: [
            'your profile',
            'account controls',
            'account'
        ],
        selectors: [
            'div[role="button"][aria-label*="profile" i]',
            'div[role="button"][aria-label*="account" i]'
        ],
        position: { maxY: 0.1, minX: 0.85 },
        priority: [
            'position', 'selectors', 'ariaPatterns'
        ]
    },

    // Page in profile dropdown menu (dynamic name)
    page_in_menu: {
        textPatterns: [],
        selectors: [
            'div[role="menuitem"]',
            'div[role="option"]',
            'div[role="button"]',
            'li[role="option"]'
        ],
        hasImage: true,
        insideDialog: false,
        priority: ['dynamic_text', 'selectors']
    },

    // See all profiles button
    see_all_profiles: {
        textPatterns: [
            'see all profiles',
            'see all pages',
            'switch profile',
            'view all profiles'
        ],
        ariaPatterns: [
            'see all profiles',
            'see all pages'
        ],
        selectors: [
            'div[role="button"][aria-label*="all profiles" i]',
            'div[role="button"][aria-label*="all pages" i]'
        ],
        priority: [
            'textPatterns', 'ariaPatterns', 'selectors'
        ]
    },

    // ═══ NAVIGATION LINKS ═══

    // Meta Business Suite link (in page's left sidebar)
    meta_business_suite: {
        textPatterns: [
            'meta business suite',
            'business suite',
            'go to business suite'
        ],
        ariaPatterns: [
            'meta business suite',
            'business suite'
        ],
        selectors: [
            'a[href*="business.facebook.com"]',
            'div[role="link"][aria-label*="business" i]',
            'a[aria-label*="business" i]'
        ],
        position: { maxX: 0.25 },
        priority: [
            'textPatterns', 'ariaPatterns',
            'selectors', 'position'
        ]
    },

    // Facebook logo (top-left)
    facebook_logo: {
        textPatterns: [],
        ariaPatterns: ['facebook', 'home'],
        selectors: [
            'a[aria-label="Facebook"]',
            'a[href="/"]',
            'a[href="https://www.facebook.com/"]'
        ],
        position: { maxY: 0.1, maxX: 0.15 },
        priority: [
            'selectors', 'ariaPatterns', 'position'
        ]
    },

    // Business Suite navigation
    home_menu: {
        textPatterns: ['home', 'dashboard'],
        ariaPatterns: ['home'],
        selectors: [
            'a[href*="/latest/home"]',
            'div[role="link"][aria-label*="home" i]'
        ],
        position: { maxX: 0.25, maxY: 0.3 },
        priority: [
            'position', 'ariaPatterns', 'selectors'
        ]
    },

    posts_menu: {
        textPatterns: [
            'posts', 'content', 'posts & stories'
        ],
        ariaPatterns: ['posts', 'content'],
        selectors: [
            'a[href*="posts"]',
            'a[href*="content"]',
            'div[role="link"][aria-label*="posts" i]'
        ],
        position: { maxX: 0.25 },
        priority: [
            'ariaPatterns', 'textPatterns',
            'selectors', 'position'
        ]
    },

    planner_menu: {
        textPatterns: ['planner', 'schedule', 'calendar'],
        ariaPatterns: ['planner', 'schedule'],
        selectors: [
            'a[href*="planner"]',
            'div[role="link"][aria-label*="planner" i]'
        ],
        position: { maxX: 0.25 },
        priority: [
            'ariaPatterns', 'textPatterns',
            'selectors', 'position'
        ]
    },

    schedule_button: {
        textPatterns: [
            'schedule', 'scheduling options',
            'schedule post', 'schedule for later'
        ],
        ariaPatterns: ['schedule', 'scheduling'],
        selectors: [
            'div[aria-label*="Schedule" i]',
            '[aria-haspopup="listbox"]'
        ],
        position: { minY: 0.3 },
        priority: [
            'textPatterns', 'ariaPatterns', 'selectors'
        ]
    },

    // ═══ FILE INPUT ═══

    file_input: {
        selectors: ['input[type="file"]'],
        priority: ['selectors'],
        returnElement: true
    }
};

// ═══════════════════════════════════════════════════════
// TEXT NORMALIZATION
// ═══════════════════════════════════════════════════════

function norm(s) {
    if (!s) return '';
    return String(s)
        .toLowerCase()
        .replace(/\s+/g, ' ')
        .trim();
}

// ═══════════════════════════════════════════════════════
// VISIBILITY CHECK
// ═══════════════════════════════════════════════════════

function isVisible(el) {
    if (!el || !el.isConnected) return false;
    try {
        const s = getComputedStyle(el);
        const r = el.getBoundingClientRect();
        return (
            s.display !== 'none' &&
            s.visibility !== 'hidden' &&
            Number(s.opacity) !== 0 &&
            r.width > 2 &&
            r.height > 2 &&
            r.bottom > 0 &&
            r.right > 0 &&
            r.top < innerHeight &&
            r.left < innerWidth
        );
    } catch (e) {
        return false;
    }
}

// ═══════════════════════════════════════════════════════
// DISABLED CHECK
// ═══════════════════════════════════════════════════════

function isDisabled(el) {
    if (!el) return true;
    try {
        return (
            el.disabled === true ||
            el.getAttribute('disabled') !== null ||
            el.getAttribute('aria-disabled') === 'true'
        );
    } catch (e) {
        return true;
    }
}

// ═══════════════════════════════════════════════════════
// HAS IMAGE (for menu items)
// ═══════════════════════════════════════════════════════

function hasImage(el) {
    if (!el) return false;
    try {
        return !!el.querySelector(
            'img, svg, image, [role="img"]'
        );
    } catch (e) {
        return false;
    }
}

// ═══════════════════════════════════════════════════════
// GET ELEMENT CENTER COORDINATES
// ═══════════════════════════════════════════════════════

function getElementCenter(el) {
    try {
        const r = el.getBoundingClientRect();
        // 🔴 FIX: Add window screen offsets for Win32 absolute mouse control
        const screenX = Math.round(window.screenX + r.left + r.width / 2);
        const screenY = Math.round(window.screenY + r.top + r.height / 2);
        return {
            x: screenX,                    // ✅ Absolute screen coords
            y: screenY,                    // ✅ Absolute screen coords
            width: Math.round(r.width),
            height: Math.round(r.height)
        };
    } catch (e) {
        return { x: 0, y: 0, width: 0, height: 0 };
    }
}

// ═══════════════════════════════════════════════════════
// POSITION HINT MATCHING
// ═══════════════════════════════════════════════════════

function matchesPositionHint(candidate, p) {
    if (!p || Object.keys(p).length === 0) return true;
    try {
        const r = candidate.element.getBoundingClientRect();
        const x = (r.left + r.width / 2) / innerWidth;
        const y = (r.top + r.height / 2) / innerHeight;
        if (p.minX != null && x < p.minX) return false;
        if (p.maxX != null && x > p.maxX) return false;
        if (p.minY != null && y < p.minY) return false;
        if (p.maxY != null && y > p.maxY) return false;
        return true;
    } catch (e) {
        return false;
    }
}

// ═══════════════════════════════════════════════════════
// GET COMBINED TEXT OF ELEMENT
// ═══════════════════════════════════════════════════════

function textOf(el) {
    if (!el) return '';
    try {
        return norm(
            (el.innerText || '') + ' ' +
            (el.getAttribute('aria-label') || '') + ' ' +
            (el.title || '')
        );
    } catch (e) {
        return '';
    }
}

// ═══════════════════════════════════════════════════════
// CHECK IF ELEMENT IS INSIDE A DIALOG
// ═══════════════════════════════════════════════════════

function isInsideDialog(el) {
    if (!el) return false;
    try {
        return !!el.closest('[role="dialog"]');
    } catch (e) {
        return false;
    }
}

// ═══════════════════════════════════════════════════════
// FIND SIBLING BY TEXT
// ═══════════════════════════════════════════════════════
// Used for finding "Post" button by locating "Create Reel"
// and finding its sibling button

function findBySiblingText(targetText) {
    const results = [];
    try {
        const all = document.querySelectorAll(
            'div[role="button"], button, a[role="button"]'
        );

        // Find the sibling anchor element first
        let anchor = null;
        for (const el of all) {
            if (!isVisible(el)) continue;
            const t = textOf(el);
            if (t.includes(norm(targetText))) {
                anchor = el;
                break;
            }
        }

        if (!anchor) return results;

        // Get parent container
        const parent = anchor.parentElement;
        if (!parent) return results;

        // Get all sibling buttons at same level
        const siblings = parent.parentElement
            ? parent.parentElement.querySelectorAll(
                'div[role="button"], button'
            )
            : [];

        for (const sib of siblings) {
            if (sib === anchor) continue;
            if (!isVisible(sib)) continue;
            results.push(sib);
        }
    } catch (e) {}

    return results;
}

// ═══════════════════════════════════════════════════════
// GET UPLOAD PROGRESS PERCENTAGE
// ═══════════════════════════════════════════════════════
// Returns: { percent: 0-100, complete: bool, found: bool }

function getUploadProgress() {
    const result = {
        found: false,
        percent: 0,
        complete: false
    };

    try {
        // Method 1: Look for percentage text (e.g., "57%", "100%")
        const bodyText = document.body.innerText || '';
        const percentMatch = bodyText.match(
            /(\d{1,3})%/g
        );

        if (percentMatch) {
            // Get all percentages, pick the highest
            const percents = percentMatch
                .map(p => parseInt(p))
                .filter(p => p >= 0 && p <= 100);

            if (percents.length > 0) {
                result.found = true;
                result.percent = Math.max(...percents);
            }
        }

        // Method 2: Check for green checkmark near percentage
        // (indicates 100% complete)
        const svgs = document.querySelectorAll('svg');
        for (const svg of svgs) {
            const rect = svg.getBoundingClientRect();
            if (rect.width < 30 && rect.height < 30) {
                const fill = svg.getAttribute('fill') || '';
                const color = getComputedStyle(svg).color;
                // Check for green color
                if (fill.includes('#') ||
                    color.includes('rgb')) {
                    // Rough green detection
                    if (color.includes('0, 128') ||
                        color.includes('66, 183') ||
                        fill.toLowerCase().includes('00a400')) {
                        result.complete = true;
                    }
                }
            }
        }

        // Method 3: Check Next/Publish button state
        // If enabled and no progress showing = complete
        if (result.percent >= 100) {
            result.complete = true;
        }

    } catch (e) {}

    return result;
}

// ═══════════════════════════════════════════════════════
// CHECK IF UPLOAD IS COMPLETE
// ═══════════════════════════════════════════════════════

function isUploadComplete() {
    try {
        // Check 1: No progress percentage < 100 visible
        const bodyText = document.body.innerText || '';
        const percentMatch = bodyText.match(/(\d{1,3})%/g);

        if (percentMatch) {
            const percents = percentMatch
                .map(p => parseInt(p))
                .filter(p => p >= 0 && p < 100);

            // If any percentage < 100, still uploading
            if (percents.length > 0) return false;
        }

        // Check 2: Next/Share button is enabled
        const buttons = document.querySelectorAll(
            'div[role="button"], button'
        );

        for (const btn of buttons) {
            if (!isVisible(btn)) continue;
            const label = norm(
                btn.getAttribute('aria-label') ||
                btn.innerText || ''
            );

            if (label === 'next' ||
                label === 'share' ||
                label === 'publish') {
                if (!isDisabled(btn)) {
                    return true;
                }
            }
        }

        return false;
    } catch (e) {
        return false;
    }
}
// ═══════════════════════════════════════════════════════
// CONTEXT (Window/Screen info)
// ═══════════════════════════════════════════════════════

function context() {
    try {
        return {
            screenX: window.screenX,
            screenY: window.screenY,
            outerWidth: window.outerWidth,
            outerHeight: window.outerHeight,
            innerWidth: window.innerWidth,
            innerHeight: window.innerHeight,
            scrollX: window.scrollX,
            scrollY: window.scrollY,
            devicePixelRatio: window.devicePixelRatio
        };
    } catch (e) {
        return {};
    }
}

// ═══════════════════════════════════════════════════════
// STRATEGY RUNNER
// ═══════════════════════════════════════════════════════
// Runs different detection strategies for target finding

function runStrategy(strategy, target, data) {
    if (!data) data = {};
    const out = [];

    const push = (el, score) => {
        if (!score) score = 0;
        if (el && isVisible(el)) {
            out.push({
                element: el,
                strategy: strategy,
                textMatchScore: score
            });
        }
    };

    // ═══ STRATEGY: SIBLING OF (NEW) ═══
    if (strategy === 'siblingOf') {
        const siblingText = target.siblingOf;
        if (siblingText) {
            const siblings = findBySiblingText(siblingText);
            for (const el of siblings) {
                push(el, 30);
            }
        }
        return out;
    }

    // ═══ STRATEGY: DYNAMIC TEXT ═══
    // Used for page names (workspace-specific)
    if (strategy === 'dynamic_text') {
        const searchText = data.name ||
            data.text ||
            data.page_name ||
            '';

        if (!searchText) return out;

        const all = document.querySelectorAll(
            'div[role="menuitem"], ' +
            'div[role="option"], ' +
            'div[role="button"], ' +
            'li[role="option"], ' +
            'a[role="link"]'
        );

        for (const el of all) {
            if (!isVisible(el)) continue;
            const hay = textOf(el);
            if (hay.includes(norm(searchText))) {
                push(el, 35);
            }
        }
        return out;
    }

    // ═══ STRATEGY: SELECTORS (CSS) ═══
    if (strategy === 'selectors') {
        for (const s of target.selectors || []) {
            try {
                const nodes = document.querySelectorAll(s);
                for (const e of nodes) {
                    // If insideDialog required, check
                    if (target.insideDialog === true) {
                        if (!isInsideDialog(e)) continue;
                    }
                    push(e, 20);
                }
            } catch (e) {}
        }
        return out;
    }

    // ═══ STRATEGY: TEXT PATTERNS ═══
    if (strategy === 'textPatterns') {
        const patterns = target.textPatterns || [];
        if (patterns.length === 0) return out;

        const all = document.querySelectorAll(
            'button, [role="button"], ' +
            '[role="menuitem"], [role="option"], ' +
            'input, textarea, ' +
            '[contenteditable="true"], a'
        );

        for (const el of all) {
            if (!isVisible(el)) continue;

            // Check dialog constraint
            if (target.insideDialog === true) {
                if (!isInsideDialog(el)) continue;
            }

            const hay = textOf(el);
            for (const p of patterns) {
                if (p && hay.includes(norm(p))) {
                    push(el, 25);
                    break;
                }
            }
        }
        return out;
    }

    // ═══ STRATEGY: ARIA PATTERNS ═══
    if (strategy === 'ariaPatterns') {
        const patterns = target.ariaPatterns || [];
        if (patterns.length === 0) return out;

        const all = document.querySelectorAll(
            'button, [role="button"], ' +
            '[role="menuitem"], [role="option"], ' +
            'input, textarea, ' +
            '[contenteditable="true"], a'
        );

        for (const el of all) {
            if (!isVisible(el)) continue;

            if (target.insideDialog === true) {
                if (!isInsideDialog(el)) continue;
            }

            const aria = norm(
                el.getAttribute('aria-label')
            );

            for (const p of patterns) {
                if (p && aria.includes(norm(p))) {
                    push(el, 25);
                    break;
                }
            }
        }
        return out;
    }

    // ═══ STRATEGY: SVG PATHS (Icon detection) ═══
    if (strategy === 'svgPaths') {
        const paths = target.svgPaths || [];
        if (paths.length === 0) return out;

        try {
            const svgs = document.querySelectorAll(
                'svg, svg *'
            );

            for (const el of svgs) {
                const hay = norm(
                    (el.outerHTML || '') + ' ' +
                    (el.getAttribute('aria-label') || '')
                );

                const match = paths.some(
                    (p) => hay.includes(norm(p))
                );

                if (match) {
                    const parent = el.closest(
                        'button, [role="button"], div'
                    );
                    push(parent || el, 10);
                }
            }
        } catch (e) {}
        return out;
    }

    // ═══ STRATEGY: POSITION (Fallback) ═══
    if (strategy === 'position') {
        try {
            const els = document.querySelectorAll(
                'button, [role="button"], ' +
                '[contenteditable="true"], ' +
                'input[type="file"], a'
            );

            for (const el of els) {
                if (matchesPositionHint(
                    { element: el },
                    target.position
                )) {
                    push(el, 0);
                }
            }
        } catch (e) {}
        return out;
    }

    return out;
}

// ═══════════════════════════════════════════════════════
// MAIN ELEMENT FINDER
// ═══════════════════════════════════════════════════════

function findElementByTarget(name, data) {
    if (!data) data = {};

    const target = FB_TARGETS[name];
    if (!target) {
        return {
            found: false,
            error: 'Unknown target: ' + name,
            ...context()
        };
    }

    const map = new Map();

    // Run all strategies in priority order
    for (const strategy of target.priority || []) {
        const results = runStrategy(
            strategy, target, data
        );

        for (const c of results) {
            const old = map.get(c.element);
            if (!old ||
                c.textMatchScore > old.textMatchScore) {
                map.set(c.element, c);
            }
        }
    }

    const candidates = [...map.values()];

    // Score each candidate
    for (const c of candidates) {
        let score = 0;

        if (isVisible(c.element)) score += 30;
        if (!isDisabled(c.element)) score += 20;
        if (matchesPositionHint(c, target.position))
            score += 25;

        score += c.textMatchScore;

        if (target.hasImage && hasImage(c.element))
            score += 10;

        if (target.mustBeEnabled &&
            isDisabled(c.element)) {
            score = 0;
        }

        c.score = score;
    }

    // Sort by score (highest first)
    candidates.sort((a, b) => b.score - a.score);

    const best = candidates[0];
    if (!best || best.score <= 50) {
        return {
            found: false,
            candidates: candidates.length,
            ...context()
        };
    }

        // Return best match with coordinates
    const p = getElementCenter(best.element);

    // 🔴 FIX: Validate coordinates to prevent (0,0) clicks
    if (p.x === 0 && p.y === 0) {
        return {
            found: false,
            error: 'Element found but coordinates are 0,0',
            candidates: candidates.length,
            ...context()
        };
    }

    return {
        found: true,
        x: p.x,
        y: p.y,
        width: p.width,
        height: p.height,
        text: (best.element.innerText || '').trim().slice(0, 100),
        ariaLabel: best.element.getAttribute('aria-label') || '',
        tag: best.element.tagName,
        score: best.score,
        strategy: best.strategy,
        confidence: Math.min(100, best.score),
        ...context()
    };
}

// ═══════════════════════════════════════════════════════
// DETECT COMPOSER STEP (Create/Edit/Share)
// ═══════════════════════════════════════════════════════
// For reels multi-step composer

function detectComposerStep() {
    try {
        const bodyText = norm(document.body.innerText);
        const url = location.href;

        if (!url.includes('/composer')) {
            return 'not_composer';
        }

        // Share step indicators
        if (bodyText.includes('add a poll') ||
            bodyText.includes('closed captions') ||
            bodyText.includes('remixing and use') ||
            bodyText.includes('privacy settings') ||
            bodyText.includes('share to')) {
            return 'share';
        }

        // Edit step indicators
        if (bodyText.includes('original audio volume') ||
            bodyText.includes('add audio') ||
            bodyText.includes('trim video') ||
            bodyText.includes('safe to publish')) {
            return 'edit';
        }

        // Publishing state
        if (bodyText.includes('publishing your post') ||
            bodyText.includes('this may take a moment')) {
            return 'publishing';
        }

        // Default: Create step
        return 'create';
    } catch (e) {
        return 'unknown';
    }
}

// ═══════════════════════════════════════════════════════
// SCREEN DETECTION
// ═══════════════════════════════════════════════════════

function detectCurrentScreen() {
    let bodyText = '';
    let url = '';

    try {
        bodyText = norm(document.body.innerText);
        url = location.href;
    } catch (e) {
        return 'unknown';
    }

    // ═══ POPUPS (HIGHEST PRIORITY) ═══

    // Publishing overlay
    if (bodyText.includes('publishing your post') ||
        bodyText.includes('this may take a moment')) {
        return 'publishing';
    }

    // Boost popup (after publish)
    if (bodyText.includes('boost your post') ||
        bodyText.includes('boost this post') ||
        bodyText.includes('post has been published')) {
        return 'boost_popup';
    }

    // Switched to page popup
    if (bodyText.includes("you're now acting as") ||
        (bodyText.includes('switched to') &&
         bodyText.includes('see page'))) {
        return 'switched_popup';
    }

    // ═══ BUSINESS SUITE ═══

    if (url.includes('business.facebook.com')) {

        // Composer screens (detailed step detection)
        if (url.includes('/composer')) {
            const step = detectComposerStep();

            if (step === 'publishing') {
                return 'publishing';
            }

            // Reel-specific screens
            if (bodyText.includes('create reel') ||
                url.includes('/reel')) {
                if (step === 'share') {
                    return 'composer_reel_share';
                }
                if (step === 'edit') {
                    return 'composer_reel_edit';
                }
                return 'composer_reel_create';
            }

            // Story
            if (url.includes('/story')) {
                return 'composer_story';
            }

            // Regular post composer
            if (step === 'share') {
                return 'composer_share';
            }
            if (step === 'edit') {
                return 'composer_edit';
            }
            return 'composer_create';
        }

        // Business Suite pages
        if (url.includes('/latest/home')) {
            return 'business_home';
        }
        if (url.includes('/latest/inbox')) {
            return 'business_inbox';
        }
        if (url.includes('/latest/notifications')) {
            return 'business_notifications';
        }
        if (url.includes('/latest/posts')) {
            return 'business_posts';
        }
        if (url.includes('/latest/planner') ||
            url.includes('/planner')) {
            return 'business_planner';
        }
        if (url.includes('/latest/insights') ||
            url.includes('/insights')) {
            return 'business_insights';
        }
        if (url.includes('/latest/ads') ||
            url.includes('/ads')) {
            return 'business_ads';
        }
        if (url.includes('/latest/content')) {
            return 'business_content';
        }
        if (url.includes('/monetization')) {
            return 'business_monetization';
        }
        if (url.includes('/settings')) {
            return 'business_settings';
        }
        if (url.includes('/latest/audience')) {
            return 'business_audience';
        }
        if (url.includes('/latest/comments')) {
            return 'business_comments';
        }

        return 'business_suite';
    }

    // ═══ FACEBOOK MAIN ═══

    if (url.includes('facebook.com')) {

        // Login/Auth (HIGH PRIORITY)
        if (url.includes('/login') ||
            url.includes('/checkpoint')) {
            return 'login';
        }

        // Content types
        if (url.includes('/reel/') ||
            url.includes('/reels/')) {
            return 'reel';
        }
        if (url.includes('/watch') ||
            url.includes('/videos/')) {
            return 'watch';
        }
        if (url.includes('/marketplace')) {
            return 'marketplace';
        }
        if (url.includes('/gaming')) {
            return 'gaming';
        }

        // Communication
        if (url.includes('/messages')) {
            return 'messages';
        }
        if (url.includes('/notifications')) {
            return 'notifications';
        }

        // Groups & Pages
        if (url.includes('/groups/')) {
            return 'group';
        }
        if (url.includes('/groups')) {
            return 'groups';
        }
        if (url.includes('/pages/')) {
            return 'page';
        }

        // Profile pages
        if (url.includes('/profile.php') ||
            url.includes('/me')) {
            return 'profile';
        }

        // Events
        if (url.includes('/events')) {
            return 'events';
        }

        // Settings
        if (url.includes('/settings')) {
            return 'settings';
        }

        // Search
        if (url.includes('/search')) {
            return 'search';
        }

        // Story
        if (url.includes('/stories/')) {
            return 'story';
        }

        // Live
        if (url.includes('/live')) {
            return 'live';
        }

        // Ads Center
        if (url.includes('/ads')) {
            return 'ads_center';
        }

        // Page profile detection (facebook.com/{pagename})
        // Check if URL has a path (not just facebook.com)
        // and page-specific sidebar is visible
        try {
            const path = location.pathname;
            if (path && path !== '/' && path.length > 1) {
                // Check for page-specific sidebar items
                if (bodyText.includes('professional dashboard') ||
                    bodyText.includes('manage page') ||
                    bodyText.includes('meta business suite') ||
                    bodyText.includes('ad centre')) {
                    return 'page_profile';
                }
            }
        } catch (e) {}

        // Home/Feed (default)
        return 'feed';
    }

    return 'unknown';
}
// ═══════════════════════════════════════════════════════
// GET ALL BUTTONS (Debug helper)
// ═══════════════════════════════════════════════════════

function getAllButtons() {
    try {
        const els = document.querySelectorAll(
            'button, [role="button"], ' +
            '[role="menuitem"], a, input, ' +
            '[contenteditable="true"]'
        );

        return [...els]
            .filter(isVisible)
            .slice(0, 500)
            .map((e) => {
                const p = getElementCenter(e);
                return {
                    text: (e.innerText || '')
                        .trim().slice(0, 100),
                    ariaLabel:
                        e.getAttribute('aria-label') || '',
                    tag: e.tagName,
                    x: p.x,
                    y: p.y,
                    width: p.width,
                    height: p.height,
                    disabled: isDisabled(e)
                };
            });
    } catch (e) {
        return [];
    }
}

// ═══════════════════════════════════════════════════════
// GET PROFILE NAME (Currently active profile)
// ═══════════════════════════════════════════════════════

function getProfileName() {
    const sources = [
        // Method 1: Profile aria-label
        () => {
            const el = document.querySelector(
                '[aria-label*="profile" i]'
            );
            return el
                ? el.getAttribute('aria-label')
                : '';
        },
        // Method 2: Account aria-label
        () => {
            const el = document.querySelector(
                '[aria-label*="account" i]'
            );
            return el
                ? el.getAttribute('aria-label')
                : '';
        },
        // Method 3: "What's on your mind, X?" placeholder
        () => {
            const el = document.querySelector(
                '[placeholder*="mind" i]'
            );
            if (el) {
                const t = el.getAttribute(
                    'placeholder'
                ) || '';
                const m = t.match(
                    /mind,\s*(.+?)\s*\?/i
                );
                if (m) return m[1];
            }
            return '';
        },
        // Method 4: Business Suite page name
        // (top-left area, usually visible)
        () => {
            const els = document.querySelectorAll(
                'div[role="button"]'
            );
            for (const el of els) {
                const r = el.getBoundingClientRect();
                // Top area, left side
                if (r.top < 100 &&
                    r.left < 300 &&
                    r.width > 100) {
                    const t = (el.innerText || '').trim();
                    if (t.length > 2 &&
                        t.length < 50 &&
                        !t.includes('\n')) {
                        return t;
                    }
                }
            }
            return '';
        }
    ];

    for (const fn of sources) {
        try {
            const name = fn();
            if (name && name.length > 2) {
                return name.trim();
            }
        } catch (e) {}
    }

    return '';
}

// ═══════════════════════════════════════════════════════
// PAGE INFO
// ═══════════════════════════════════════════════════════

function pageInfo() {
    return {
        url: location.href,
        title: document.title,
        profile_name: getProfileName(),
        screen: detectCurrentScreen(),
        composer_step: detectComposerStep(),
        ...context()
    };
}

// ═══════════════════════════════════════════════════════
// CLICK ELEMENT (READ-ONLY - Returns coordinates)
// ═══════════════════════════════════════════════════════
// NOTE: Does NOT actually click. Returns coords for
// Python Win32 mouse to perform real click.

function clickElement(targetName, data) {
    const result = findElementByTarget(
        targetName, data
    );
    return {
        ...result,
        clicked: false,
        note: 'Coordinates returned for Win32 click'
    };
}

// ═══════════════════════════════════════════════════════
// CHECK ELEMENT STATE
// ═══════════════════════════════════════════════════════

function checkElementState(targetName, data) {
    const found = findElementByTarget(targetName, data);

    if (!found.found) {
        return {
            found: false,
            enabled: false,
            visible: false,
            ...context()
        };
    }

    let el = null;
    try {
        el = document.elementFromPoint(
            found.x, found.y
        );
    } catch (e) {}

    return {
        found: true,
        enabled: el ? !isDisabled(el) : true,
        visible: true,
        x: found.x,
        y: found.y,
        text: found.text,
        ariaLabel: found.ariaLabel,
        ...context()
    };
}

// ═══════════════════════════════════════════════════════
// WAIT FOR ELEMENT (Non-blocking check)
// ═══════════════════════════════════════════════════════

function waitForElementCheck(targetName, data) {
    const result = findElementByTarget(targetName, data);
    return {
        ready: result.found,
        ...result
    };
}

// ═══════════════════════════════════════════════════════
// MESSAGE HANDLER (Chrome Runtime API)
// ═══════════════════════════════════════════════════════

try {
    chrome.runtime.onMessage.addListener(
        (msg, sender, reply) => {
            try {
                let result;

                switch (msg.command) {

                    case 'find_element':
                        result = findElementByTarget(
                            msg.target, msg.data || {}
                        );
                        break;

                    case 'click_element':
                        result = clickElement(
                            msg.target, msg.data || {}
                        );
                        break;

                    case 'check_element_state':
                        result = checkElementState(
                            msg.target, msg.data || {}
                        );
                        break;

                    case 'wait_for_element':
                        result = waitForElementCheck(
                            msg.target, msg.data || {}
                        );
                        break;

                    case 'get_screen':
                        result = {
                            screen: detectCurrentScreen(),
                            composer_step:
                                detectComposerStep(),
                            ...context()
                        };
                        break;

                    case 'get_composer_step':
                        result = {
                            step: detectComposerStep(),
                            screen: detectCurrentScreen(),
                            ...context()
                        };
                        break;

                    case 'get_upload_progress':
                        result = {
                            ...getUploadProgress(),
                            complete: isUploadComplete(),
                            ...context()
                        };
                        break;

                    case 'is_upload_complete':
                        result = {
                            complete: isUploadComplete(),
                            ...context()
                        };
                        break;

                    case 'get_all_buttons':
                        result = {
                            buttons: getAllButtons(),
                            ...context()
                        };
                        break;

                    case 'get_page_info':
                        result = pageInfo();
                        break;

                    case 'ping':
                        result = {
                            pong: true,
                            version: '3.0',
                            ...context()
                        };
                        break;

                    default:
                        result = {
                            error: 'Unknown command: ' +
                                msg.command
                        };
                }

                reply(result);
            } catch (e) {
                reply({
                    error: e.message,
                    ...context()
                });
            }

            return true;
        }
    );
} catch (e) {}

// ═══════════════════════════════════════════════════════
// DOM CHANGE MONITOR (STEALTH MODE)
// ═══════════════════════════════════════════════════════
// - Throttled (min 5 sec between messages)
// - Random jitter added
// - Silent errors
// - Passive observation only

let lastSignature = '';
let lastSentTime = 0;
let observerActive = true;

// Random throttle base (5-8 seconds)
const THROTTLE_MIN = 5000;
const THROTTLE_JITTER = 3000;

function getRandomThrottle() {
    return THROTTLE_MIN +
        Math.floor(Math.random() * THROTTLE_JITTER);
}

let currentThrottle = getRandomThrottle();

try {
    const domObserver = new MutationObserver(() => {
        if (!observerActive) return;

        const now = Date.now();
        if (now - lastSentTime < currentThrottle) return;

        try {
            const screen = detectCurrentScreen();

            let dialogs = 0;
            try {
                dialogs = document.querySelectorAll(
                    '[role="dialog"]'
                ).length;
            } catch (e) {}

            const sig = screen + '|' + dialogs;

            if (sig !== lastSignature) {
                lastSignature = sig;
                lastSentTime = now;
                currentThrottle = getRandomThrottle();

                try {
                    chrome.runtime.sendMessage({
                        type: 'dom_change',
                        data: {
                            type: 'screen_or_popup_change',
                            screen: screen,
                            details: {
                                dialogs: dialogs
                            },
                            ...context()
                        }
                    }).catch(() => {});
                } catch (e) {}
            }
        } catch (e) {}
    });

    // Observe only high-level changes
    domObserver.observe(document.body, {
        childList: true,
        subtree: false,
        attributes: false,
        characterData: false
    });
} catch (e) {}

// ═══════════════════════════════════════════════════════
// VISIBILITY CHANGE HANDLER
// ═══════════════════════════════════════════════════════
// Pause observer when tab is hidden (saves resources)

try {
    document.addEventListener('visibilitychange', () => {
        try {
            if (document.hidden) {
                observerActive = false;
            } else {
                observerActive = true;
                lastSentTime = 0;
            }
        } catch (e) {}
    });
} catch (e) {}

// ═══════════════════════════════════════════════════════
// INITIALIZATION
// ═══════════════════════════════════════════════════════

log('FB Scanner V3.0 ready');

})();