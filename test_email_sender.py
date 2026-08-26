from email_sender import send_email


TEST_EMAIL = "rohit87799@gmail.com"


subject = "RateBotAi Email Test"

body = f"""Hi  KB Team,

I came across KB  while researching accommodation properties in Mumbai .

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


try:

    send_email(
        recipient=TEST_EMAIL,
        subject=subject,
        body=body,
    )

    print("================================")
    print("Email sent successfully.")
    print("================================")

except Exception as error:

    print("================================")
    print("Email sending failed:")
    print(error)
    print("================================")