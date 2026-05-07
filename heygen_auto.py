"""
HeyGen Auto Video Generator v2
================================
- Pehli baar manually login karo (Cloudflare bypass)
- Session save ho jaata hai — dobara login nahi maangega
- Phir sab automatic!

Requirements:
    pip install playwright
    playwright install chromium

Usage:
    MODE 1: Automated Chrome (new instance):
        python heygen_auto.py
    
    MODE 2: Your Personal Chrome (existing profile):
        1. Pehle ye command terminal mein chalao:
           chrome.exe --remote-debugging-port=9222
        2. Phir doosre terminal mein:
           python heygen_auto.py personal
"""

import asyncio
import os
import random
import time
import sys
from pathlib import Path
from playwright.async_api import async_playwright

# ══════════════════════════════════════════
#  CONFIG
# ══════════════════════════════════════════
DOWNLOAD_FOLDER = r"C:\Videos\HeyGen"
AVATAR_NAME     = "Nicholas"
HEADLESS        = False   # Pehli baar False rakhna zaroori hai
AUTH_FILE       = "heygen_session.json"
DEFAULT_SCRIPT   = (
    "You’re tuned into today’s news briefing. Let’s take a quick look at the biggest stories.\n"
    "Experts weigh in as the situation develops across multiple regions."
)
# ══════════════════════════════════════════


def p(msg):  print(f"[>] {msg}")
def ok(msg): print(f"[✓] {msg}")
def err(msg):print(f"[✗] {msg}")


