import asyncio
from playwright.async_api import async_playwright
import os

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()

        filepath = "file://" + os.path.abspath("index.html")
        await page.goto(filepath)
        await asyncio.sleep(1)

        # Sprawdź czy Przegląd ma treść
        overview_content = await page.inner_text("#tab-overview")
        print(f"Overview has content: {len(overview_content.strip()) > 0}")
        if len(overview_content.strip()) > 0:
            print(f"Overview preview: {overview_content.strip()[:100]}...")

        # Kliknij 'Następny wyścig'
        await page.click("button[data-tab='nextrace']")
        await asyncio.sleep(0.5)

        nextrace_content = await page.inner_text("#tab-nextrace")
        print(f"Next Race has content: {len(nextrace_content.strip()) > 0}")

        # Kliknij 'Tabela'
        await page.click("button[data-tab='standings']")
        await asyncio.sleep(0.5)

        standings_content = await page.inner_text("#tab-standings")
        print(f"Standings has content: {len(standings_content.strip()) > 0}")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
