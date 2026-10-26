import pytest
from playwright.async_api import expect


@pytest.mark.asyncio
async def test_demowebshop_product_and_cart(browser_page):
    page = browser_page

    # 1. Open the home page and verify main navigation is visible
    print("Step 1: Opening DemoWebShop home page...")
    response = await page.goto(
        "https://demowebshop.tricentis.com/",
        wait_until="domcontentloaded",
        timeout=60000
    )
    assert response is not None and response.status < 500

    top_menu = page.locator("ul.top-menu")
    await expect(top_menu).to_be_visible(timeout=15000)

    # 2. Hover over a navigation/category item with submenu and verify menu state
    print("Step 2: Hovering over 'Computers' menu and checking submenu...")
    computers_menu = page.locator('(//a[@href="/computers"])[1]')
    await computers_menu.hover()

    # Verify that the dropdown sublist appears
    computers_sublist = page.locator('(//a[@href="/notebooks"])[1]').first
    await expect(computers_sublist).to_be_visible()

    # 3. Open Books category
    print("Step 3: Opening 'Books' category...")
    books_link = page.locator('(//a[@href="/books"])[1]').first
    await books_link.click()
    await expect(page.locator('//div[@class="page-title"]')).to_contain_text("Books")

    # 4. Scroll through product listings and verify items & pager
    print("Step 4: Scrolling product listing...")
    await page.mouse.wheel(0, 500)
    await page.wait_for_timeout(500)
    product_items = page.locator(".product-grid .item-box")
    await expect(product_items.first).to_be_visible()

    # 5. Handle dynamic dropdown / autocomplete suggestions
    print("Step 5: Typing in search box and selecting autocomplete suggestion...")
    search_box = page.locator("#small-searchterms")
    await expect(search_box).to_be_visible()
    await search_box.fill("Comput")

    # Wait for the jQuery UI autocomplete dropdown list to appear
    autocomplete_menu = page.locator("ul.ui-autocomplete")
    await expect(autocomplete_menu).to_be_visible(timeout=10000)

    # Select the expected visible option ("Computing and Internet")
    expected_option = autocomplete_menu.locator("li a", has_text="Computing and Internet").first
    await expect(expected_option).to_be_visible()
    await expected_option.click()

    # 6. Validate product title and price
    print("Step 6: Validating product title and price...")
    product_title = page.locator("div.product-name h1")
    await expect(product_title).to_be_visible(timeout=15000)
    title_text = (await product_title.inner_text()).strip()
    assert "Computing and Internet" in title_text
    print(f"Product title: {title_text}")

    price_locator = page.locator("div.product-price span[itemprop='price']").first
    await expect(price_locator).to_be_visible()
    price_val = (await price_locator.inner_text()).strip()
    assert float(price_val) > 0
    print(f"Product price: {price_val}")

    # 7. Safe target right-click and double-click actions
    print("Step 7: Performing safe right-click and double-click...")
    # Right-click on header logo
    logo = page.locator("div.header-logo a")
    await logo.click(button="right")

    # Double-click on quantity input
    qty_input = page.locator("input.qty-input").first
    await qty_input.dblclick()

    # 8. Check hidden/collapsed element before and after revealing it
    print("Step 8: Testing hidden/collapsed notification bar...")
    notification_bar = page.locator("#bar-notification")
    # Assert it is initially hidden or empty
    await expect(notification_bar).not_to_be_visible()

    # 9. Add product to cart and verify confirmation / cart count
    print("Step 9: Adding product to cart...")
    add_to_cart_btn = page.locator("input[id^='add-to-cart-button-']").first
    await expect(add_to_cart_btn).to_be_visible()
    await add_to_cart_btn.click()

    # Bar notification is revealed through interaction
    await expect(notification_bar).to_be_visible(timeout=10000)
    await expect(notification_bar).to_contain_text("The product has been added")

    # Verify cart count update in the header
    cart_qty = page.locator("span.cart-qty")
    await expect(cart_qty).not_to_have_text("(0)", timeout=10000)
    print(f"Updated Cart Count: {await cart_qty.inner_text()}")

    # 10. Open Cart page and stop before checkout
    print("Step 10: Navigating to cart and asserting contents (stopping before checkout)...")
    cart_link = page.locator("a.ico-cart").first
    await cart_link.click()

    await expect(page).to_have_url("https://demowebshop.tricentis.com/cart")
    await expect(page.locator("table.cart")).to_be_visible()
    await expect(page.locator("table.cart")).to_contain_text("Computing and Internet")
    print("Test passed successfully without proceeding to checkout.")