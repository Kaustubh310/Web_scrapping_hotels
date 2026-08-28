import os
import math
import requests

from dotenv import load_dotenv

from filters import (
    is_excluded,
    is_accommodation,
    is_chain,
    has_phone,
    calculate_lead_score,
)

from excel_export import export_to_excel


# ============================================================
# CONFIGURATION
# ============================================================

load_dotenv()

API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")

if not API_KEY:
    raise ValueError(
        "GOOGLE_MAPS_API_KEY not found in .env"
    )


# ------------------------------------------------------------
# CITY CONFIGURATION
# ------------------------------------------------------------
# For now you only need to change these values.
# Later we can make this a command-line argument.
# ------------------------------------------------------------

CITY = "Pushkar"
STATE = "Rajasthan"
COUNTRY = "India"


# Nashik approximate center
CITY_LATITUDE = 26.49022
CITY_LONGITUDE = 74.55211


# ------------------------------------------------------------
# SEARCH CONFIGURATION
# ------------------------------------------------------------

# Search radius for each grid point.
#
# 7 km gives good coverage without making the circles
# excessively large.
#
SEARCH_RADIUS_METERS = 7000


# Distance between search points.
#
# Slightly larger than the radius would create gaps.
# Using approximately the same distance gives overlap.
#
GRID_STEP_KM = 8


# Number of grid points in each direction.
#
# 3 means:
#
#       ● ● ●
#       ● ● ●
#       ● ● ●
#
# Total = 9 search areas
#
GRID_SIZE = 3


# Accommodation types we want.
#
# We intentionally don't search only "hotel".
# Resorts, B&Bs and guest houses can also be
# potential Channel Manager customers.
#
INCLUDED_TYPES = [
    "hotel",
    "resort_hotel",
    "bed_and_breakfast",
    "guest_house",
]


# ============================================================
# GOOGLE PLACES API
# ============================================================

URL = (
    "https://places.googleapis.com/v1/"
    "places:searchNearby"
)


HEADERS = {
    "Content-Type": "application/json",

    "X-Goog-Api-Key": API_KEY,

    "X-Goog-FieldMask": (
        "places.id,"
        "places.displayName,"
        "places.formattedAddress,"
        "places.nationalPhoneNumber,"
        "places.websiteUri,"
        "places.rating,"
        "places.userRatingCount,"
        "places.primaryType,"
        "places.location"
    ),
}


# ============================================================
# GRID GENERATION
# ============================================================

def km_to_latitude(km):
    """
    Convert kilometres to approximate latitude degrees.
    """

    return km / 111.0


def km_to_longitude(km, latitude):
    """
    Convert kilometres to approximate longitude degrees.
    """

    latitude_radians = math.radians(latitude)

    return km / (
        111.0 * math.cos(latitude_radians)
    )


def generate_search_grid(
    center_lat,
    center_lng,
):
    """
    Generate a grid of search points around the city center.
    """

    grid = []

    half = GRID_SIZE // 2

    for row in range(
        -half,
        half + 1,
    ):

        for column in range(
            -half,
            half + 1,
        ):

            lat_offset = (
                row
                * km_to_latitude(
                    GRID_STEP_KM
                )
            )

            lng_offset = (
                column
                * km_to_longitude(
                    GRID_STEP_KM,
                    center_lat,
                )
            )

            lat = (
                center_lat
                + lat_offset
            )

            lng = (
                center_lng
                + lng_offset
            )

            grid.append(
                {
                    "latitude": lat,
                    "longitude": lng,
                }
            )

    return grid


# ============================================================
# NEARBY SEARCH
# ============================================================

def search_nearby(
    latitude,
    longitude,
):
    """
    Search for accommodation businesses
    around one geographic point.
    """

    payload = {
        "includedTypes": INCLUDED_TYPES,

        "maxResultCount": 20,

        "locationRestriction": {
            "circle": {
                "center": {
                    "latitude": latitude,
                    "longitude": longitude,
                },

                "radius": SEARCH_RADIUS_METERS,
            }
        },
    }

    response = requests.post(
        URL,
        headers=HEADERS,
        json=payload,
        timeout=30,
    )

    response.raise_for_status()

    return response.json().get(
        "places",
        []
    )


# ============================================================
# PROCESS PLACE
# ============================================================

