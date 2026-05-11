"""
HeyGen Simple Video Generator - Complete Fixed Flow
Uses correct Radix UI selectors for Avatar IV dropdown and Avatar III selection.
All original functionality preserved + fixes applied.
"""

import asyncio
import os
import random
import sys
from datetime import datetime
from playwright.async_api import async_playwright

AUTH_FILE = "heygen_session.json"

# Global flag — jab True ho to dialog monitor kuch nahi karega
dialog_monitor_active = True


async def pick_first_visible(page, selectors, timeout=5000):
    for selector in selectors:
        try:
            locator = page.locator(selector).first
            await locator.wait_for(state="visible", timeout=timeout)
            return locator
        except Exception:
            continue
    return None


async def dismiss_optional_popups(page):
    popup_candidates = [
        'button[aria-label*="close" i]',
        'button[title*="close" i]',
        'button:has-text("Close")',
        'button:has-text("No thanks")',
        'button:has-text("Maybe later")',
        'button:has-text("Not now")',
        '[role="button"]:has-text("Close")',
        '[class*="close"]',
    ]
    try:
        for attempt in range(3):
            popup_closed = False
            for selector in popup_candidates:
                locator = page.locator(selector)
                count = await locator.count()
                if count > 0:
                    for i in range(min(count, 10)):
                        item = locator.nth(i)
                        try:
                            if await item.is_visible(timeout=500):
                                await item.click(force=True)
                                await page.wait_for_timeout(600)
                                print(f"[✓] Popup closed via {selector}")
                                popup_closed = True
                                return True
                        except Exception:
                            continue
            if popup_closed:
                return True

        for _ in range(3):
            await page.keyboard.press("Escape")
            await page.wait_for_timeout(500)
        print("[✓] Popup dismissed with Escape")
        return True
    except Exception as e:
        print(f"[!] Popup dismiss attempt failed: {e}")
        return False


async def monitor_and_close_dialogs(page):
    """Monitor for dialogs and close them automatically in the background."""
    print("[>] Starting dialog monitor - checking for popups...")

    async def close_dialogs_loop():
        global dialog_monitor_active
        while True:
            try:
                if not dialog_monitor_active:
                    await page.wait_for_timeout(1000)
                    continue

                dialog_locator = page.locator('[role="dialog"]')
                dialog_count = await dialog_locator.count()

                if dialog_count > 0:
                    for i in range(dialog_count):
                        dialog = dialog_locator.nth(i)
                        # Skip and DISABLE monitor if download popup appears
                        try:
                            dialog_text = await dialog.inner_text()
                            if "Download" in dialog_text or "Connect to Google Drive" in dialog_text:
                                print("[>] Download dialog detected — disabling monitor!")
                                dialog_monitor_active = False
                                continue
                        except Exception:
                            pass
                        close_button = dialog.locator(
                            'button[type="button"].tw-absolute.tw-right-4.tw-top-4'
                        ).first
                        try:
                            if await close_button.is_visible(timeout=1000):
                                await close_button.click(force=True)
                                await page.wait_for_timeout(800)
                                print("[✓] Dialog closed!")
                        except Exception:
                            try:
                                close_btn_alt = dialog.locator('button:has(svg)').first
                                if await close_btn_alt.is_visible(timeout=500):
                                    await close_btn_alt.click(force=True)
                                    await page.wait_for_timeout(800)
                                    print("[✓] Dialog closed via alternative selector!")
                            except Exception as e:
                                print(f"[!] Could not close dialog: {e}")

                await page.wait_for_timeout(1000)
            except Exception as e:
                # Gracefully exit if browser/page is closed
                if "Target" in str(e) and "closed" in str(e):
                    return
                print(f"[!] Error in dialog monitor: {e}")
                try:
                    await page.wait_for_timeout(1000)
                except Exception:
                    return  # Browser closed, exit monitor

    asyncio.create_task(close_dialogs_loop())


