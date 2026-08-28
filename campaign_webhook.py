from flask import Flask, request, jsonify
import pandas as pd

from email_sender import send_email


app = Flask(__name__)

CAMPAIGN_FILE = "ratebotai_nashik_leads1.xlsx"


def clean_phone(phone):
    if phone is None:
        return ""

    phone = str(phone).strip()

    # Remove Excel's trailing .0 for numeric values
    if phone.endswith(".0"):
        phone = phone[:-2]

    # Keep digits only
    phone = "".join(
        char for char in phone
        if char.isdigit()
    )

    # Indian number normalization
    if phone.startswith("0") and len(phone) == 11:
        # 09615080505 -> 919615080505
        phone = "91" + phone[1:]

    elif len(phone) == 10:
        # 9615080505 -> 919615080505
        phone = "91" + phone

    elif phone.startswith("91") and len(phone) == 12:
        # Already normalized
        pass

    return phone


def find_property(phone):
    df = pd.read_excel(CAMPAIGN_FILE)

    target_phone = clean_phone(phone)

    for _, row in df.iterrows():

        excel_phone = clean_phone(
            row.get("Phone", "")
        )

        if excel_phone == target_phone:
            return str(
                row.get(
                    "Property Name",
                    "Unknown Property"
                )
            ).strip()

    return "Unknown Property"


@app.route("/campaign/call-request", methods=["POST"])
def call_request():

    data = request.get_json(silent=True) or {}

    phone = clean_phone(
        data.get("phone", "")
    )

    if not phone:

        return jsonify({
            "success": False,
            "error": "Missing phone"
        }), 400

    property_name = find_property(
        phone
    )

    print(
        f"CALL REQUESTED: "
        f"{property_name} - {phone}"
    )

    subject = (
        "RateBotAi - Hotel Requested a Call"
    )

    body = f"""Hi RateBotAi Sales,

A hotel lead has requested a call through the WhatsApp campaign.

Property:
{property_name}

WhatsApp Number:
{phone}

Response:
Schedule a Call

Please follow up with the hotel and arrange the 15-minute call.

Regards,
RateBotAi Hotel Campaign
"""

    try:

        send_email(
            recipient="sales@ratebotai.com",
            subject=subject,
            body=body,
        )

        return jsonify({
            "success": True,
            "property_name": property_name,
            "message": "Call request email sent"
        })

    except Exception as error:

        print(
            f"EMAIL ERROR: {error}"
        )

        return jsonify({
            "success": False,
            "error": str(error)
        }), 500


if __name__ == "__main__":

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=False,
    )