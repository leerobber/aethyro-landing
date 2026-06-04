"""Google Search Console — verify ownership + submit sitemap for aethyro.com."""
import asyncio
from pathlib import Path
from playwright.async_api import async_playwright, TimeoutError as PWTimeout

SITE       = "https://aethyro.com/"
SITEMAP    = "https://aethyro.com/sitemap.xml"
PROFILE    = str(Path.home() / ".gsc_profile2")
SHOTS      = "C:/Users/leer4/Documents/aethyro_landing"

VERIFY_URL  = "https://search.google.com/search-console/ownership?resource_id=https%3A%2F%2Faethyro.com%2F&hl=en"
SITEMAP_URL = "https://search.google.com/search-console/sitemaps?resource_id=https%3A%2F%2Faethyro.com%2F&hl=en"
SC_HOME     = "https://search.google.com/search-console/welcome?hl=en"


def log(m): print(f"  >> {m}", flush=True)


async def shot(page, name):
    try:
        await page.screenshot(path=f"{SHOTS}/gsc_{name}.png", full_page=False)
        log(f"Screenshot: gsc_{name}.png")
    except Exception:
        pass


async def on_gsc(page) -> bool:
    """True only if we're on a real GSC page (not the login form)."""
    try:
        url = page.url
        # Must be on search.google.com but NOT the accounts/signin flow
        if "accounts.google.com" in url:
            return False
        if "search.google.com" not in url:
            return False
        # Confirm there's no email/password input (login form)
        email_input = page.locator('input[type="email"], input[type="password"]')
        count = await email_input.count()
        return count == 0
    except Exception:
        return False


async def wait_for_gsc(page, timeout_s=300):
    """Block until the user is signed into GSC and the dashboard has loaded."""
    log("Sign in with your Google account in the browser.")
    log("(Enter your email, password, and 2FA if prompted.)")
    log("The script will resume automatically once you're signed in.")
    deadline = asyncio.get_event_loop().time() + timeout_s
    while asyncio.get_event_loop().time() < deadline:
        await asyncio.sleep(4)
        try:
            if await on_gsc(page):
                # Extra stability wait — make sure page isn't still loading
                await page.wait_for_load_state("networkidle", timeout=10_000)
                await asyncio.sleep(2)
                if await on_gsc(page):
                    log("Signed in — GSC loaded. Resuming.")
                    return True
        except Exception:
            pass
    log("Sign-in timed out. Proceeding anyway...")
    return False


async def safe_goto(page, url):
    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=30_000)
        await page.wait_for_load_state("networkidle", timeout=15_000)
    except Exception as e:
        log(f"Nav note: {e}")


async def click_first(page, selectors, label="button"):
    for sel in selectors:
        try:
            loc = page.locator(sel).first
            if await loc.is_visible(timeout=4_000):
                await loc.click()
                log(f"Clicked: {label}")
                return True
        except Exception:
            pass
    return False


async def fill_first(page, selectors, value, label="field"):
    for sel in selectors:
        try:
            loc = page.locator(sel).first
            if await loc.is_visible(timeout=4_000):
                await loc.triple_click()
                await loc.fill(value)
                log(f"Filled {label}: {value}")
                return True
        except Exception:
            pass
    return False


async def do_verify(page):
    log("Loading verification page...")
    await safe_goto(page, VERIFY_URL)
    await asyncio.sleep(3)

    # If we got redirected to login again, wait
    if not await on_gsc(page):
        await wait_for_gsc(page)
        await safe_goto(page, VERIFY_URL)
        await asyncio.sleep(3)

    await shot(page, "03_verify_page")

    content = await page.inner_text("body")
    if any(w in content for w in ["Ownership verified", "Verified", "verified"]):
        log("Already verified!")
        return True

    # Expand HTML tag verification method
    await click_first(page,
        ["text=HTML tag", "text=HTML meta tag", "[role='tab']:has-text('HTML')"],
        "HTML tag tab")
    await asyncio.sleep(2)

    # Click Verify
    clicked = await click_first(page,
        ["button:has-text('Verify')", "text=Verify",
         "input[value='Verify']", "[aria-label='Verify']"],
        "Verify button")

    if clicked:
        await asyncio.sleep(5)
        await page.wait_for_load_state("networkidle", timeout=25_000)
        await shot(page, "04_after_verify")
        content = await page.inner_text("body")
        if any(w in content for w in ["verified", "Verified", "Ownership verified"]):
            log("VERIFIED!")
            return True
        log("Verify clicked — check gsc_04_after_verify.png")
        return True

    # Could not auto-click — try getting page source for debugging
    log("Could not find Verify button automatically.")
    html = await page.content()
    # Save a snippet for debugging
    with open(f"{SHOTS}/gsc_verify_debug.html", "w", encoding="utf-8") as f:
        f.write(html[:5000])
    log("Saved gsc_verify_debug.html for inspection")
    return False


