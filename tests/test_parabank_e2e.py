import os
import pytest
from dotenv import load_dotenv
from playwright.async_api import expect

load_dotenv()


@pytest.mark.asyncio
async def test_parabank_account_overview(browser_page):
    page = browser_page

    # Use credentials from .env, or default to standard ParaBank demo account
    username = os.getenv("PARABANK_USERNAME", "john").strip() or "john"
    password = os.getenv("PARABANK_PASSWORD", "demo") or "demo"

    # 1. Open ParaBank and Log in with demo user
    print("Step 1: Opening ParaBank and logging in...")
    await page.goto(
        "https://parabank.parasoft.com/parabank/index.htm",
        wait_until="domcontentloaded",
        timeout=60000,
    )

    await page.locator("input[name='username']").fill(username)
    await page.locator("input[name='password']").fill(password)
    await page.locator("input[value='Log In']").click()

    # 2. Verify the account overview page
    print("Step 2: Verifying Accounts Overview...")
    overview_heading = page.locator("h1.title", has_text="Accounts Overview").first
    await expect(overview_heading).to_be_visible(timeout=15000)

    account_rows = page.locator("#accountTable tbody tr")
    await expect(account_rows.first).to_be_visible()

    # 3. Use navigation links to open account details and validate information
    print("Step 3: Opening specific account details...")
    first_account_link = page.locator("#accountTable tbody tr a").first
    account_number = (await first_account_link.inner_text()).strip()
    await first_account_link.click()

    # Validate displayed account information
    details_heading = page.locator("h1.title", has_text="Account Details").first
    await expect(details_heading).to_be_visible()
    await expect(page.locator("#accountId")).to_contain_text(account_number)

    # 4. Open Transfer Funds page and select accounts from dynamic dropdowns
    print("Step 4: Opening Transfer Funds and selecting dynamic accounts...")
    await page.locator("a", has_text="Transfer Funds").click()
    await expect(page.locator("h1.title", has_text="Transfer Funds").first).to_be_visible()

    from_account = page.locator("#fromAccountId")
    to_account = page.locator("#toAccountId")

    # Wait for dynamic dropdown options to populate
    await expect(from_account.locator("option").first).to_be_attached(timeout=15000)
    await expect(to_account.locator("option").first).to_be_attached(timeout=15000)

    # Submit a small demo transfer ($1)
    print("Step 5: Submitting $1 demo transfer...")
    await page.locator("#amount").fill("1")
    await page.locator("input[value='Transfer']").click()

    # 5. Verify the transfer result and verify account overview
    print("Step 6: Verifying transfer result and account overview...")
    transfer_result = page.locator("h1.title", has_text="Transfer Complete").first
    await expect(transfer_result).to_be_visible(timeout=15000)

    # Return to Accounts Overview to confirm state
    await page.locator("a", has_text="Accounts Overview").click()
    await expect(page.locator("#accountTable")).to_be_visible()

    # 6. Hover on navigation element (check if hover-driven menu exists)
    print("Step 7: Testing navigation hover...")
    services_link = page.locator("ul.leftmenu a", has_text="Services").first
    if await services_link.is_visible():
        await services_link.hover()
        print("Hovered on 'Services' navigation link (ParaBank uses static left menu without sub-popups).")

    # 7. Safe target right-click and double-click
    print("Step 8: Performing safe right-click and double-click...")
    # Right-click on header logo (safe, non-submitting target)
    logo = page.locator("img.logo")
    await logo.click(button="right")

    # Double-click on header title (.first avoids strict mode violation)
    overview_title = page.locator("h1.title").first
    await overview_title.dblclick()

    # 8. Test genuinely hidden element handling
    print("Step 9: Testing hidden element assertion...")
    # Once logged in, the login form/button is hidden/removed from DOM
    login_btn = page.locator("input[value='Log In']")
    await expect(login_btn).not_to_be_visible()

    # 9. Log out and verify the signed-out state
    print("Step 10: Logging out and verifying signed-out state...")
    logout_link = page.locator("a", has_text="Log Out")
    await expect(logout_link).to_be_visible()
    await logout_link.click()

    # Verify return to login page
    await expect(page.locator("input[name='username']")).to_be_visible(timeout=15000)
    print("ParaBank test completed successfully!")