async def click_avatar_iv_dropdown(page):
    print("[>] Clicking 'Avatar IV' dropdown in bottom toolbar...")

    for sel in [
        '[aria-haspopup="menu"]:has-text("Avatar IV")',
        '[aria-haspopup="menu"]:has-text("Avatar V")',
        '[aria-haspopup="menu"]:has-text("Avatar")',
        'div[data-state="closed"]:has-text("Avatar IV")',
        'div[data-state]:has-text("Avatar IV")',
    ]:
        try:
            loc = page.locator(sel).first
            if await loc.is_visible(timeout=2000):
                await loc.click(force=True)
                await page.wait_for_timeout(1200)
                print(f"[✓] Avatar IV dropdown opened via Playwright: {sel}")
                return
        except Exception:
            continue

    result = await page.evaluate("""
        () => {
            const triggers = Array.from(document.querySelectorAll('[aria-haspopup="menu"]'));
            for (let el of triggers) {
                const text = (el.textContent || '').trim();
                if (text.includes('Avatar')) {
                    el.click();
                    return 'Clicked radix trigger: "' + text.substring(0, 50) + '"';
                }
            }
            const labels = Array.from(document.querySelectorAll('div'));
            for (let el of labels) {
                const cls = el.className || '';
                const text = (el.textContent || '').trim();
                if (cls.includes('tw-h-9') && cls.includes('tw-cursor-pointer') && text.includes('Avatar')) {
                    el.click();
                    return 'Clicked inner label div: "' + text.substring(0, 50) + '"';
                }
            }
            return 'Avatar IV trigger not found';
        }
    """)
    print(f"[>] JS result: {result}")
    await page.wait_for_timeout(1200)


async def select_avatar_iii(page):
    print("[>] Waiting for Radix menu to open...")
    await page.wait_for_timeout(800)

    for sel in [
        '[role="menuitem"]:has-text("Avatar III")',
        '[role="option"]:has-text("Avatar III")',
        '[data-radix-collection-item]:has-text("Avatar III")',
        'div[role="menuitem"]:has-text("Avatar III")',
    ]:
        try:
            loc = page.locator(sel).first
            if await loc.is_visible(timeout=2000):
                await loc.click(force=True)
                await page.wait_for_timeout(1000)
                print(f"[✓] Avatar III selected via: {sel}")
                return True
        except Exception:
            continue

    result = await page.evaluate("""
        () => {
            const candidates = Array.from(document.querySelectorAll(
                '[role="menuitem"], [role="option"], [data-radix-collection-item]'
            ));
            const visible = candidates.filter(el => el.offsetParent !== null);
            const labels = visible.map(el => el.textContent.trim());
            for (let item of visible) {
                const text = (item.textContent || '').trim();
                if (text.includes('Avatar III') || text === 'Avatar 3') {
                    item.click();
                    return 'Clicked menuitem: "' + text + '"';
                }
            }
            const walker = document.createTreeWalker(
                document.body, NodeFilter.SHOW_TEXT, null, false
            );
            let node;
            while ((node = walker.nextNode())) {
                if (node.textContent.trim() === 'Avatar III') {
                    const el = node.parentElement;
                    const target = el.closest('[role="menuitem"]') ||
                                   el.closest('[role="option"]') ||
                                   el.closest('li') || el;
                    if (target.offsetParent !== null) {
                        target.click();
                        return 'Clicked via text node: "Avatar III"';
                    }
                }
            }
            return 'Avatar III not found. Menu items: [' + labels.join(' | ') + ']';
        }
    """)
    print(f"[>] JS Avatar III result: {result}")
    await page.wait_for_timeout(1000)

    if "not found" in result.lower():
        await page.screenshot(path="debug_dropdown.png")
        print("[!] debug_dropdown.png saved")
        return False
    return True


