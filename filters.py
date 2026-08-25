import re


# These are businesses that are NOT useful for RateBotAi.
# We intentionally DO NOT exclude hotels, resorts, villas,
# homestays, guest houses, lodges, etc.
EXCLUDE_TERMS = [
    "restaurant",
    "restaurants",
    "cafe",
    "coffee shop",
    "bar",
    "pub",
    "bakery",

    "travel agency",
    "travel agencies",
    "tour operator",
    "tour operators",
    "travel company",

    "real estate",
    "realty",
    "property developer",
    "real estate developer",

    "wedding venue",
    "wedding hall",
    "event venue",
    "event center",
    "banquet hall",

    "hotel software",
    "hotel technology",
    "channel manager",
    "property management software",
    "pms software",

    "ota platform",
    "online travel agency",
]


# These indicate accommodation businesses.
# They are NOT exclusion terms.
ACCOMMODATION_TERMS = [
    "hotel",
    "hotels",
    "resort",
    "resorts",
    "villa",
    "villas",
    "homestay",
    "homestays",
    "guest house",
    "guesthouse",
    "lodge",
    "lodges",
    "inn",
    "heritage hotel",
    "boutique hotel",
    "boutique",
    "serviced apartment",
    "serviced apartments",
    "holiday home",
    "holiday homes",
    "holiday resort",
    "eco resort",
    "eco-resort",
    "retreat",
    "camp",
    "camping",
    "glamping",
    "cottage",
    "cottages",
]


CHAIN_TERMS = [
    "marriott",
    "hilton",
    "hyatt",
    "radisson",
    "ibis",
    "novotel",
    "accor",
    "holiday inn",
    "crowne plaza",
    "intercontinental",
    "sheraton",
    "westin",
    "le meridien",
    "four points",
    "courtyard",
    "taj ",
    "itc ",
    "lemon tree",
    "ginger hotel",
]

EXCLUDED_BRANDS = [
    # OYO
    "oyo",
    "hotel oyo",
    "oyo rooms",

    # FabHotels
    "fabhotel",
    "fab hotels",
    "fabexpress",
    "fab express",

    # StayVista
    "stayvista",
    "stay vista",

    # Treebo
    "treebo",
    "treebo hotels",

    # Bloom
    "bloom hotel",
    "bloom hotels",
    "bloom rooms",

    # Itsy
    "itsy hotels",
    "itsy hotel",

    # Ginger / Lemon Tree
    "ginger hotel",
    "ginger hotels",
    "lemon tree",

    # Other common managed/franchise brands
    "hotel surya",
]

def normalize_text(value):
    if not value:
        return ""

    return re.sub(r"\s+", " ", value.lower()).strip()


def is_excluded_brand(text):
    """
    Check if the text contains any excluded brand names.
    """
    return contains_any(text, EXCLUDED_BRANDS)


def contains_any(text, terms):
    text = normalize_text(text)

    return any(term in text for term in terms)


def is_excluded(
    name,
    address="",
    primary_type=None,
    website="",
):
    """
    Exclude non-target businesses, major chains,
    and managed/franchise accommodation brands.
    """

    combined_text = normalize_text(
        f"{name} {address} {website}"
    )

    # --------------------------------------------------------
    # Managed / aggregator brands
    # --------------------------------------------------------

    if is_excluded_brand(name):
        return True

    if website and is_excluded_brand(website):
        return True

    # --------------------------------------------------------
    # Major hotel chains
    # --------------------------------------------------------

    if is_chain(name):
        return True

    # --------------------------------------------------------
    # Primary Google business type
    # --------------------------------------------------------

    non_accommodation_types = {
        "restaurant",
        "vegetarian_restaurant",
        "cafe",
        "bar",
        "bakery",
        "meal_takeaway",
        "meal_delivery",
        "food",
        "travel_agency",
        "real_estate_agency",
        "wedding_venue",
        "event_venue",
    }

    if primary_type:

        normalized_type = normalize_text(
            primary_type
        )

        if normalized_type in non_accommodation_types:
            return True

    # --------------------------------------------------------
    # Explicit non-accommodation keywords
    #
    # Don't exclude generic words like "bar" or "banquet"
    # because hotels can contain them.
    # --------------------------------------------------------

    strong_exclusions = [
        "travel agency",
        "tour operator",
        "real estate",
        "property developer",
        "hotel software",
        "channel manager",
        "property management software",
        "ota platform",
    ]

    if contains_any(
        combined_text,
        strong_exclusions,
    ):
        return True

    return False

