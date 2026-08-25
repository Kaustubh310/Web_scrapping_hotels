import re

from playwright.sync_api import (
    sync_playwright,
)


EMAIL_REGEX = re.compile(
    r"[A-Za-z0-9._%+-]+"
    r"@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"
)


def find_emails_with_browser(
    url,
):

    print(
        f"    Browser scan: {url}"
    )

    try:

        with sync_playwright() as p:

            browser = p.chromium.launch(
                headless=True
            )

            page = browser.new_page(
                user_agent=(
                    "Mozilla/5.0 "
                    "(Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 "
                    "(KHTML, like Gecko) "
                    "Chrome/151.0.0.0 "
                    "Safari/537.36"
                )
            )

            page.goto(
                url,
                wait_until="networkidle",
                timeout=30000,
            )

            # Give JS a little time
            page.wait_for_timeout(
                2000
            )

            html = page.content()

            emails = set(
                EMAIL_REGEX.findall(
                    html
                )
            )

            # Check mailto links
            links = page.locator(
                'a[href^="mailto:"]'
            )

            count = links.count()

            for i in range(count):

                href = links.nth(i).get_attribute(
                    "href"
                )

                if href:

                    email = href[
                        7:
                    ].split(
                        "?",
                        1,
                    )[0]

                    emails.add(
                        email.lower().strip()
                    )

            browser.close()

            emails = sorted(
                emails
            )

            if emails:

                print(
                    f"    Browser found: "
                    f"{emails}"
                )

            return emails

    except Exception as error:

        print(
            f"    Browser failed: "
            f"{error}"
        )

        return []