async def click_generate_button(page):
    print("[>] Looking for Generate button...")

    result = await page.evaluate("""
        () => {
            const allBtns = Array.from(document.querySelectorAll('button'));
            const aiBtn = allBtns.find(btn => (btn.textContent || '').trim().includes('Open in AI Studio'));
            if (aiBtn) {
                let sibling = aiBtn.nextElementSibling;
                while (sibling) {
                    if (sibling.tagName === 'BUTTON') {
                        sibling.click();
                        return 'Clicked button after "Open in AI Studio"';
                    }
                    sibling = sibling.nextElementSibling;
                }
                const parent = aiBtn.parentElement;
                if (parent) {
                    const children = Array.from(parent.querySelectorAll('button'));
                    const idx = children.indexOf(aiBtn);
                    if (idx >= 0 && children[idx + 1]) {
                        children[idx + 1].click();
                        return 'Clicked sibling button in parent';
                    }
                }
            }
            const bottomBtns = allBtns.filter(btn => {
                const rect = btn.getBoundingClientRect();
                return rect.top > window.innerHeight * 0.75 && rect.width > 0 && btn.offsetParent !== null;
            });
            if (bottomBtns.length > 0) {
                bottomBtns[bottomBtns.length - 1].click();
                return 'Clicked last bottom button';
            }
            return 'Generate button not found';
        }
    """)
    print(f"[>] Generate JS result: {result}")
    await page.wait_for_timeout(2000)

    for sel in [
        'button[aria-label*="generate" i]',
        'button[aria-label*="submit" i]',
        'button[title*="generate" i]',
        'button[class*="tw-bg-primary"]',
    ]:
        try:
            loc = page.locator(sel).first
            if await loc.is_visible(timeout=1500):
                await loc.click(force=True)
                await page.wait_for_timeout(2000)
                print(f"[✓] Generate button clicked via: {sel}")
                return True
        except Exception:
            continue

    if "not found" not in result.lower():
        print("[✓] Generate button clicked!")
        return True

    print("[!] Generate button not found — trying Ctrl+Enter...")
    await page.keyboard.press("Control+Return")
    await page.wait_for_timeout(2000)
    return False