def process_place(
    place,
    seen_place_ids,
):

    place_id = place.get("id")

    if not place_id:
        return None

    # --------------------------------------------------------
    # DEDUPLICATION
    # --------------------------------------------------------

    if place_id in seen_place_ids:
        return None

    seen_place_ids.add(place_id)

    # --------------------------------------------------------
    # BASIC INFORMATION
    # --------------------------------------------------------

    name = (
        place.get(
            "displayName",
            {},
        )
        .get(
            "text",
            "",
        )
        .strip()
    )

    address = place.get(
        "formattedAddress",
        "",
    )

    phone = place.get(
        "nationalPhoneNumber"
    )

    website = place.get(
        "websiteUri"
    )

    rating = place.get(
        "rating"
    )

    review_count = place.get(
        "userRatingCount"
    )

    primary_type = place.get(
        "primaryType"
    )

    # --------------------------------------------------------
    # REMOVE IRRELEVANT BUSINESSES
    # --------------------------------------------------------

    if is_excluded(
        name=name,
        address=address,
        primary_type=primary_type,
        website=website,
    ):
        return None

    # --------------------------------------------------------
    # ACCOMMODATION CHECK
    # --------------------------------------------------------

    if not is_accommodation(
        name=name,
        address=address,
        primary_type=primary_type,
    ):
        return None

    # --------------------------------------------------------
    # PHONE REQUIRED
    # --------------------------------------------------------

    if not has_phone(phone):
        return None

    # --------------------------------------------------------
    # CHAIN DETECTION
    # --------------------------------------------------------

    chain = is_chain(name)

    # --------------------------------------------------------
    # LEAD SCORE
    # --------------------------------------------------------

    score = calculate_lead_score(
        name=name,
        phone=phone,
        website=website,
        rating=rating,
        review_count=review_count,
        primary_type=primary_type,
    )

    # Reduce priority for known chains.
    #
    # We don't completely remove them because later you may
    # want to inspect the data.
    #
    if chain:
        score = max(
            score - 15,
            0,
        )

    # --------------------------------------------------------
    # QUALIFICATION
    # --------------------------------------------------------

    if chain:

        qualification = (
            "Chain property - lower priority"
        )

    elif rating and rating >= 4.0:

        qualification = (
            "High-priority accommodation lead"
        )

    elif rating and rating >= 3.5:

        qualification = (
            "Good accommodation lead"
        )

    else:

        qualification = (
            "Accommodation property"
        )

    # --------------------------------------------------------
    # RETURN LEAD
    # --------------------------------------------------------

    return {

        "hotel_name": name,

        "phone": phone,

        "website": website,

        "address": address,

        "city": CITY,

        "state": STATE,

        "country": COUNTRY,

        "rating": rating,

        "review_count": review_count,

        "place_id": place_id,

        "primary_type": primary_type,

        "chain": (
            "Yes"
            if chain
            else "No"
        ),

        "lead_score": score,

        "qualification": qualification,

    }


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 70)

    print(
        "RateBotAi Hotel Lead Finder"
    )

    print("=" * 70)

    print(
        f"\nCity: {CITY}"
    )

    print(
        f"State: {STATE}"
    )

    print(
        f"Country: {COUNTRY}"
    )

    print(
        f"\nSearch radius: "
        f"{SEARCH_RADIUS_METERS / 1000:.1f} km"
    )

    print(
        f"Grid size: "
        f"{GRID_SIZE} x {GRID_SIZE}"
    )

    print(
        f"Search areas: "
        f"{GRID_SIZE * GRID_SIZE}"
    )

    print(
        "\nIncluded types:"
    )

    for accommodation_type in INCLUDED_TYPES:

        print(
            f"  - {accommodation_type}"
        )

    # --------------------------------------------------------
    # GENERATE GRID
    # --------------------------------------------------------

    grid = generate_search_grid(
        CITY_LATITUDE,
        CITY_LONGITUDE,
    )

    print(
        "\nGenerated search grid:"
    )

    for index, point in enumerate(
        grid,
        start=1,
    ):

        print(
            f"  Area {index}: "
            f"{point['latitude']:.5f}, "
            f"{point['longitude']:.5f}"
        )

    # --------------------------------------------------------
    # SEARCH
    # --------------------------------------------------------

    leads = []

    seen_place_ids = set()

    for index, point in enumerate(
        grid,
        start=1,
    ):

        print(
            "\n" + "-" * 70
        )

        print(
            f"Searching area "
            f"{index}/{len(grid)}"
        )

        print(
            f"Center: "
            f"{point['latitude']:.5f}, "
            f"{point['longitude']:.5f}"
        )

        print(
            f"Radius: "
            f"{SEARCH_RADIUS_METERS / 1000:.1f} km"
        )

        try:

            places = search_nearby(
                latitude=point[
                    "latitude"
                ],
                longitude=point[
                    "longitude"
                ],
            )

        except requests.RequestException as error:

            print(
                f"Search failed: {error}"
            )

            continue

        print(
            f"Google returned "
            f"{len(places)} places"
        )

        # ----------------------------------------------------
        # PROCESS RESULTS
        # ----------------------------------------------------

        for place in places:

            lead = process_place(
                place,
                seen_place_ids,
            )

            if lead:

                leads.append(
                    lead
                )

                print(
                    f"  + Lead: "
                    f"{lead['hotel_name']}"
                )

    # --------------------------------------------------------
    # SORT
    # --------------------------------------------------------

    leads.sort(
        key=lambda x: x[
            "lead_score"
        ],
        reverse=True,
    )

    # --------------------------------------------------------
    # EXPORT
    # --------------------------------------------------------

    filename = (
        f"ratebotai_"
        f"{CITY.lower().replace(' ', '_')}"
        f"_leads2.xlsx"
    )

    export_to_excel(
        leads,
        filename=filename,
    )

    # --------------------------------------------------------
    # SUMMARY
    # --------------------------------------------------------

    print(
        "\n" + "=" * 70
    )

    print(
        f"Qualified leads: "
        f"{len(leads)}"
    )

    print(
        f"Unique places discovered: "
        f"{len(seen_place_ids)}"
    )

    print(
        f"Excel file: "
        f"{filename}"
    )

    print(
        "=" * 70
    )


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":

    main()