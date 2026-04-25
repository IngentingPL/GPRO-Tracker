import asyncio
from playwright.async_api import async_playwright
import os

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()

        errors = []
        page.on("pageerror", lambda exc: errors.append(f"EXCEPTION: {exc}"))
        page.on("console", lambda msg: errors.append(f"CONSOLE {msg.type}: {msg.text}") if msg.type == "error" else None)

        filepath = "file://" + os.path.abspath("index.html")
        await page.goto(filepath)

        # Wait a bit for JS to run
        await asyncio.sleep(1)

        if errors:
            print("Found JS errors:")
            for err in errors:
                print(err)
        else:
            print("No JS errors found on load.")

        # Try clicking a tab
        try:
            await page.click("button[data-tab='nextrace']")
            await asyncio.sleep(0.5)
        except Exception as e:
            print(f"Failed to click tab: {e}")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
