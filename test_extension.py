"""
Test Extension Connection
Run this to check if Chrome extension connects
"""

import sys
import time
import os

# Add parent folder to path
sys.path.insert(
    0,
    os.path.dirname(
        os.path.dirname(os.path.abspath(__file__))
    )
)

from fb_helper import websocket_server as ws
from fb_helper.element_bridge import ElementBridge


def main():
    print("=" * 50)
    print("EXTENSION CONNECTION TEST")
    print("=" * 50)

    # Start WebSocket server
    print("\n[1] Starting WebSocket server...")
    bridge = ElementBridge()
    bridge.start(port=8765)

    # Wait for extension
    print("\n[2] Waiting for extension to connect...")
    print("    → Open Facebook.com in Chrome")
    print("    → Extension should connect automatically")
    print("    → Waiting up to 30 seconds...\n")

    if bridge.wait_for_extension(timeout=30):
        print("✅ Extension CONNECTED!\n")
    else:
        print("❌ Extension did not connect")
        print("\nTroubleshooting:")
        print("1. Chrome me extension load hai?")
        print("2. Facebook.com open hai?")
        print("3. Extension popup mein green dot dikh raha?")
        return

    # Test 1: Ping
    print("[3] Testing PING...")
    if bridge.ping():
        print("    ✅ Ping successful!")
    else:
        print("    ❌ Ping failed")

    time.sleep(1)

    # Test 2: Get screen
    print("\n[4] Getting current screen...")
    screen = bridge.get_screen()
    print(f"    Current screen: {screen}")

    time.sleep(1)

    # Test 3: Page info
    print("\n[5] Getting page info...")
    info = bridge.get_page_info()
    print(f"    URL     : {info.get('url', '?')[:60]}")
    print(f"    Title   : {info.get('title', '?')[:60]}")
    print(f"    Screen  : {info.get('screen', '?')}")
    print(f"    Profile : {info.get('profile_name', '?')}")

    time.sleep(1)

    # Test 4: All buttons
    print("\n[6] Getting all buttons...")
    buttons = bridge.get_all_buttons()
    print(f"    Found {len(buttons)} interactive elements")
    print("\n    First 10 buttons:")
    for i, btn in enumerate(buttons[:10], 1):
        text = btn.get('text', '')[:40] or btn.get(
            'ariaLabel', ''
        )[:40]
        x = int(btn.get('x', 0))
        y = int(btn.get('y', 0))
        print(f"    {i}. [{text}] @ ({x}, {y})")

    time.sleep(1)

    # Test 5: Find Create Post
    print("\n[7] Finding 'Create Post' button...")
    result = bridge.find_element(
        'create_post', timeout=5
    )
    if result.get('found'):
        print("    ✅ Found!")
        print(f"    Position: ({int(result['x'])}, "
              f"{int(result['y'])})")
        print(f"    Text    : {result.get('text', '?')}")
        print(f"    Score   : {result.get('score', 0)}")
        print(f"    Source  : {result.get('source', '?')}")
    else:
        print("    ⚠️ Not found (may not be on this page)")

    # Test 6: Find Share button
    print("\n[8] Finding 'Share' button...")
    result = bridge.find_element(
        'share_button', timeout=5
    )
    if result.get('found'):
        print("    ✅ Found!")
        print(f"    Position: ({int(result['x'])}, "
              f"{int(result['y'])})")
    else:
        print("    ⚠️ Not found (may not be on composer)")

    print("\n" + "=" * 50)
    print("TEST COMPLETE!")
    print("=" * 50)
    print("\nPress Ctrl+C to exit...")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\nStopping...")
        bridge.stop()


if __name__ == "__main__":
    main()