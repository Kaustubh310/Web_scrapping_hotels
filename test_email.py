from email_finder import (
    find_emails_from_website,
)


website = "http://www.forestcounty.co.in/"


result = find_emails_from_website(
    website
)


print("\n")
print("=" * 70)
print("RESULT")
print("=" * 70)

print(
    "Emails:",
    result["emails"]
)

print(
    "Primary:",
    result["primary_email"]
)

print(
    "Type:",
    result["email_type"]
)

print(
    "Source:",
    result["source_url"]
)