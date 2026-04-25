from playwright.sync_api import sync_playwright
import os

def run_cuj(page):
    # Go to the local index.html
    path = os.path.abspath("index.html")
    page.goto(f"file://{path}")
    page.wait_for_timeout(1000)

    # 1. Verify Overview tab (default)
    page.screenshot(path="verification/screenshots/overview_driver.png")
    page.wait_for_timeout(500)

    # 2. Click on 'Tabela' tab (exact match)
    page.get_by_role("button", name="Tabela", exact=True).click()
    page.wait_for_timeout(1000)
    page.screenshot(path="verification/screenshots/standings_tab.png")
    page.wait_for_timeout(500)

    # 3. Go back to Overview and click 'PEŁNA TABELA' button
    page.get_by_role("button", name="Przegląd").click()
    page.wait_for_timeout(500)
    page.get_by_role("button", name="PEŁNA TABELA »").click()
    page.wait_for_timeout(1000)
    page.screenshot(path="verification/screenshots/full_standings_via_button.png")

    page.wait_for_timeout(1000)

if __name__ == "__main__":
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            record_video_dir="verification/videos",
            viewport={'width': 1280, 'height': 1024}
        )
        page = context.new_page()
        try:
            run_cuj(page)
        finally:
            context.close()
            browser.close()
