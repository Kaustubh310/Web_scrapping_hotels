import os
from datetime import datetime

import pandas as pd
import requests
from dotenv import load_dotenv


load_dotenv()


INPUT_FILE = "ratebotai_pushkar_campaign.xlsx"
OUTPUT_FILE = "ratebotai_pushkar_campaign.xlsx"

# Start small
SEND_LIMIT = 25

# Your Cloudflare Worker
WORKER_URL = (
    "https://ratebotai-hotel-campaign."
    "kaustubh-bandkar.workers.dev/"
)


def is_empty(value):
    if value is None:
        return True

    if pd.isna(value):
        return True

    return not str(value).strip()


def clean_phone(phone):
    if is_empty(phone):
        return ""

    phone = str(phone).strip()

    # Remove Excel numeric formatting
    if phone.endswith(".0"):
        phone = phone[:-2]

    # Keep digits only
    phone = "".join(
        char for char in phone
        if char.isdigit()
    )

    # Indian number normalization
    if phone.startswith("0") and len(phone) == 11:
        phone = "91" + phone[1:]

    elif len(phone) == 10:
        phone = "91" + phone

    return phone


def main():

    print("=" * 70)
    print("RateBotAi WhatsApp Campaign")
    print("=" * 70)

    # --------------------------------------------------
    # Load Excel
    # --------------------------------------------------

    df = pd.read_excel(INPUT_FILE)

    print(
        f"Loaded {len(df)} leads"
    )

    # --------------------------------------------------
    # Add WhatsApp campaign columns
    # --------------------------------------------------

    campaign_columns = {
        "whatsapp_status": "Not Sent",
        "whatsapp_sent_at": "",
        "whatsapp_message_id": "",
        "whatsapp_error": "",
    }

    for column, default in campaign_columns.items():

        if column not in df.columns:
            df[column] = default

    # --------------------------------------------------
    # Find eligible leads
    # --------------------------------------------------

    eligible = []

    for index, row in df.iterrows():

        phone = row.get(
            "Phone",
            ""
        )

        status = str(
            row.get(
                "whatsapp_status",
                ""
            )
        ).strip().lower()

        # email_quality = str(
        #     row.get(
        #         "email_quality",
        #         ""
        #     )
        # ).strip().lower()

        if is_empty(phone):
            continue

        # Don't send WhatsApp twice
        if status in [
            "accepted",
            "sent",
            "delivered",
            "read",
        ]:
            continue

        # Skip invalid emails only if you want
        # to keep the campaign quality filter
        # if email_quality == "invalid":
        #     continue

        eligible.append(index)

    print(
        f"Eligible WhatsApp leads: "
        f"{len(eligible)}"
    )

    # --------------------------------------------------
    # Select batch
    # --------------------------------------------------

    selected = eligible[:SEND_LIMIT]

    print(
        f"Selected for this run: "
        f"{len(selected)}"
    )

    if not selected:

        print(
            "No eligible WhatsApp leads."
        )

        return

    # --------------------------------------------------
    # Send WhatsApp messages
    # --------------------------------------------------

    for index in selected:

        row = df.loc[index]

        property_name = str(
            row.get(
                "Property Name",
                ""
            )
        ).strip()

        raw_phone = row.get(
            "Phone",
            ""
        )

        phone = clean_phone(
            raw_phone
        )

        print()
        print("-" * 70)

        print(
            f"Property: {property_name}"
        )

        print(
            f"Phone: {phone}"
        )

        if not phone:

            print(
                "SKIPPED: Invalid phone"
            )

            df.at[
                index,
                "whatsapp_status"
            ] = "Failed"

            df.at[
                index,
                "whatsapp_error"
            ] = "Invalid phone"

            continue

        payload = {
            "phone": phone,
            "property_name": property_name,
        }

        try:

            response = requests.post(
                WORKER_URL,
                json=payload,
                timeout=30,
            )

            response_text = (
                response.text
            )

            print(
                f"Worker HTTP status: "
                f"{response.status_code}"
            )

            print(
                f"Worker response: "
                f"{response_text}"
            )

            if response.ok:

                try:
                    result = response.json()
                except Exception:
                    result = {}

                message_id = ""

                messages = result.get(
                    "messages",
                    []
                )

                if messages:

                    message_id = messages[0].get(
                        "id",
                        ""
                    )

                sent_time = (
                    datetime.now()
                    .strftime(
                        "%Y-%m-%d %H:%M:%S"
                    )
                )

                df.at[
                    index,
                    "whatsapp_status"
                ] = "Accepted"

                df.at[
                    index,
                    "whatsapp_sent_at"
                ] = sent_time

                df.at[
                    index,
                    "whatsapp_message_id"
                ] = message_id

                df.at[
                    index,
                    "whatsapp_error"
                ] = ""

                print(
                    "SUCCESS: WhatsApp accepted"
                )

            else:

                df.at[
                    index,
                    "whatsapp_status"
                ] = "Failed"

                df.at[
                    index,
                    "whatsapp_error"
                ] = response_text

                print(
                    "FAILED: Worker rejected request"
                )

        except Exception as error:

            df.at[
                index,
                "whatsapp_status"
            ] = "Failed"

            df.at[
                index,
                "whatsapp_error"
            ] = str(error)

            print(
                f"FAILED: {error}"
            )

    # --------------------------------------------------
    # Save campaign
    # --------------------------------------------------

    df.to_excel(
        OUTPUT_FILE,
        index=False,
    )

    print()
    print("=" * 70)

    print(
        "WhatsApp campaign file updated:"
    )

    print(
        OUTPUT_FILE
    )

    print("=" * 70)


if __name__ == "__main__":
    main()