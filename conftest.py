import logging
import os
import shutil
from pathlib import Path

import pytest
import pytest_asyncio
from playwright.async_api import async_playwright

BASE = Path(__file__).parent
(BASE / "logs").mkdir(exist_ok=True)
(BASE / "artifacts/screenshots").mkdir(parents=True, exist_ok=True)
(BASE / "artifacts/traces").mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[
        logging.FileHandler(BASE / "logs/pytest.log"),
        logging.StreamHandler(),
    ],
    force=True,
)
logger = logging.getLogger("assignment3")


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()
    setattr(item, "rep_" + report.when, report)


@pytest_asyncio.fixture
async def browser_page(request):
    async with async_playwright() as p:
        browser_path = (
            shutil.which("google-chrome")
            or shutil.which("chromium")
            or shutil.which("chromium-browser")
        )

        options = {
            "headless": os.getenv("HEADLESS", "false").lower() == "true",
            "slow_mo": int(os.getenv("SLOW_MO", "300")),
        }

        if browser_path:
            options["executable_path"] = browser_path

        browser = await p.chromium.launch(**options)
        context = await browser.new_context(
            viewport={"width": 1440, "height": 900}
        )
        page = await context.new_page()

        await context.tracing.start(screenshots=True, snapshots=True)

        logger.info("START: %s", request.node.nodeid)

        try:
            yield page
        finally:
            report = getattr(request.node, "rep_call", None)

            if report and report.failed:
                name = request.node.name

                try:
                    await page.screenshot(
                        path=str(BASE / "artifacts/screenshots" / f"{name}.png"),
                        full_page=True,
                    )
                    await context.tracing.stop(
                        path=str(BASE / "artifacts/traces" / f"{name}.zip")
                    )
                    logger.error("Failure screenshot and trace saved")
                except Exception:
                    logger.exception("Could not save failure evidence")
            else:
                await context.tracing.stop()

            await context.close()
            await browser.close()

            logger.info("END: %s", request.node.nodeid)