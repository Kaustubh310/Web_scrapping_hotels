import os
from datetime import datetime
import pandas as pd
from dotenv import load_dotenv
from email_sender import send_email
load_dotenv()

INPUT_FILE = "ratebotai_mahabaleshwar_leads_enriched.xlsx"

OUTPUT_FILE = "ratebotai_mahabaleshwar_campaign.xlsx"

# IMPORTANT:
# Start with 1.
# Increase only after manually checking the emails.
SEND_LIMIT = 9

def is_empty(value):
    if value is None:
        return True

    if pd.isna(value):
        return True

    return not str(value).strip()

def get_city(address):
    """
    Extract a readable city/location from a Google Places address.
    """

    if is_empty(address):
        return "your area"

    parts = [
        part.strip()
        for part in str(address).split(",")
        if part.strip()
    ]

    if not parts:
        return "your area"

    # Remove country
    country_names = {
        "india",
    }

    parts = [
        part
        for part in parts
        if part.lower() not in country_names
    ]

    if not parts:
        return "your area"

    # Remove PIN-code-only component
    parts = [
        part
        for part in parts
        if not part.isdigit()
    ]

    if not parts:
        return "your area"

    # For addresses such as:
    # Panchgani - Mahabaleshwar Rd,
    # Mahabaleshwar,
    # Dhangarwadi,
    # Maharashtra 412806,
    # India
    #
    # Maharashtra is the state, so prefer the
    # component before the state.

    state_names = {
        "maharashtra",
        "goa",
        "gujarat",
        "karnataka",
        "kerala",
        "madhya pradesh",
        "rajasthan",
        "delhi",
        "tamil nadu",
        "telangana",
        "andhra pradesh",
    }

    for index, part in enumerate(parts):

        if part.lower() in state_names:

            if index > 0:
                return parts[index - 1]

    # Fallback
    if len(parts) >= 2:
        return parts[-2]

    return parts[0]


def create_subject(property_name):
    return (
        f"Streamline OTA management for "
        f"{property_name}"
    )


def create_email(property_name, address):
    city = get_city(address)

    subject = create_subject(
        property_name
    )

    body = f"""Hi {property_name} Team,

I came across {property_name} while researching accommodation properties in {city}.

RateBotAi helps hotels and resorts manage OTA rates, availability and inventory from a centralized platform, reducing the need to manage multiple OTA extranets manually.

If your team is currently managing multiple OTAs, we'd be happy to give you a quick overview of how RateBotAi can simplify the process.

You can learn more about RateBotAi here:
https://ratebotai.com/

Would you be open to a short 15-minute call this week?

Regards,
RateBotAi Sales
sales@ratebotai.com

If you'd prefer not to receive further emails from us, simply reply and let us know.
"""

    return subject, body

def is_business_email(email_quality):
    return str(
        email_quality
    ).strip().lower() == "business email"


def is_free_email(email_quality):
    return str(
        email_quality
    ).strip().lower() == "free email"


def is_chain_property(value):
    return str(
        value
    ).strip().lower() == "yes"
    
def main():

    print("=" * 70)
    print("RateBotAi Email Campaign")
    print("=" * 70)

    # --------------------------------------------------
    # Load Excel
    # --------------------------------------------------

    df = pd.read_excel(
        INPUT_FILE
    )

    print(
        f"Loaded {len(df)} leads"
    )

    # --------------------------------------------------
    # Add campaign columns if missing
    # --------------------------------------------------

    campaign_columns = {
        "email_status": "Not Sent",
        "email_sent_at": "",
        "email_subject": "",
        "email_error": "",
    }

    for column, default in campaign_columns.items():

        if column not in df.columns:
            df[column] = default

    # --------------------------------------------------
    # Find eligible leads
    # --------------------------------------------------

    eligible = []

    for index, row in df.iterrows():

        email = row.get(
            "email",
            ""
        )

        if is_empty(email):
            continue

        status = str(
            row.get(
                "email_status",
                ""
            )
        ).strip().lower()

        # Never retry these automatically
        if status in {
            "sent",
            "bounced",
            "delivery failed",
            "do not contact",
        }:
            continue

        email_quality = str(
            row.get(
                "email_quality",
                ""
            )
        ).strip()

        # Never send to explicitly invalid emails
        if email_quality.lower() == "invalid":
            continue

        eligible.append({
            "index": index,
            "business_email": (
                1
                if is_business_email(email_quality)
                else 0
            ),
            "free_email": (
                1
                if is_free_email(email_quality)
                else 0
            ),
            "chain": (
                1
                if is_chain_property(
                    row.get(
                        "Chain",
                        ""
                    )
                )
                else 0
            ),
            "lead_score": (
                float(
                    row.get(
                        "Lead Score",
                        0
                    )
                )
                if pd.notna(
                    row.get(
                        "Lead Score",
                        0
                    )
                )
                else 0
            ),
        })


    # --------------------------------------------------
    # Prioritize leads
    # --------------------------------------------------

    eligible.sort(
        key=lambda lead: (
            lead["business_email"],
            -lead["chain"],
            lead["lead_score"],
        ),
        reverse=True,
    )


    eligible_indexes = [
        lead["index"]
        for lead in eligible
    ]

    print(
        f"Eligible leads: "
        f"{len(eligible_indexes)}"
    )

    # --------------------------------------------------
    # Limit sending
    # --------------------------------------------------

    selected = eligible_indexes[
        :SEND_LIMIT
    ]

    print(
        f"Selected for this run: "
        f"{len(selected)}"
    )

    if not selected:

        print(
            "No eligible leads to send."
        )

        return

    # --------------------------------------------------
    # Send
    # --------------------------------------------------

    for index in selected:

        row = df.loc[index]

        property_name = str(
            row.get(
                "Property Name",
                ""
            )
        ).strip()

        email = str(
            row.get(
                "email",
                ""
            )
        ).strip()

        address = str(
            row.get(
                "Address",
                ""
            )
        ).strip()

        print()
        print("-" * 70)

        print(
            f"Property: {property_name}"
        )

        print(
            f"Email: {email}"
        )

        subject, body = create_email(
            property_name,
            address,
        )

        print(
            f"Subject: {subject}"
        )

        try:

            send_email(
                recipient=email,
                subject=subject,
                body=body,
            )

            sent_time = (
                datetime.now()
                .strftime(
                    "%Y-%m-%d %H:%M:%S"
                )
            )

            df.at[
                index,
                "email_status"
            ] = "Sent"

            df.at[
                index,
                "email_sent_at"
            ] = sent_time

            df.at[
                index,
                "email_subject"
            ] = subject

            df.at[
                index,
                "email_error"
            ] = ""

            print(
                "SUCCESS: Email sent"
            )

        except Exception as error:

            df.at[
                index,
                "email_status"
            ] = "Failed"

            df.at[
                index,
                "email_error"
            ] = str(error)

            print(
                f"FAILED: {error}"
            )

        # --------------------------------------------
        # Save progress after every email attempt
        # --------------------------------------------

        df.to_excel(
            OUTPUT_FILE,
            index=False,
        )

    print()
    print("=" * 70)

    print(
        f"Campaign file created:"
    )

    print(
        OUTPUT_FILE
    )

    print("=" * 70)


if __name__ == "__main__":
    main()