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
SEND_LIMIT = 6



def is_empty(value):
    if value is None:
        return True

    if pd.isna(value):
        return True

    return not str(value).strip()


def get_city(address):
    """
    Try to get a readable location from the Google Places address.
    """

    if is_empty(address):
        return "your area"

    parts = [
        part.strip()
        for part in str(address).split(",")
        if part.strip()
    ]

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

        status = row.get(
            "email_status",
            ""
        )

        if is_empty(email):
            continue

        # Don't send twice
        if str(status).strip().lower() == "sent":
            continue

        email_quality = str(
            row.get(
                "email_quality",
                ""
            )
        ).strip()

        # Skip emails explicitly marked invalid
        if email_quality.lower() == "invalid":
            continue

        eligible.append(index)

    print(
        f"Eligible leads: {len(eligible)}"
    )

    # --------------------------------------------------
    # Limit sending
    # --------------------------------------------------

    selected = eligible[
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