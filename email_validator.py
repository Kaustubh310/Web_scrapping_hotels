import re


FREE_EMAIL_DOMAINS = {
    "gmail.com",
    "yahoo.com",
    "hotmail.com",
    "outlook.com",
    "rediffmail.com",
    "icloud.com",
}


def is_valid_email(email):

    if not email:
        return False

    email = email.strip().lower()

    pattern = (
        r"^[A-Za-z0-9._%+-]+"
        r"@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$"
    )

    return bool(
        re.match(
            pattern,
            email,
        )
    )


def get_email_domain(email):

    if not email:
        return None

    if "@" not in email:
        return None

    return email.split(
        "@",
        1,
    )[1].lower()


def is_business_email(email):

    if not is_valid_email(email):
        return False

    domain = get_email_domain(
        email
    )

    return (
        domain
        not in FREE_EMAIL_DOMAINS
    )


def classify_email_quality(email):

    if not is_valid_email(email):
        return "Invalid"

    if is_business_email(email):
        return "Business Email"

    return "Free Email"