def is_accommodation(
    name,
    address="",
    primary_type=None,
):
    """
    Determine whether the business is genuinely an
    accommodation property.

    Google primary_type gets priority when available.
    """

    combined_text = normalize_text(
        f"{name} {address}"
    )

    accommodation_types = {
        "hotel",
        "lodging",
        "resort_hotel",
        "bed_and_breakfast",
        "guest_house",
        "motel",
    }

    # --------------------------------------------------------
    # If Google explicitly identifies it as a restaurant,
    # food business, cafe, etc., reject it.
    # --------------------------------------------------------

    non_accommodation_types = {
        "restaurant",
        "vegetarian_restaurant",
        "cafe",
        "bar",
        "bakery",
        "meal_takeaway",
        "meal_delivery",
        "food",
        "service",
    }

    if primary_type:

        normalized_type = normalize_text(
            primary_type
        )

        if normalized_type in non_accommodation_types:
            return False

        if normalized_type in accommodation_types:
            return True

    # --------------------------------------------------------
    # If Google doesn't provide a useful accommodation type,
    # fall back to the name/address.
    # --------------------------------------------------------

    if contains_any(
        combined_text,
        ACCOMMODATION_TERMS,
    ):
        return True

    return False

def is_chain(name):
    """
    Detect obvious large hotel chains.

    We don't necessarily want to delete them forever,
    but for the initial RateBotAi campaign we can mark
    them as lower priority.
    """

    text = normalize_text(name)

    return contains_any(text, CHAIN_TERMS)


def has_phone(phone):
    """
    Phone number is mandatory for V1 because the
    primary sales channel is calling.
    """

    return bool(phone and phone.strip())


def calculate_lead_score(
    name,
    phone=None,
    website=None,
    rating=None,
    review_count=None,
    primary_type=None,
):
    score = 0

    # Accommodation
    if is_accommodation(
        name=name,
        primary_type=primary_type,
    ):
        score += 20

    # Phone — extremely important
    if has_phone(phone):
        score += 20

    # Website
    if website:
        score += 10

    # Rating
    if rating:
        if rating >= 4.5:
            score += 15
        elif rating >= 4.0:
            score += 12
        elif rating >= 3.5:
            score += 8
        elif rating >= 3.0:
            score += 4

    # Reviews — deliberately capped
    if review_count:
        if review_count >= 1000:
            score += 8
        elif review_count >= 500:
            score += 7
        elif review_count >= 100:
            score += 5
        elif review_count >= 50:
            score += 3

    # Property type
    text = normalize_text(name)

    if contains_any(text, ["hotel"]):
        score += 10

    elif contains_any(text, ["resort"]):
        score += 10

    elif contains_any(text, ["boutique"]):
        score += 8

    elif contains_any(text, ["homestay"]):
        score += 6

    elif contains_any(text, ["villa"]):
        score += 6

    elif contains_any(text, ["guest house"]):
        score += 6

    elif contains_any(text, ["lodge"]):
        score += 5

    # Independent bonus
    if (
        not is_chain(name)
        and not is_excluded_brand(name)
    ):
        score += 5

    return min(score, 100)

def add_ota_score(base_score, ota_count):
    """
    Increase lead score based on the number of detected OTAs.

    Multiple OTA presence is a strong signal that the property
    could benefit from a Channel Manager.
    """

    if ota_count >= 4:
        base_score += 20

    elif ota_count == 3:
        base_score += 15

    elif ota_count == 2:
        base_score += 10

    elif ota_count == 1:
        base_score += 5

    return min(base_score, 100)