async def wait_and_download_latest_video(page, custom_filename=None):
    print("\n[>] === STEP: Monitoring Video Generation ===")
    print("[>] Waiting 10 seconds for video to appear in RECENTS...")
    await page.wait_for_timeout(10000)

    # ── STEP 1: Poll until % disappears ──────────────────────────────
    print("[>] Monitoring progress... This may take several minutes.")
    for i in range(120):  # up to 10 minutes
        state_info = await page.evaluate('''() => {
            const recentsDivs = Array.from(document.querySelectorAll('div, a, li')).filter(el => {
                const text = el.innerText || '';
                return text.includes('Avatar Video') && el.getBoundingClientRect().width > 0 && el.children.length > 0;
            });
            if (recentsDivs.length === 0) return { status: 'not_found', text: '' };
            recentsDivs.sort((a, b) => (a.innerText.length) - (b.innerText.length));
            const target = recentsDivs[0];
            const text = target.innerText || '';
            if (text.includes('%')) return { status: 'generating', text: text.replace(/\\n/g, ' ') };
            else return { status: 'completed', text: text.replace(/\\n/g, ' ') };
        }''')

        status = state_info.get("status")
        text = state_info.get("text", "")

        if status == 'generating':
            print(f"\r[*] Generating: {text.strip()}", end="", flush=True)
            await page.wait_for_timeout(5000)
        elif status == 'completed':
            print(f"\n[✓] Generation Completed! {text.strip()}")
            break
        else:
            print(f"\r[*] Waiting... {text.strip()}", end="", flush=True)
            await page.wait_for_timeout(5000)

    await page.wait_for_timeout(1000)

    # ── STEP 2: Hover over the first completed "Avatar Video" in RECENTS ──
    print("\n[>] === STEP: Hovering over completed video ===")

    # Find the first Avatar Video item that has NO percentage (completed)
    # and hover it to reveal the 3-dots button
    hovered = await page.evaluate('''() => {
        const allEls = Array.from(document.querySelectorAll('div, a, li'));
        const candidates = allEls.filter(el => {
            const text = el.innerText || '';
            return text.includes('Avatar Video') &&
                   (text.includes('ago') || text.includes('just now')) &&
                   !text.includes('%') &&
                   el.getBoundingClientRect().width > 0 &&
                   el.children.length > 0;
        });
        if (candidates.length === 0) return false;
        candidates.sort((a, b) => a.innerText.length - b.innerText.length);
        const target = candidates[0];
        target.dispatchEvent(new MouseEvent('mouseenter', { bubbles: true }));
        target.dispatchEvent(new MouseEvent('mouseover', { bubbles: true }));
        return true;
    }''')
    print(f"[>] Hover via JS: {hovered}")

    # Also hover via Playwright for real CSS :hover state
    try:
        video_loc = page.locator('text="Avatar Video"').first
        await video_loc.hover(force=True)
        await page.wait_for_timeout(1000)
        print("[✓] Hovered via Playwright!")
    except Exception as e:
        print(f"[!] Playwright hover: {e}")

    await page.wait_for_timeout(1500)

    # ── STEP 3: Click the 3-dots button ──────────────────────────────
    # From the HTML: button with classes tw-h-[24px] tw-w-[24px] !tw-border-transparent
    print("[>] Looking for 3-dots button...")

    dots_clicked = False

    # Strategy 1: Playwright — exact class match from the HTML you provided
    for sel in [
        'button.tw-h-\\[24px\\].tw-w-\\[24px\\]',
        'button[class*="tw-h-[24px]"][class*="tw-w-[24px]"]',
        'button[class*="!tw-border-transparent"]',
        'button[class*="tw-h-\\[24px\\]"]',
    ]:
        try:
            loc = page.locator(sel).first
            if await loc.is_visible(timeout=1500):
                await loc.click(force=True)
                await page.wait_for_timeout(800)
                print(f"[✓] 3-dots clicked via: {sel}")
                dots_clicked = True
                break
        except Exception:
            continue

    # Strategy 2: JS — find the 24x24 button near the Avatar Video item
    if not dots_clicked:
        dots_clicked = await page.evaluate('''() => {
            // Find all buttons that are 24x24 size (the 3-dots button)
            const allBtns = Array.from(document.querySelectorAll('button'));
            const smallBtns = allBtns.filter(btn => {
                const cls = btn.className || '';
                const rect = btn.getBoundingClientRect();
                return (
                    cls.includes('tw-h-[24px]') ||
                    cls.includes('!tw-border-transparent') ||
                    (Math.round(rect.width) === 24 && Math.round(rect.height) === 24)
                ) && btn.offsetParent !== null;
            });

            if (smallBtns.length === 0) return false;

            // Click the first visible one
            smallBtns[0].click();
            return true;
        }''')
        if dots_clicked:
            print("[✓] 3-dots clicked via JS (24x24 size match)!")

    # Strategy 3: JS — hover the container and click whatever button appears
    if not dots_clicked:
        dots_clicked = await page.evaluate('''() => {
            const allEls = Array.from(document.querySelectorAll('div, li'));
            const containers = allEls.filter(el => {
                const text = el.innerText || '';
                return text.includes('Avatar Video') &&
                       (text.includes('ago') || text.includes('just now')) &&
                       el.getBoundingClientRect().width > 0;
            });
            if (containers.length === 0) return false;
            containers.sort((a, b) => a.innerText.length - b.innerText.length);
            const container = containers[0];

            // Trigger hover
            container.dispatchEvent(new MouseEvent('mouseenter', { bubbles: true }));
            container.dispatchEvent(new MouseEvent('mouseover', { bubbles: true }));

            // Find any button inside this container
            const btns = Array.from(container.querySelectorAll('button'));
            if (btns.length > 0) {
                btns[btns.length - 1].click();  // last button = 3 dots
                return true;
            }
            return false;
        }''')
        if dots_clicked:
            print("[✓] 3-dots clicked via container hover+click JS!")

    if not dots_clicked:
        print("[!] Could not click 3-dots. Taking screenshot...")
        await page.screenshot(path="debug_3dots.png")
        return

    # ── STEP 4: Wait for context menu → click Download ───────────────
    # Disable dialog monitor so it does not interfere with download popup
    global dialog_monitor_active
    dialog_monitor_active = False
    print("[>] Dialog monitor disabled for download")
    print("[>] Waiting for context menu...")
    await page.wait_for_timeout(1500)

    download_clicked = False
    downloaded_path = None

    for sel in [
        '[role="menuitem"]:has-text("Download")',
        '[role="option"]:has-text("Download")',
        'div[class*="tw-cursor-pointer"]:has-text("Download")',
        'button:has-text("Download")',
    ]:
        try:
            loc = page.locator(sel).first
            if await loc.is_visible(timeout=2000):
                os.makedirs("heygen_downloads", exist_ok=True)
                async with page.expect_download(timeout=60000) as download_info:
                    await loc.click(force=True)
                download = await download_info.value
                # Use custom filename if provided, else suggested
                filename = custom_filename if custom_filename else download.suggested_filename
                save_path = os.path.join("heygen_downloads", filename)
                await download.save_as(save_path)
                print(f"[✓] Downloaded! Saved to: {save_path}")
                download_clicked = True
                downloaded_path = save_path
                break
        except Exception as e:
            print(f"[!] Download attempt via {sel}: {e}")
            continue

    if not download_clicked:
        # JS fallback — click Download text
        result = await page.evaluate('''() => {
            const items = Array.from(document.querySelectorAll(
                '[role="menuitem"], [role="option"], div, button'
            )).filter(el => {
                const t = (el.innerText || '').trim();
                return t === 'Download' && el.offsetParent !== null;
            });
            if (items.length > 0) {
                items[0].click();
                return true;
            }
            return false;
        }''')
        if result:
            print("[✓] Download clicked via JS! File saved to default downloads folder.")
        else:
            print("[✗] Could not find Download option.")
            await page.screenshot(path="debug_download_menu.png")

    return downloaded_path if download_clicked else None


