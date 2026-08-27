from flask import Flask, request, jsonify

from email_sender import send_email


app = Flask(__name__)


@app.route("/campaign/call-request", methods=["POST"])
def call_request():

    data = request.get_json(silent=True) or {}

    phone = data.get("phone", "").strip()
    property_name = data.get(
        "property_name",
        "Unknown Property"
    ).strip()

    if not phone:
        return jsonify({
            "success": False,
            "error": "Missing phone"
        }), 400

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

        print(
            f"CALL REQUESTED: "
            f"{property_name} - {phone}"
        )

        return jsonify({
            "success": True,
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