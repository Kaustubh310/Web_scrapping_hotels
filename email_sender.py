import os
import smtplib

from email.message import EmailMessage
from dotenv import load_dotenv


load_dotenv()


SMTP_HOST = os.getenv("SMTP_HOST")
SMTP_PORT = int(
    os.getenv(
        "SMTP_PORT",
        "587",
    )
)

SMTP_USERNAME = os.getenv(
    "SMTP_USERNAME"
)

SMTP_PASSWORD = os.getenv(
    "SMTP_PASSWORD"
)

SENDER_NAME = os.getenv(
    "SENDER_NAME",
    "RateBotAi",
)

SENDER_EMAIL = os.getenv(
    "SENDER_EMAIL"
)


def validate_config():

    required = {
        "SMTP_HOST": SMTP_HOST,
        "SMTP_USERNAME": SMTP_USERNAME,
        "SMTP_PASSWORD": SMTP_PASSWORD,
        "SENDER_EMAIL": SENDER_EMAIL,
    }

    missing = [
        key
        for key, value in required.items()
        if not value
    ]

    if missing:

        raise ValueError(
            "Missing .env values: "
            + ", ".join(missing)
        )


def send_email(
    recipient,
    subject,
    body,
):

    validate_config()

    message = EmailMessage()

    message["From"] = (
        f"{SENDER_NAME} "
        f"<{SENDER_EMAIL}>"
    )

    message["To"] = recipient
    
    message["Bcc"] = SENDER_EMAIL

    message["Subject"] = subject

    message.set_content(
        body
    )

    with smtplib.SMTP_SSL(
        SMTP_HOST,
        SMTP_PORT,
        timeout=30,
    ) as server:

        server.login(
            SMTP_USERNAME,
            SMTP_PASSWORD,
        )

        server.send_message(
            message
        )

    return True