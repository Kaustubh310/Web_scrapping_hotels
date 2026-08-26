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

MAX_PAGES = 10

PAGE_PRIORITY_TERMS = {
    # Highest priority
    "contact": 100,
    "contact-us": 100,
    "contactus": 100,
    "contact-information": 100,
    "reach-us": 95,
    "get-in-touch": 95,

    # Sales / management
    "sales": 95,
    "revenue": 95,
    "management": 90,
    "team": 85,
    "owner": 85,
    "director": 85,

    # Booking
    "reservation": 90,
    "reservations": 90,
    "booking": 85,
    "bookings": 85,
    "enquiry": 80,
    "enquiries": 80,

    # About
    "about": 60,
    "about-us": 60,
}

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
    "yourdomain.com",
    "domain.com",
}

def is_high_priority_email(email):

    if not email:
        return False

    local_part = (
        email
        .split("@")[0]
        .lower()
        .strip()
    )

    return local_part in {
        "sales",
        "revenue",
        "gm",
        "generalmanager",
        "general.manager",
        "owner",
        "director",
    }
    
EXCLUDED_EMAIL_LOCALS = {
    "test",
    "testing",
    "example",
    "yourname",
    "your.name",
    "username",
    "user",
    "admin",
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

    # ----------------------------------------
    # Reject image filenames
    # ----------------------------------------

    if "@2x" in email:
        return False

    if email.endswith(
        (
            ".png",
            ".jpg",
            ".jpeg",
            ".gif",
            ".svg",
            ".webp",
        )
    ):
        return False

    # ----------------------------------------
    # Split email
    # ----------------------------------------

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

def normalize_internal_url(
    base_url,
    link,
):
    """
    Convert a discovered link into an absolute URL
    and keep only HTTP/HTTPS internal links.
    """

    if not link:
        return None

    link = link.strip()

    # Ignore mailto links
    if link.lower().startswith("mailto:"):
        return None

    # Ignore telephone links
    if link.lower().startswith("tel:"):
        return None

    # Ignore javascript links
    if link.lower().startswith("javascript:"):
        return None

    absolute_url = urljoin(
        base_url,
        link,
    )

    parsed_base = urlparse(
        base_url
    )

    parsed_url = urlparse(
        absolute_url
    )

    if parsed_url.scheme not in (
        "http",
        "https",
    ):
        return None

    # Only crawl same-domain pages
    if (
        parsed_url.netloc.lower()
        != parsed_base.netloc.lower()
    ):
        return None

    # Remove fragment
    clean_url = absolute_url.split(
        "#",
        1,
    )[0]

    return clean_url.rstrip("/")

def get_page_priority(url):
    """
    Give higher priority to pages that are more likely
    to contain business contact emails.
    """

    url_lower = url.lower()

    score = 0

    for term, priority in PAGE_PRIORITY_TERMS.items():

        if term in url_lower:
            score = max(
                score,
                priority,
            )

    return score

def find_emails_from_website(
    website
):

    if not website:

        return {
            "emails": [],
            "primary_email": None,
            "email_type": None,
            "source_url": None,
        }

    # ------------------------------------------------
    # Normalize website
    # ------------------------------------------------

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

    # ------------------------------------------------
    # Prefer HTTPS
    # ------------------------------------------------

    if website.startswith(
        "http://"
    ):

        website = (
            "https://"
            + website[len("http://"):]
        )

    website = website.rstrip("/")

    # ------------------------------------------------
    # Tracking
    # ------------------------------------------------

    pages_checked = set()

    pages_to_visit = []

    discovered_emails = set()

    email_sources = {}

    # ------------------------------------------------
    # Homepage gets highest priority
    # ------------------------------------------------

    pages_to_visit.append(
        (
            1000,
            website,
        )
    )

    # ------------------------------------------------
    # Maximum 10 pages
    # ------------------------------------------------

    while (
        pages_to_visit
        and len(pages_checked) < MAX_PAGES
    ):

        # Highest priority first
        pages_to_visit.sort(
            key=lambda item: item[0],
            reverse=True,
        )

        priority, url = (
            pages_to_visit.pop(0)
        )

        if url in pages_checked:
            continue

        pages_checked.add(url)

        print(
            f"    Checking "
            f"({len(pages_checked)}/{MAX_PAGES}): "
            f"{url}"
        )

        # ------------------------------------------------
        # Fetch page using your existing fetch_page()
        # ------------------------------------------------

        html, final_url = fetch_page(
            url
        )

        # ------------------------------------------------
        # Detect external redirects
        # ------------------------------------------------

        original_domain = (
            urlparse(website)
            .netloc
            .lower()
            .replace("www.", "")
        )

        final_domain = (
            urlparse(final_url)
            .netloc
            .lower()
            .replace("www.", "")
        )

        if (
            final_domain
            and final_domain != original_domain
        ):

            print(
                f"    Redirected externally: "
                f"{final_domain}"
            )

            print(
                "    Skipping external domain."
            )

            continue

        if not html:
            continue

        # ------------------------------------------------
        # Extract emails
        # ------------------------------------------------

        emails = (
            extract_emails_from_html(
                html
            )
        )

        if emails:

            print(
                f"    Found: {emails}"
            )

        for email in emails:

            email = clean_email(
                email
            )

            if not email:
                continue

            if not is_real_email(
                email
            ):
                continue

            if email not in discovered_emails:

                discovered_emails.add(
                    email
                )

                email_sources[
                    email
                ] = final_url

        # ------------------------------------------------
        # Discover internal links
        # ------------------------------------------------

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

            link = normalize_internal_url(
                final_url,
                href,
            )

            if not link:
                continue

            if link in pages_checked:
                continue

            # Don't queue duplicate URLs
            already_queued = any(
                item[1] == link
                for item in pages_to_visit
            )

            if already_queued:
                continue

            page_priority = (
                get_page_priority(
                    link
                )
            )

            pages_to_visit.append(
                (
                    page_priority,
                    link,
                )
            )

        # ------------------------------------------------
        # Early stop for strong business email
        # ------------------------------------------------

        if any(
            is_high_priority_email(
                email
            )
            for email in discovered_emails
        ):

            print(
                "    High-priority "
                "business email found."
            )

            break

    # ------------------------------------------------
    # Browser fallback
    # ------------------------------------------------

    if not discovered_emails:

        print(
            "    Requests found no email."
        )

        print(
            "    Trying browser..."
        )

        try:

            browser_emails = (
                find_emails_with_browser(
                    website
                )
            )

        except Exception as error:

            print(
                f"    Browser failed: "
                f"{error}"
            )

            browser_emails = []

        for email in browser_emails:

            email = clean_email(
                email
            )

            if not email:
                continue

            if not is_real_email(
                email
            ):
                continue

            discovered_emails.add(
                email
            )

            email_sources[
                email
            ] = website

    # ------------------------------------------------
    # Still nothing
    # ------------------------------------------------

    if not discovered_emails:

        print(
            "    No email found."
        )

        return {
            "emails": [],
            "primary_email": None,
            "email_type": None,
            "source_url": None,
        }

    # ------------------------------------------------
    # Select primary email
    # ------------------------------------------------

    primary_email = max(
        discovered_emails,
        key=get_email_priority,
    )

    source_url = email_sources.get(
        primary_email
    )

    email_type = classify_email(
        primary_email
    )

    print(
        f"    PRIMARY EMAIL: "
        f"{primary_email}"
    )

    return {
        "emails": sorted(
            discovered_emails
        ),
        "primary_email": primary_email,
        "email_type": email_type,
        "source_url": source_url,
    }