import re
import requests

from bs4 import BeautifulSoup
from urllib.parse import (
    urljoin,
    urlparse,
    unquote,
)
from browser_email_finder import (
    find_emails_with_browser,
)

EMAIL_REGEX = re.compile(
    r"(?<![A-Za-z0-9._%+-])"
    r"[A-Za-z0-9][A-Za-z0-9._%+-]{0,63}"
    r"@"
    r"[A-Za-z0-9]"
    r"(?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?"
    r"(?:\.[A-Za-z]{2,})+"
    r"(?![A-Za-z0-9._%+-])"
)


COMMON_CONTACT_KEYWORDS = [
    "contact",
    "contact us",
    "contact-us",
    "about",
    "about us",
    # "reservation",
    # "reservations",
    # "booking",
    # "bookings",
    "enquiry",
    "enquiries",
    "reach us",
    "get in touch",
]


COMMON_CONTACT_PATHS = [
    "/contact",
    "/contact-us",
    "/contactus",
    "/about",
    "/about-us",
    "/reservations",
    "/reservation",
    "/booking",
    "/bookings",
    "/enquiry",
    "/enquiries",
]


EMAIL_PRIORITY = {
    # Highest priority — people who can make/buy decisions
    "sales": 100,
    "revenue": 98,
    "gm": 98,
    "generalmanager": 98,
    "general.manager": 98,
    "owner": 98,
    "director": 95,

    # Reservations / booking
    "reservations": 85,
    "reservation": 85,
    "booking": 80,
    "bookings": 80,

    # General business
    "info": 65,
    "contact": 60,
    "hello": 55,
    "enquiry": 55,
    "enquiries": 55,
}

def get_email_priority(email):

    if not email:
        return 0

    local_part = (
        email
        .split("@")[0]
        .lower()
        .strip()
    )

    return EMAIL_PRIORITY.get(
        local_part,
        40,
    )
    
EXCLUDED_EMAIL_DOMAINS = {
    # Website / hosting infrastructure
    "sentry.wixpress.com",
    "sentry-next.wixpress.com",
    "wixpress.com",

    # Common technical / infrastructure domains
    "example.com",
    "example.org",
    "example.net",

    # Add more here if we encounter them
}

def normalize_website(url):

    if not url:
        return None

    url = str(url).strip()

    if not url:
        return None

    if not url.startswith(
        ("http://", "https://")
    ):
        url = "https://" + url

    return url.rstrip("/")


def clean_email(email):

    if not email:
        return None

    email = unquote(
        email
    )

    email = email.strip()

    email = email.lower()

    # Remove common trailing characters
    email = email.strip(
        ".,;:()[]{}<>\"'"
    )

    return email

def is_real_email(email):

    if not email:
        return False

    email = email.strip().lower()

    if "@" not in email:
        return False

    local_part, domain = email.rsplit(
        "@",
        1,
    )

    if not local_part:
        return False

    if len(local_part) > 64:
        return False

    if not domain:
        return False

    if "." not in domain:
        return False

    if " " in domain:
        return False

    # ----------------------------------------
    # Reject technical/infrastructure domains
    # ----------------------------------------

    if domain in EXCLUDED_EMAIL_DOMAINS:
        return False

    technical_prefixes = [
        "sentry.",
        "wixpress.",
        "cloudflare.",
        "vercel.",
        "netlify.",
        "amazonaws.",
        "googleusercontent.",
    ]

    for prefix in technical_prefixes:

        if domain.startswith(prefix):
            return False

    # ----------------------------------------
    # Reject fake filename-like domains
    # ----------------------------------------

    fake_extensions = {
        ".php",
        ".html",
        ".htm",
        ".aspx",
        ".jsp",
        ".js",
        ".css",
    }

    for extension in fake_extensions:

        if domain.endswith(extension):
            return False

    return True

def extract_emails_from_text(text):

    if not text:
        return []

    emails = []

    matches = EMAIL_REGEX.findall(
        text
    )

    for email in matches:

        email = clean_email(
            email
        )

        if not email:
            continue

        if not is_real_email(
            email
        ):
            continue

        if email not in emails:
            emails.append(
                email
            )

    # Obfuscated emails
    obfuscated_pattern = re.compile(
        r"([A-Za-z0-9._%+-]+)"
        r"\s*(?:\[at\]|\(at\)|\bat\b)"
        r"\s*"
        r"([A-Za-z0-9.-]+\.[A-Za-z]{2,})",
        re.IGNORECASE,
    )

    for match in obfuscated_pattern.findall(
        text
    ):

        email = (
            f"{match[0]}@{match[1]}"
        )

        email = clean_email(
            email
        )

        if not email:
            continue

        if not is_real_email(
            email
        ):
            continue

        if email not in emails:
            emails.append(
                email
            )

    return emails


def extract_emails_from_html(html):

    if not html:
        return []

    emails = []

    matches = EMAIL_REGEX.findall(
        html
    )

    for email in matches:

        email = clean_email(
            email
        )

        if not email:
            continue

        if not is_real_email(
            email
        ):
            continue

        if email not in emails:
            emails.append(
                email
            )

    # --------------------------------------------------------
    # mailto links
    # --------------------------------------------------------

    soup = BeautifulSoup(
        html,
        "html.parser",
    )

    for anchor in soup.find_all(
        "a",
        href=True,
    ):

        href = anchor.get(
            "href",
            "",
        ).strip()
        
        if href.lower().startswith(
            "mailto:"
        ):

            email = href[7:].split(
                "?",
                1,
            )[0]

            email = clean_email(
                email
            )

            if not email:
                continue

            if not is_real_email(
                email
            ):
                continue

            if email not in emails:
                emails.append(
                    email
                )

    return emails


