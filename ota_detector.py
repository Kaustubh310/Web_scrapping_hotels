import re
import requests

from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse


OTA_PLATFORMS = {
    "Booking.com": [
        "booking.com",
    ],
    "MakeMyTrip": [
        "makemytrip.com",
    ],
    "Agoda": [
        "agoda.com",
    ],
    "Expedia": [
        "expedia.com",
    ],
    "Goibibo": [
        "goibibo.com",
    ],
    "Yatra": [
        "yatra.com",
    ],
    "Cleartrip": [
        "cleartrip.com",
    ],
    "EaseMyTrip": [
        "easemytrip.com",
    ],
}


def normalize_url(url):
    """
    Make sure the URL has a scheme.
    """

    if not url:
        return None

    url = url.strip()

    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    return url


def fetch_page(url):
    """
    Download the public hotel website.
    """

    url = normalize_url(url)

    if not url:
        return ""

    headers = {
        "User-Agent": (
            "Mozilla/5.0 "
            "(X11; Linux x86_64) "
            "AppleWebKit/537.36 "
            "(KHTML, like Gecko) "
            "Chrome/151 Safari/537.36"
        )
    }

    try:
        response = requests.get(
            url,
            headers=headers,
            timeout=15,
            allow_redirects=True,
        )

        if response.status_code != 200:
            return ""

        content_type = response.headers.get(
            "Content-Type",
            "",
        ).lower()

        if "text/html" not in content_type:
            return ""

        return response.text

    except requests.RequestException:
        return ""


def extract_links(html, base_url):
    """
    Extract all links from the website.
    """

    if not html:
        return []

    soup = BeautifulSoup(
        html,
        "html.parser",
    )

    links = []

    for anchor in soup.find_all("a", href=True):

        href = anchor.get("href")

        if not href:
            continue

        absolute_url = urljoin(
            base_url,
            href,
        )

        links.append(
            absolute_url.lower()
        )

    return links


def detect_otas(website):
    """
    Detect OTA platforms mentioned on the hotel's
    public website.

    Returns:
        {
            "Booking.com": True,
            ...
        }
    """

    result = {
        ota: False
        for ota in OTA_PLATFORMS
    }

    if not website:
        return result

    html = fetch_page(website)

    if not html:
        return result

    soup = BeautifulSoup(
        html,
        "html.parser",
    )

    # Visible/text content
    visible_text = soup.get_text(
        " ",
        strip=True,
    ).lower()

    # Links
    links = extract_links(
        html,
        website,
    )

    combined_content = (
        visible_text
        + " "
        + " ".join(links)
    )

    for ota, domains in OTA_PLATFORMS.items():

        for domain in domains:

            if domain in combined_content:
                result[ota] = True
                break

    return result


def get_ota_summary(ota_results):
    """
    Convert OTA dictionary into:
    - OTA count
    - comma-separated platform names
    """

    platforms = [
        ota
        for ota, found in ota_results.items()
        if found
    ]

    return len(platforms), ", ".join(platforms)