async def manual_login(playwright):
    """
    Browser kholo — manually login karo — session save karo
    Yeh sirf PEHLI BAAR karna hai
    """
    print("=" * 55)
    print("  MANUAL LOGIN MODE")
    print("=" * 55)
    print()
    print("Browser khulega — aap manually login karo:")
    print("  1. Sign in with Email click karo")
    print("  2. Use password instead click karo")
    print("  3. Email/password bharo")
    print("  4. Cloudflare checkbox tick karo")
    print("  5. Log in karo")
    print()
    print("Jab dashboard khul jaaye — terminal mein Enter dabao!")
    print()

    browser = await playwright.chromium.launch(
        headless=False,
        args=["--no-sandbox", "--disable-blink-features=AutomationControlled"]
    )
    context = await browser.new_context(
        viewport={"width": 1280, "height": 800},
        user_agent=(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
    )
    page = await context.new_page()
    await page.goto("https://app.heygen.com/login", wait_until="domcontentloaded", timeout=60000)

    # User ke login ka wait karo
    await asyncio.to_thread(input, "Login karne ke baad Enter dabao...")

    # Session save karo
    await context.storage_state(path=AUTH_FILE)
    ok(f"Session saved: {AUTH_FILE}")
    await browser.close()


async def go_to_avatar_page(page):
    p("Avatar page pe ja raha hun...")
    await page.goto("https://app.heygen.com/avatar", wait_until="domcontentloaded", timeout=60000)
    await page.wait_for_timeout(7000)
    ok("Avatar page khul gaya!")


async def select_script_to_video(page):
    p("Checking current tab...")
    try:
        # Check agar Script to video pehle se active hai
        script_tab = page.get_by_role("tab", name="Script to video")
        if await script_tab.count() > 0:
            # Check agar ye tab active hai (aria-selected="true" ya selected class)
            is_active = await script_tab.first.evaluate("el => el.getAttribute('aria-selected') === 'true' || el.classList.contains('active')")
            if is_active:
                ok("Script to video already active!")
                return
        
        # Agar active nahi hai, then click karo
        p("Switching to Script to video tab...")
        await script_tab.first.click(force=True)
        await page.wait_for_timeout(1500)
        ok("Script to video tab active ho gaya!")
    except Exception as e:
        err(f"Tab switch mein issue: {e}")
        p("Continuing anyway...")


async def select_avatar(page):
    p("Avatar panel ke left arrow pe click kar raha hun...")
    try:
        left_arrow = page.locator(
            'button.tw-inline-flex.tw-items-center.tw-justify-center.tw-shrink-0.tw-text-textBody, '
            '[class="tw-inline-flex tw-items-center tw-justify-center tw-shrink-0 tw-text-textBody"]'
        ).first
        await left_arrow.wait_for(state="visible", timeout=10000)
        await left_arrow.click(force=True)
        await page.wait_for_timeout(1500)
        ok("Avatar selector arrow clicked")

        # Pehle Nicholas try karo.
        nicholas = page.locator(
            'button:has-text("Nicholas"), '
            '[role="button"]:has-text("Nicholas"), '
            'div:has-text("Nicholas")'
        ).first

        if await nicholas.count() > 0:
            try:
                await nicholas.click(force=True)
                await page.wait_for_timeout(1200)
                ok("Nicholas avatar selected")
            except Exception:
                p("Nicholas mila lekin click issue, fallback use kar raha hun...")
        else:
            p("Nicholas nahi mila, 2nd last / 3rd last rows se random avatar le raha hun...")
            avatar_cards = page.locator(
                '[role="button"][class*="avatar"], '
                'button[class*="avatar"], '
                '[class*="avatar-card"], '
                'div[role="button"][class*="rounded"]'
            )
            card_count = await avatar_cards.count()

            if card_count > 0:
                row_size = 4
                second_last_row_start = max(0, card_count - (2 * row_size))
                second_last_row_end = max(0, card_count - row_size - 1)
                third_last_row_start = max(0, card_count - (3 * row_size))
                third_last_row_end = max(0, card_count - (2 * row_size) - 1)

                fallback_indices = []
                fallback_indices.extend(range(third_last_row_start, third_last_row_end + 1))
                fallback_indices.extend(range(second_last_row_start, second_last_row_end + 1))
                fallback_indices = [i for i in fallback_indices if 0 <= i < card_count]

                if not fallback_indices:
                    fallback_indices = [max(0, card_count - 1)]

                pick_idx = random.choice(fallback_indices)
                await avatar_cards.nth(pick_idx).click(force=True)
                await page.wait_for_timeout(1200)
                ok(f"Fallback avatar selected at index {pick_idx}")
            else:
                p("Avatar cards nahi mile, current avatar continue hoga")

        # Ab isi section se random avatar image choose karo.
        p("Avatar images me se random image choose kar raha hun...")
        image_options = page.locator(
            '[role="button"] img, '
            'button img, '
            '[class*="thumbnail"] img'
        )
        img_count = await image_options.count()

        if img_count > 0:
            img_idx = random.randint(0, img_count - 1)
            chosen_img = image_options.nth(img_idx)
            try:
                await chosen_img.click(force=True)
            except Exception:
                await chosen_img.evaluate("el => el.closest('button,[role=button]')?.click()")
            await page.wait_for_timeout(1200)
            ok(f"Random avatar image selected at index {img_idx}")
        else:
            p("Random image options nahi mili, skip kar raha hun")
            
    except Exception as e:
        err(f"Avatar select mein issue: {e}")
        await page.screenshot(path="avatar_error.png")
        p("Continuing...")


async def select_avatar_iii(page):
    p("Avatar IV / Avatar V icon se Avatar III select kar raha hun...")
    try:
        avatar_switch = page.locator(
            'button:has-text("Avatar IV"), '
            'button:has-text("Avatar V"), '
            '[role="button"]:has-text("Avatar IV"), '
            '[role="button"]:has-text("Avatar V")'
        ).first
        await avatar_switch.wait_for(state="visible", timeout=10000)
        await avatar_switch.click(force=True)
        await page.wait_for_timeout(1200)

        avatar_iii = page.locator(
            'button:has-text("Avatar III"), '
            '[role="option"]:has-text("Avatar III"), '
            'text="Avatar III"'
        ).first
        await avatar_iii.wait_for(state="visible", timeout=10000)
        await avatar_iii.click(force=True)
        await page.wait_for_timeout(1000)
        ok("Avatar III selected")
    except Exception as e:
        err(f"Avatar III select nahi hua: {e}")
        await page.screenshot(path="avatar_iii_error.png")
        p("Continuing with currently selected avatar...")


async def enter_script(page, script_text):
    p("Script enter kar raha hun...")
    try:
        box = page.locator(
            'textarea[placeholder*="script" i], '
            'textarea[placeholder*="Script" i], '
            'div[contenteditable="true"]'
        ).first
        await box.wait_for(state="visible", timeout=10000)
        await box.click()
        await box.fill(script_text)
        await page.wait_for_timeout(1000)
        ok("Script enter ho gayi!")
    except Exception as e:
        err(f"Script enter nahi hui: {e}")
        raise


async def click_generate(page):
    p("Generate button click kar raha hun...")
    try:
        # Scroll down taake button visible ho
        await page.evaluate("window.scrollBy(0, 300)")
        await page.wait_for_timeout(1000)
        
        # Multiple selectors try karo
        gen_btn = None
        
        # Try 1: Button with Generate text
        try:
            gen_btn = page.locator('button:has-text("Generate")').first
            await gen_btn.wait_for(state="visible", timeout=3000)
        except:
            pass
        
        # Try 2: Aria-label se
        if not gen_btn or await gen_btn.count() == 0:
            try:
                gen_btn = page.locator('[aria-label*="Generate" i]').first
                await gen_btn.wait_for(state="visible", timeout=3000)
            except:
                pass
        
        # Try 3: Class-based selector
        if not gen_btn or await gen_btn.count() == 0:
            try:
                gen_btn = page.locator('button[class*="primary"], button[class*="generate"]').first
                await gen_btn.wait_for(state="visible", timeout=3000)
            except:
                pass
        
        # Try 4: Last button in certain container
        if not gen_btn or await gen_btn.count() == 0:
            try:
                gen_btn = page.locator('button').filter(has_text="Generate").first
                await gen_btn.wait_for(state="visible", timeout=3000)
            except:
                pass
        
        if gen_btn and await gen_btn.count() > 0:
            await gen_btn.click(force=True)
            await page.wait_for_timeout(1000)
            ok("Video started!")
        else:
            err("Generate button selector failed — all attempts unsuccessful")
            await page.screenshot(path="generate_button_error.png")
            raise Exception("Could not locate Generate button")
            
    except Exception as e:
        err(f"Generate button nahi mila: {e}")
        await page.screenshot(path="generate_error.png")
        raise


async def wait_and_download(page, folder):
    p("Video complete hone ka wait kar raha hun...")
    p("(2-5 minutes lag sakte hain)")
    os.makedirs(folder, exist_ok=True)

    max_wait = 600
    start    = time.time()
    downloaded = False

    while time.time() - start < max_wait:
        elapsed = int(time.time() - start)
        print(f"\r    Waiting... {elapsed}s", end="", flush=True)

        try:
            items = page.locator(
                '[class*="recent"] [class*="item"], '
                '[class*="video-list"] [class*="item"], '
                'li[class*="video"]'
            )
            if await items.count() > 0:
                first = items.first
                loading = await first.locator(
                    'text="%", [class*="progress"], [class*="loading"], [class*="pending"]'
                ).count()

                if loading == 0:
                    print()
                    ok("Video ready ho gayi!")
                    await first.click()
                    await page.wait_for_timeout(2000)

                    dl_btn = page.locator(
                        'button:has-text("Download"), '
                        'a:has-text("Download"), '
                        '[aria-label*="download" i]'
                    ).first

                    if await dl_btn.is_visible(timeout=5000):
                        async with page.expect_download(timeout=60000) as dl_info:
                            await dl_btn.click()
                        dl = await dl_info.value
                        fname = f"heygen_{int(time.time())}.mp4"
                        save_path = os.path.join(folder, fname)
                        await dl.save_as(save_path)
                        ok(f"Video saved: {save_path}")
                        downloaded = True
                        break
                    else:
                        err("Download button nahi mila")
                        await page.screenshot(path="debug.png")
                        p("debug.png check karo")
                        break

        except Exception:
            pass

        await asyncio.sleep(10)

    print()
    if not downloaded:
        err("Timeout ya error — video download nahi hui")
        await page.screenshot(path="debug.png")
    return downloaded


async def auto_run(playwright, script_text, use_personal_chrome=False):
    """Saved session se automatic run karo"""
    
    if use_personal_chrome:
        p("Personal Chrome se connect kar raha hun (port 9222)...")
    else:
        p("Saved session se login kar raha hun...")

    while True:
        try:
            if use_personal_chrome:
                # Existing Chrome instance se connect karo with retries
                browser = None
                max_retries = 15
                retry_count = 0
                
                while retry_count < max_retries:
                    try:
                        p(f"Chrome se connect kar raha hun (attempt {retry_count + 1}/{max_retries})...")
                        # Try 127.0.0.1 explicitly instead of localhost
                        browser = await playwright.chromium.connect_over_cdp("http://127.0.0.1:9222")
                        ok("Personal Chrome se connected!")
                        break
                    except Exception as e:
                        retry_count += 1
                        if retry_count < max_retries:
                            p(f"Waiting 3 seconds before retry... ({str(e)[:50]})")
                            await asyncio.sleep(3)
                        else:
                            err(f"Chrome se connect nahi ho saka (after {max_retries} attempts): {e}")
                            err("Ensure Chrome is running with: chrome.exe --remote-debugging-port=9222")
                            err("Chrome ko fully load hone mein 10-15 seconds lag sakte hain!")
                            break
                
                if not browser:
                    break
                    
                context = browser.contexts[0] if browser.contexts else await browser.new_context()
                page = context.pages[0] if context.pages else await context.new_page()
                
            else:
                # New browser launch karo (pehli tarah)
                browser = await playwright.chromium.launch(
                    headless=HEADLESS,
                    args=["--no-sandbox", "--disable-blink-features=AutomationControlled"]
                )
                context = await browser.new_context(
                    viewport={"width": 1280, "height": 800},
                    user_agent=(
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/120.0.0.0 Safari/537.36"
                    ),
                    storage_state=AUTH_FILE,
                    accept_downloads=True,
                )
                page = await context.new_page()

            try:
                await page.goto("https://app.heygen.com/avatar", wait_until="domcontentloaded", timeout=60000)
                await page.wait_for_timeout(3000)

                if "login" in page.url.lower() or await page.locator('button:has-text("Sign in with email"), button:has-text("Sign in with Email")').count() > 0:
                    err("Saved session invalid ya expire ho gayi hai")
                    if not use_personal_chrome and Path(AUTH_FILE).exists():
                        Path(AUTH_FILE).unlink()
                    if not use_personal_chrome:
                        await browser.close()
                    await manual_login(playwright)
                    p("Fresh session mil gayi — ab automation continue kar raha hun...")
                    if use_personal_chrome:
                        break
                    continue

                await go_to_avatar_page(page)
                await page.wait_for_timeout(2000)
                await select_script_to_video(page)
                await page.wait_for_timeout(1000)
                await select_avatar(page)
                await page.wait_for_timeout(1000)
                await select_avatar_iii(page)
                await page.wait_for_timeout(1000)
                await enter_script(page, script_text)
                ok("Script entered. Generate click skip kiya gaya hai.")
                await page.screenshot(path="final_script_entered.png")
                await asyncio.to_thread(input, "Script enter ho gaya. Browser close karne ke liye Enter dabao...")
                break
            except Exception as e:
                err(f"Error: {e}")
                await page.screenshot(path="error.png")
                p("error.png check karo")
                break
            finally:
                if not use_personal_chrome and browser:
                    await browser.close()
                    
        except Exception as e:
            err(f"Connection error: {e}")
            if not use_personal_chrome:
                err("Retrying...")
                await asyncio.sleep(2)
            else:
                err("Personal Chrome se disconnect hua — dobara try karo")
                break


async def main():
    print("=" * 55)
    print("   HEYGEN AUTO VIDEO GENERATOR  v2")
    print("=" * 55)

    # Check if personal Chrome mode
    use_personal = len(sys.argv) > 1 and sys.argv[1].lower() == "personal"
    
    if use_personal:
        print()
        print("🔗 PERSONAL CHROME MODE")
        print("-" * 55)
        print("Ensure Chrome is running with:")
        print("  chrome.exe --remote-debugging-port=9222")
        print("-" * 55)
        print()

    async with async_playwright() as pw:

        # Manual login sirf agar automated mode ho
        if not use_personal and not Path(AUTH_FILE).exists():
            print()
            print("Session file nahi mili — pehle manual login karein!")
            await manual_login(pw)
            print()
            ok("Ab automatic mode shuru ho raha hai!")
            print()
        elif use_personal:
            p("Personal Chrome se directly connect kar raha hun...")
        else:
            p(f"Session file mili: {AUTH_FILE}")

        # Default script use karo
        script_text = DEFAULT_SCRIPT
        print()
        p(f"Default script: {script_text[:70]}...")
        print()

        # Auto run (with personal flag)
        await auto_run(pw, script_text, use_personal_chrome=use_personal)

    print()
    print("=" * 55)
    print("   DONE!")
    print("=" * 55)


if __name__ == "__main__":
    asyncio.run(main())