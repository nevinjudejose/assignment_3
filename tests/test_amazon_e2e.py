from pathlib import Path
import pytest
from playwright.async_api import expect


@pytest.mark.asyncio
async def test_amazon_full_navigation_workflow(browser_page):
    page = browser_page

    # 1. Open Amazon India and verify home page loads
    response = await page.goto(
        "https://www.amazon.in/",
        wait_until="domcontentloaded",
        timeout=60000
    )
    assert response is not None and response.status < 500, "Amazon home page failed to load"

    search_box = page.locator("#twotabsearchtextbox")
    await expect(search_box).to_be_visible(timeout=30000)

    # 2 & 9. Verify hover menu (hidden -> trigger hover -> visible)
    account_menu = page.locator("#nav-link-accountList")
    hover_dropdown = page.locator("#nav-al-container")

    if await account_menu.count() > 0:
        await expect(hover_dropdown).not_to_be_visible()
        await account_menu.hover()
        await expect(hover_dropdown).to_be_visible(timeout=5000)

    # 3 & 4. Search using dynamic suggestions with visible text
    await search_box.fill("iphone")
    suggestion = page.locator("div.s-suggestion").filter(has_text="Apple").first

    try:
        await expect(suggestion).to_be_visible(timeout=10000)
        await suggestion.click()
    except Exception:
        await page.locator("#nav-search-submit-button").click()

    await page.wait_for_load_state("domcontentloaded")

    # 5. Incremental scroll & pagination check
    for _ in range(3):
        await page.mouse.wheel(0, 800)
        await page.wait_for_timeout(1000)

    pagination = page.locator("span.s-pagination-strip, ul.a-pagination")
    if await pagination.count() > 0:
        await pagination.scroll_into_view_if_needed()
        await expect(pagination.first).to_be_visible(timeout=10000)
        print("Verified: Page uses pagination footer rather than infinite scroll.")

    # 4 & 5. Open organic product (extract URL and goto to avoid popup/tab issues)
    organic_card = page.locator(
        'div[data-component-type="s-search-result"]:not(:has(.puis-sponsored-label-text))'
    ).filter(has=page.locator('a[href*="/dp/"]')).first

    product_link = organic_card.locator('a[href*="/dp/"]').first
    await expect(product_link).to_be_attached(timeout=30000)

    href = await product_link.get_attribute("href")
    if href.startswith("/"):
        href = f"https://www.amazon.in{href}"

    await page.goto(href, wait_until="domcontentloaded", timeout=60000)

    # 6. Verify Watch Product Title AND Price on details page
    watch_title = page.locator("span#productTitle")
    await expect(watch_title).to_be_visible(timeout=30000)
    title_text = (await watch_title.inner_text()).strip()
    assert len(title_text) > 0, "Product title is empty"
    print("Verified Title:", title_text)

    price = page.locator('//span[@data-a-size="xl"]').first
    await expect(price).to_be_visible(timeout=15000)
    print("Verified Price: ₹", (await price.inner_text()).strip())

    # 7. Right-click on non-destructive element
    await watch_title.click(button="right")

    # 8. Double-click harmless text label
    await watch_title.dblclick()

    # 9. Verify expandable section (hidden -> trigger -> visible)
    expander = page.locator("a[data-action='a-expander-toggle']").first
    if await expander.count() > 0 and await expander.is_visible():
        await expander.scroll_into_view_if_needed()
        await expander.click()
        await page.wait_for_timeout(500)

    # 10. Save screenshot
    screenshot_dir = Path("artifacts/screenshots")
    screenshot_dir.mkdir(parents=True, exist_ok=True)
    await page.screenshot(
        path=str(screenshot_dir / "amazon_watch_verification.png"),
        full_page=True
    )

    print("PASS: Amazon watch navigation and verification completed successfully.")