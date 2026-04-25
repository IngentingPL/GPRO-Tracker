import asyncio
from playwright.async_api import async_playwright
import os

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        filepath = "file://" + os.path.abspath("index.html")
        await page.goto(filepath)
        await asyncio.sleep(0.5)

        # Initial active tab should be overview
        is_overview_visible = await page.is_visible("#tab-overview.active")
        print(f"Initial Overview active: {is_overview_visible}")

        # Click Next Race tab
        await page.click("button[data-tab='nextrace']")
        await asyncio.sleep(0.5)
        is_nextrace_active = await page.is_visible("#tab-nextrace.active")
        print(f"Next Race tab active after click: {is_nextrace_active}")

        # Click Car tab
        await page.click("button[data-tab='car']")
        await asyncio.sleep(0.5)
        is_car_active = await page.is_visible("#tab-car.active")
        print(f"Car tab active after click: {is_car_active}")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
