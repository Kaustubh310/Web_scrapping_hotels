import pandas as pd

from email_finder import (
    find_emails_from_website,
)

from email_validator import (
    classify_email_quality,
)


def find_column(
    df,
    possible_names,
):

    normalized_columns = {
        str(column).strip().lower(): column
        for column in df.columns
    }

    for name in possible_names:

        key = (
            name
            .strip()
            .lower()
        )

        if key in normalized_columns:

            return normalized_columns[
                key
            ]

    return None


def enrich_lead(
    row,
    hotel_column,
    website_column,
):

    hotel_name = row.get(
        hotel_column,
        "",
    )

    website = row.get(
        website_column,
        "",
    )

    hotel_name = (
        str(hotel_name)
        if pd.notna(hotel_name)
        else ""
    )

    website = (
        str(website)
        if pd.notna(website)
        else ""
    )

    print(
        f"  Searching email: "
        f"{hotel_name}"
    )

    if not website:

        print(
            "    No website available"
        )

        row["email"] = ""
        row["email_type"] = ""
        row["email_quality"] = ""
        row["email_source"] = ""
        row["all_emails"] = ""

        return row

    result = find_emails_from_website(
        website
    )

    primary_email = result.get(
        "primary_email"
    )

    email_type = result.get(
        "email_type"
    )

    source_url = result.get(
        "source_url"
    )

    email_quality = (
        classify_email_quality(
            primary_email
        )
    )

    row["email"] = (
        primary_email
        or ""
    )

    row["email_type"] = (
        email_type
        or ""
    )

    row["email_quality"] = (
        email_quality
    )

    row["email_source"] = (
        source_url
        or ""
    )

    row["all_emails"] = ", ".join(
        result.get(
            "emails",
            [],
        )
    )

    return row


def enrich_excel(
    input_file,
    output_file,
):

    df = pd.read_excel(
        input_file
    )

    print(
        f"Loaded {len(df)} leads"
    )

    print(
        "\nExcel columns:"
    )

    for column in df.columns:

        print(
            f"  - {column}"
        )

    # --------------------------------------------------------
    # Find columns
    # --------------------------------------------------------

    hotel_column = find_column(
        df,
        [
            "hotel_name",
            "hotel name",
            "name",
            "property_name",
            "property name",
        ],
    )

    website_column = find_column(
        df,
        [
            "website",
            "website_url",
            "website url",
            "url",
        ],
    )

    # --------------------------------------------------------
    # Validate
    # --------------------------------------------------------

    if not hotel_column:

        raise ValueError(
            "Could not find hotel name column."
        )

    if not website_column:

        raise ValueError(
            "Could not find website column."
        )

    print(
        f"\nHotel column: "
        f"{hotel_column}"
    )

    print(
        f"Website column: "
        f"{website_column}"
    )

    # --------------------------------------------------------
    # Process
    # --------------------------------------------------------

    enriched_rows = []

    for _, row in df.iterrows():

        row_dict = row.to_dict()

        try:

            enriched = enrich_lead(
                row_dict,
                hotel_column,
                website_column,
            )

            enriched_rows.append(
                enriched
            )

        except Exception as error:

            print(
                f"    Error: {error}"
            )

            row_dict["email"] = ""
            row_dict["email_type"] = ""
            row_dict["email_quality"] = ""
            row_dict["email_source"] = ""
            row_dict["all_emails"] = ""

            enriched_rows.append(
                row_dict
            )

    result_df = pd.DataFrame(
        enriched_rows
    )

    result_df.to_excel(
        output_file,
        index=False,
    )

    email_count = (
        result_df["email"]
        .astype(str)
        .str.strip()
        .ne("")
        .sum()
    )

    print(
        "\n"
        + "=" * 70
    )

    print(
        "Excel created:"
    )

    print(
        output_file
    )

    print(
        f"Emails found: "
        f"{email_count}"
    )

    print(
        "=" * 70
    )