def fetch_page(url):

    headers = {
        "User-Agent": (
            "Mozilla/5.0 "
            "(Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 "
            "(KHTML, like Gecko) "
            "Chrome/151.0.0.0 "
            "Safari/537.36"
        ),

        "Accept": (
            "text/html,"
            "application/xhtml+xml,"
            "application/xml;q=0.9,"
            "image/avif,"
            "image/webp,"
            "*/*;q=0.8"
        ),

        "Accept-Language":
            "en-US,en;q=0.9",
    }

    try:

        response = requests.get(
            url,
            headers=headers,
            timeout=20,
            allow_redirects=True,
        )

        if response.status_code != 200:

            print(
                f"    HTTP "
                f"{response.status_code}: "
                f"{url}"
            )

            return None, url

        content_type = (
            response.headers
            .get(
                "Content-Type",
                "",
            )
            .lower()
        )

        if (
            "text/html"
            not in content_type
        ):

            return None, response.url

        return (
            response.text,
            response.url,
        )

    except requests.RequestException as error:

        print(
            f"    Request failed: "
            f"{error}"
        )

        return None, url


def find_contact_links(
    base_url,
    html,
):

    if not html:
        return []

    soup = BeautifulSoup(
        html,
        "html.parser",
    )

    links = []

    for anchor in soup.find_all(
        "a",
        href=True,
    ):

        href = anchor.get(
            "href",
            "",
        ).strip()

        if not href:
            continue

        text = anchor.get_text(
            " ",
            strip=True,
        ).lower()

        href_lower = href.lower()

        combined = (
            f"{text} {href_lower}"
        )

        if any(
            keyword in combined
            for keyword
            in COMMON_CONTACT_KEYWORDS
        ):

            absolute_url = urljoin(
                base_url,
                href,
            )

            if (
                absolute_url
                not in links
            ):
                links.append(
                    absolute_url
                )

    return links


def classify_email(email):

    if not email:
        return "Unknown"

    local_part = (
        email
        .split("@")[0]
        .lower()
        .strip()
    )

    if local_part in {
        "sales",
        "revenue",
        "gm",
        "generalmanager",
        "general.manager",
        "owner",
        "director",
    }:
        return "Business Decision Maker"

    if local_part in {
        "reservations",
        "reservation",
        "booking",
        "bookings",
    }:
        return "Reservations"

    if local_part in {
        "info",
        "contact",
        "hello",
        "enquiry",
        "enquiries",
    }:
        return "Generic Business"

    return "Business Contact"


def find_emails_from_website(
    website
):

    website = normalize_website(
        website
    )

    if not website:

        return {
            "emails": [],
            "primary_email": None,
            "email_type": None,
            "source_url": None,
        }

    print(
        f"    Website: {website}"
    )

    emails = []

    pages_checked = []

    # ========================================================
    # STEP 1 — Homepage
    # ========================================================

    html, final_url = fetch_page(
        website
    )

    if html:

        pages_checked.append(
            final_url
        )

        homepage_emails = (
            extract_emails_from_html(
                html
            )
        )

        if homepage_emails:

            print(
                f"    Found on homepage: "
                f"{homepage_emails}"
            )

        emails.extend(
            homepage_emails
        )

        contact_links = (
            find_contact_links(
                final_url,
                html,
            )
        )

    else:

        contact_links = []

    # ========================================================
    # STEP 2 — Add standard contact URLs
    # ========================================================

    parsed = urlparse(
        final_url
        if final_url
        else website
    )

    base_url = (
        f"{parsed.scheme}://"
        f"{parsed.netloc}"
    )

    for path in COMMON_CONTACT_PATHS:

        url = (
            base_url.rstrip("/")
            + path
        )

        if url not in contact_links:

            contact_links.append(
                url
            )

    # ========================================================
    # STEP 3 — Crawl contact-related pages
    # ========================================================

    for url in contact_links:

        if len(pages_checked) >= 10:
            break

        if url in pages_checked:
            continue

        print(
            f"    Checking: {url}"
        )

        html, final_url = fetch_page(
            url
        )

        if not html:
            continue

        pages_checked.append(
            final_url
        )

        page_emails = (
            extract_emails_from_html(
                html
            )
        )

        if page_emails:

            print(
                f"    Found: "
                f"{page_emails}"
            )

        for email in page_emails:

            if email not in emails:

                emails.append(
                    email
                )

        # ------------------------------------------------
        # Stop once we have a useful business email
        # ------------------------------------------------

        if emails:

            has_priority_email = any(
                get_email_priority(email) >= 80
                for email in emails
            )

            if has_priority_email:
                break

    # ========================================================
    # STEP 4 — Select primary email
    # ========================================================

    if not emails:

        print(
            "    Requests found no email."
        )

        print(
            "    Trying browser..."
        )

        browser_emails = (
            find_emails_with_browser(
                website
            )
        )

        for email in browser_emails:

            email = clean_email(
                email
            )

            if (
                email
                and email not in emails
            ):
                emails.append(
                    email
                )

    # Prefer generic business emails
    generic_emails = [
        email
        for email in emails
        if classify_email(email)
        == "Generic Business"
    ]

    primary_email = max(
        emails,
        key=get_email_priority,
    )

    source_url = None

    # We already know which pages produced emails
    # from the crawling process. To keep this version
    # simple, use the first page that contains the email.
    for url in pages_checked:

        html, _ = fetch_page(
            url
        )

        if html and (
            primary_email
            in html.lower()
        ):

            source_url = url

            break

    print(
        f"    PRIMARY EMAIL: "
        f"{primary_email}"
    )

    return {
        "emails": emails,
        "primary_email": primary_email,
        "email_type": classify_email(
            primary_email
        ),
        "source_url": source_url,
    }