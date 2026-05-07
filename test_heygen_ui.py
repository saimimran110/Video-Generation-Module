from playwright.sync_api import sync_playwright
import json
with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    context = browser.new_context(storage_state='heygen_session.json')
    page = context.new_page()
    page.goto('https://app.heygen.com')
    page.wait_for_timeout(5000)
    page.screenshot(path='heygen_dashboard.png')
    browser.close()
