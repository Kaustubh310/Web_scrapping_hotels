import os
import requests
from dotenv import load_dotenv


load_dotenv()

API_KEY = os.getenv("GOOGLE_SEARCH_API_KEY")
CX = os.getenv("GOOGLE_SEARCH_ENGINE_ID")


if not API_KEY:
    raise ValueError(
        "GOOGLE_SEARCH_API_KEY is missing from .env"
    )

if not CX:
    raise ValueError(
        "GOOGLE_SEARCH_ENGINE_ID is missing from .env"
    )


url = "https://www.googleapis.com/customsearch/v1"


params = {
    "key": API_KEY,
    "cx": CX,

    # Test with ONE hotel only
    "q": '"Grape County Eco Resort" Nashik Booking.com',

    # Number of results
    "num": 5,

    # India
    "gl": "in",

    # English
    "hl": "en",
}


response = requests.get(
    url,
    params=params,
    timeout=30,
)


print("=" * 70)
print("Google Search API Test")
print("=" * 70)

print("Status:", response.status_code)


if response.status_code != 200:

    print("\nERROR:")
    print(response.text)

    raise SystemExit(1)


data = response.json()


print(
    "\nTotal results:",
    data.get(
        "searchInformation",
        {}
    ).get(
        "formattedTotalResults",
        "unknown",
    ),
)


items = data.get(
    "items",
    []
)


if not items:

    print("\nNo results found.")

    raise SystemExit(0)


print(
    f"\nFound {len(items)} results:\n"
)


for index, item in enumerate(
    items,
    start=1,
):

    print("-" * 70)

    print(
        f"Result #{index}"
    )

    print(
        "Title:",
        item.get(
            "title",
            "",
        ),
    )

    print(
        "URL:",
        item.get(
            "link",
            "",
        ),
    )

    print(
        "Snippet:",
        item.get(
            "snippet",
            "",
        ),
    )


print("-" * 70)