async def do_sitemap(page):
    log("Loading Sitemaps page...")
    await safe_goto(page, SITEMAP_URL)
    await asyncio.sleep(3)

    if not await on_gsc(page):
        await wait_for_gsc(page)
        await safe_goto(page, SITEMAP_URL)
        await asyncio.sleep(3)

    await shot(page, "05_sitemaps_page")

    content = await page.inner_text("body")
    if "sitemap.xml" in content:
        log("Sitemap already submitted!")
        return True

    # Fill sitemap URL
    filled = await fill_first(page,
        ['input[placeholder*="sitemap" i]',
         'input[placeholder*="Enter" i]',
         'input[placeholder*="Add" i]',
         'input[type="url"]'],
        SITEMAP, "sitemap URL")

    if not filled:
        log("Could not find sitemap input. Saving page for debug.")
        html = await page.content()
        with open(f"{SHOTS}/gsc_sitemap_debug.html", "w", encoding="utf-8") as f:
            f.write(html[:5000])
        return False

    await asyncio.sleep(1)
    clicked = await click_first(page,
        ["button:has-text('Submit')", "text=Submit", "input[value='Submit']"],
        "Submit button")

    if clicked:
        await asyncio.sleep(5)
        await page.wait_for_load_state("networkidle", timeout=25_000)
        await shot(page, "06_after_submit")
        content = await page.inner_text("body")
        if any(w in content for w in ["sitemap.xml", "Pending", "Success"]):
            log("Sitemap submitted!")
            return True
        log("Submitted — check gsc_06_after_submit.png")

    return True


async def main():
    print()
    print("=" * 60)
    print("  Aethyro GSC — Verify + Submit Sitemap")
    print("=" * 60)
    print(f"  Site:    {SITE}")
    print(f"  Sitemap: {SITEMAP}")
    print()
    print("  Browser opening. Sign in with your Google account.")
    print("  Script waits until you're fully logged in.")
    print()

    async with async_playwright() as p:
        ctx = await p.chromium.launch_persistent_context(
            user_data_dir=PROFILE,
            headless=False,
            args=[
                "--start-maximized",
                "--disable-blink-features=AutomationControlled",
                "--no-first-run",
                "--no-default-browser-check",
                "--disable-web-security",
            ],
            viewport=None,
            ignore_https_errors=True,
        )
        page = await ctx.new_page()

        try:
            # Navigate to GSC — will redirect to login if not signed in
            log("Navigating to Google Search Console...")
            await safe_goto(page, SC_HOME)
            await asyncio.sleep(3)
            await shot(page, "01_initial")

            # If not logged in, wait for the user
            if not await on_gsc(page):
                await wait_for_gsc(page)
                await safe_goto(page, SC_HOME)
                await asyncio.sleep(3)

            await shot(page, "02_logged_in")
            log("On GSC dashboard.")

            # Verify ownership
            verified = await do_verify(page)

            # Submit sitemap
            await do_sitemap(page)

            await shot(page, "07_final")
            print()
            print("=" * 60)
            print("  DONE. Check screenshots in aethyro_landing/")
            print("  Browser stays open 60s for review.")
            print("=" * 60)
            await asyncio.sleep(60)

        except KeyboardInterrupt:
            log("Stopped.")
        except Exception as e:
            log(f"Error: {e}")
            import traceback; traceback.print_exc()
            await asyncio.sleep(60)
        finally:
            try:
                await ctx.close()
            except Exception:
                pass


if __name__ == "__main__":
    asyncio.run(main())
