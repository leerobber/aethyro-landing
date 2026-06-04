"""Submit sitemap using your signed-in Chrome profile."""
import asyncio
from playwright.async_api import async_playwright

SITEMAP     = "https://aethyro.com/sitemap.xml"
SHOTS       = "C:/Users/leer4/Documents/aethyro_landing"
CHROME_PROFILE = "C:/Users/leer4/AppData/Local/Google/Chrome/User Data"
SITEMAP_URL = "https://search.google.com/search-console/sitemaps?resource_id=https%3A%2F%2Faethyro.com%2F"

def log(m): print(f"  >> {m}", flush=True)

async def main():
    print("\n  Submitting sitemap using your Chrome profile...\n")
    async with async_playwright() as p:
        ctx = await p.chromium.launch_persistent_context(
            user_data_dir=CHROME_PROFILE,
            channel="chrome",
            headless=False,
            args=["--start-maximized"],
            ignore_default_args=["--disable-sync", "--enable-automation", "--disable-extensions"],
            viewport=None,
        )
        page = await ctx.new_page()
        try:
            log("Opening GSC sitemaps page...")
            await page.goto(SITEMAP_URL, wait_until="domcontentloaded", timeout=30_000)
            await page.wait_for_load_state("networkidle", timeout=15_000)
            await asyncio.sleep(3)
            await page.screenshot(path=f"{SHOTS}/sitemap_01_loaded.png")
            log("Screenshot: sitemap_01_loaded.png")

            content = await page.inner_text("body")

            # Already submitted?
            if "sitemap.xml" in content:
                log("Sitemap already submitted and showing in GSC!")
                await page.screenshot(path=f"{SHOTS}/sitemap_done.png")
                await asyncio.sleep(20)
                return

            # Enter sitemap URL
            log(f"Entering: {SITEMAP}")
            for sel in [
                'input[placeholder*="sitemap" i]',
                'input[placeholder*="Enter" i]',
                'input[placeholder*="Add" i]',
                'input[type="url"]',
            ]:
                try:
                    el = page.locator(sel).first
                    if await el.is_visible(timeout=4_000):
                        await el.click()
                        await el.fill(SITEMAP)
                        log("URL entered.")
                        break
                except Exception:
                    pass

            await asyncio.sleep(1)
            await page.screenshot(path=f"{SHOTS}/sitemap_02_filled.png")

            # Click Submit
            for sel in ["button:has-text('Submit')", "text=Submit"]:
                try:
                    btn = page.locator(sel).first
                    if await btn.is_visible(timeout=4_000):
                        await btn.click()
                        log("Submitted!")
                        break
                except Exception:
                    pass

            await asyncio.sleep(5)
            await page.wait_for_load_state("networkidle", timeout=20_000)
            await page.screenshot(path=f"{SHOTS}/sitemap_03_result.png")
            log("Screenshot: sitemap_03_result.png")

            content = await page.inner_text("body")
            if any(w in content for w in ["sitemap.xml", "Pending", "Success"]):
                log("Sitemap submitted successfully!")
            else:
                log("Done. Check sitemap_03_result.png")

            log("Keeping open 30s...")
            await asyncio.sleep(30)

        except Exception as e:
            log(f"Error: {e}")
            import traceback; traceback.print_exc()
            await asyncio.sleep(20)
        finally:
            await ctx.close()

asyncio.run(main())