async def main(news_script=None):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        
        context_options = {"accept_downloads": True}
        if os.path.exists(AUTH_FILE):
            context_options["storage_state"] = AUTH_FILE
            
        context = await browser.new_context(**context_options)
        page = await context.new_page()
        downloaded_file = None

        print("[>] Opening HeyGen...")
        await page.goto("https://app.heygen.com", timeout=60000)
        await page.wait_for_timeout(3000)

        # Check if login is required
        current_url = page.url.lower()
        if "login" in current_url or "sign" in current_url or "auth" in current_url:
            print("\n[!] Login required! Session expired or missing.")
            print("[!] Please log in manually in the opened browser window.")
            print("[!] The script will pause and wait until you reach the dashboard...")
            
            while True:
                curr = page.url.lower()
                if "login" not in curr and "sign" not in curr and "auth" not in curr:
                    break
                await page.wait_for_timeout(2000)
            
            print("[✓] Login detected! Waiting a few seconds for dashboard to fully load...")
            await page.wait_for_timeout(5000)
            await context.storage_state(path=AUTH_FILE)
            print(f"[✓] New session successfully saved to '{AUTH_FILE}'.")
            print("[>] Resuming automation...\n")
        else:
            # Refresh session to keep it alive
            try:
                await context.storage_state(path=AUTH_FILE)
            except Exception:
                pass

        print("[>] Looking for 'Make an avatar video from a photo'...")
        photo_option = await pick_first_visible(page, [
            'button:has-text("Make an avatar video from a photo")',
            'div:has-text("Make an avatar video from a photo")',
        ])

        if photo_option:
            print("[✓] Option found! Clicking...")
            await photo_option.click(force=True)
            await page.wait_for_timeout(3000)
            print("[✓] Clicked!")

            print("[>] Looking for 'Start Creating' button...")
            start_creating = await pick_first_visible(page, [
                'button:has-text("Start Creating")',
                'button:has-text("Start creating")',
                '[role="button"]:has-text("Start Creating")',
                '[role="button"]:has-text("Start creating")',
            ], timeout=15000)

            if start_creating:
                print("[✓] Start Creating found! Clicking...")
                await start_creating.click(force=True)
                await page.wait_for_timeout(3000)
                print("[✓] Start Creating clicked!")

                print("[>] Looking for 'Script to video' tab...")
                script_tab = await pick_first_visible(page, [
                    '[role="tab"]:has-text("Script to video")',
                    'button:has-text("Script to video")',
                    '[role="button"]:has-text("Script to video")',
                ], timeout=9000)

                if script_tab:
                    await script_tab.click(force=True)
                    await page.wait_for_timeout(2000)
                    print("[✓] Script to video tab opened!")

                    print("[>] Dismissing popup if it appears...")
                    await dismiss_optional_popups(page)
                    await page.wait_for_timeout(2000)

                    print("[>] Selecting a different avatar...")
                    avatar_button = 'button[class*="tw-flex"][class*="tw-size-6"][class*="tw-shrink-0"][class*="tw-cursor-pointer"]'
                    avatar_locator = page.locator(avatar_button).first
                    try:
                        await avatar_locator.wait_for(state="visible", timeout=5000)
                        await avatar_locator.click(force=True)
                        await page.wait_for_timeout(1500)
                        print("[✓] Avatar selected!")
                    except Exception as e:
                        print(f"[✗] Avatar click failed: {e}")

                    print("[>] Clicking the top-left button...")
                    top_button = 'button[class*="tw-absolute"][class*="tw-left-4"][class*="tw-top-4"]'
                    top_btn_locator = page.locator(top_button).first
                    try:
                        await top_btn_locator.wait_for(state="visible", timeout=5000)
                        await top_btn_locator.click(force=True)
                        await page.wait_for_timeout(1500)
                        print("[✓] Top button clicked!")
                    except Exception as e:
                        print(f"[✗] Top button click failed: {e}")

                    print("[>] Clicking the 'Change avatar' option...")
                    change_avatar = await pick_first_visible(page, [
                        'button:has-text("Change avatar")',
                        '[role="button"]:has-text("Change avatar")',
                        'text="Change avatar"',
                    ], timeout=5000)

                    if change_avatar:
                        await change_avatar.click(force=True)
                        await page.wait_for_timeout(1500)
                        print("[✓] Change avatar clicked!")

                        print("[>] Scrolling the avatar list...")
                        await page.evaluate("""
                            () => {
                                const containers = Array.from(document.querySelectorAll('div')).filter(div => {
                                    const style = window.getComputedStyle(div);
                                    return (style.overflowY === 'auto' || style.overflowY === 'scroll' ||
                                            style.overflow === 'auto' || style.overflow === 'scroll') &&
                                           div.scrollHeight > div.clientHeight;
                                });
                                if (containers.length > 0) {
                                    containers[0].scrollTop = containers[0].scrollHeight;
                                }
                            }
                        """)
                        await page.wait_for_timeout(1500)

                        print("[>] Clicking the Nicholas avatar...")
                        nicholas_div = page.locator(
                            'div[class*="tw-cursor-pointer"][class*="tw-aspect"]'
                        ).filter(has=page.locator('img[alt="Nicholas"]')).first
                        try:
                            await nicholas_div.wait_for(state="visible", timeout=5000)
                            await nicholas_div.click(force=True)
                            await page.wait_for_timeout(1500)
                            print("[✓] Nicholas clicked!")
                        except Exception as e:
                            print(f"[!] Nicholas click via filter failed: {e}")
                            await page.evaluate("""
                                () => {
                                    const nicholas = Array.from(document.querySelectorAll('img')).find(img => img.alt === 'Nicholas');
                                    if (nicholas) {
                                        const parent = nicholas.closest('div[class*="tw-cursor-pointer"]');
                                        if (parent) parent.click();
                                    }
                                }
                            """)
                            await page.wait_for_timeout(1500)
                            print("[✓] Nicholas clicked via JavaScript!")

                    # ── STEP: Pick a random look from Nicholas's looks grid ──
                    print("[>] Waiting for Nicholas looks grid to load...")
                    await page.wait_for_timeout(2000)

                    random_look_picked = False
                    try:
                        # Find all look options inside the grid
                        looks_grid = page.locator('div.tw-grid.tw-grid-cols-3')
                        await looks_grid.first.wait_for(state="visible", timeout=5000)

                        look_items = looks_grid.first.locator(
                            'div.tw-relative.tw-cursor-pointer.tw-overflow-hidden.tw-rounded-lg'
                        )
                        look_count = await look_items.count()
                        print(f"[>] Found {look_count} looks available.")

                        if look_count > 1:
                            # Pick a random index (any look, including the first)
                            rand_idx = random.randint(0, look_count - 1)
                            print(f"[>] Randomly selecting look #{rand_idx + 1} out of {look_count}...")
                            chosen_look = look_items.nth(rand_idx)
                            await chosen_look.click(force=True)
                            await page.wait_for_timeout(1500)
                            print(f"[✓] Look #{rand_idx + 1} clicked!")
                            random_look_picked = True
                        elif look_count == 1:
                            await look_items.first.click(force=True)
                            await page.wait_for_timeout(1500)
                            print("[✓] Only 1 look available, selected it.")
                            random_look_picked = True
                    except Exception as e:
                        print(f"[!] Could not pick random look via Playwright: {e}")

                    # JS fallback for random look selection
                    if not random_look_picked:
                        try:
                            result = await page.evaluate('''
                                () => {
                                    const grid = document.querySelector('.tw-grid.tw-grid-cols-3');
                                    if (!grid) return 'Grid not found';
                                    const items = Array.from(grid.querySelectorAll(
                                        'div.tw-relative.tw-cursor-pointer.tw-overflow-hidden.tw-rounded-lg'
                                    )).filter(el => el.offsetParent !== null);
                                    if (items.length === 0) return 'No look items found';
                                    const idx = Math.floor(Math.random() * items.length);
                                    items[idx].click();
                                    return 'Clicked look #' + (idx + 1) + ' of ' + items.length;
                                }
                            ''')
                            print(f"[>] JS random look result: {result}")
                            if 'Clicked' in result:
                                random_look_picked = True
                            await page.wait_for_timeout(1500)
                        except Exception as e:
                            print(f"[!] JS fallback also failed: {e}")

                    # Click "Change look" button to confirm selection
                    if random_look_picked:
                        print("[>] Clicking 'Change look' button...")
                        change_look_clicked = False
                        for sel in [
                            'div[role="button"]:has-text("Change look")',
                            '[role="button"]:has-text("Change look")',
                            'button:has-text("Change look")',
                            'span:has-text("Change look")',
                        ]:
                            try:
                                loc = page.locator(sel).first
                                if await loc.is_visible(timeout=3000):
                                    await loc.click(force=True)
                                    await page.wait_for_timeout(2000)
                                    print("[✓] 'Change look' clicked!")
                                    change_look_clicked = True
                                    break
                            except Exception:
                                continue

                        if not change_look_clicked:
                            # JS fallback for Change look button
                            result = await page.evaluate('''
                                () => {
                                    const els = Array.from(document.querySelectorAll(
                                        'div[role="button"], button, span'
                                    )).filter(el => {
                                        const t = (el.innerText || '').trim();
                                        return t === 'Change look' && el.offsetParent !== null;
                                    });
                                    if (els.length > 0) {
                                        els[0].click();
                                        return true;
                                    }
                                    return false;
                                }
                            ''')
                            if result:
                                print("[✓] 'Change look' clicked via JS!")
                            else:
                                print("[!] Could not find 'Change look' button.")
                                await page.screenshot(path="debug_change_look.png")
                            await page.wait_for_timeout(2000)

                    # Dialog monitor will handle any popups automatically
                    await page.wait_for_timeout(2000)

                    print("[>] Entering the news script into the script box...")
                    script_box = await pick_first_visible(page, [
                        'div[contenteditable="true"]',
                        'textarea[placeholder*="script" i]',
                        'textarea[placeholder*="Script" i]',
                        'div[placeholder*="Type or paste" i]',
                        '[class*="editor"] div[contenteditable]',
                    ], timeout=5000)

                    if script_box:
                        await script_box.click(force=True)
                        await page.wait_for_timeout(500)
                        tag = await script_box.evaluate("el => el.tagName.toLowerCase()")
                        # Use provided news_script or fallback to default
                        script_text = news_script if news_script else (
                            "Breaking news today: Markets are showing strong growth signals. "
                            "Analysts expect continued momentum in the coming weeks. "
                            "Investors remain cautiously optimistic as economic indicators point upward."
                        )
                        if tag == "textarea":
                            await script_box.fill(script_text)
                        else:
                            await page.keyboard.press("Control+a")
                            await script_box.type(script_text, delay=20)
                        await page.wait_for_timeout(1000)
                        print("[✓] News script entered!")
                    else:
                        print("[✗] Script box not found")

                    print("\n[>] === STEP: Opening Avatar IV dropdown ===")
                    await click_avatar_iv_dropdown(page)

                    print("[>] === STEP: Selecting Avatar III ===")
                    ok = await select_avatar_iii(page)
                    if ok:
                        print("[✓] Avatar III selected!")
                    else:
                        print("[!] Check debug_dropdown.png for what was visible")

                    await page.wait_for_timeout(1500)

                    print("[>] Starting popup monitor...")
                    await monitor_and_close_dialogs(page)

                    print("\n[>] === STEP: Clicking Generate ===")
                    await click_generate_button(page)

                    # Generate a unique filename with timestamp for tracking
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    custom_filename = f"heygen_video_{timestamp}.mp4"
                    downloaded_file = await wait_and_download_latest_video(page, custom_filename)

                else:
                    print("[✗] Script to video tab not found")
            else:
                print("[✗] Start Creating button not found")
        else:
            print("[✗] 'Make an avatar video from a photo' option not found")

        print("\n[✓] Task completed!")

        # If called as module, return the path and close browser
        if news_script is not None:
            await browser.close()
            return downloaded_file

        # If run directly, keep browser open
        print("Browser will stay open...")
        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            print("\n[>] Closing browser...")
            await browser.close()


async def run_heygen(news_script):
    """Public API: run the full HeyGen flow with given news script.
    Returns the path to the downloaded video, or None on failure."""
    return await main(news_script)


if __name__ == "__main__":
    # When run directly, check if news script passed via command line
    if len(sys.argv) > 1:
        asyncio.run(main(news_script=sys.argv[1]))
    else:
        asyncio.run(main())
