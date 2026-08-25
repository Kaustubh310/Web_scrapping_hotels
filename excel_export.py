from openpyxl import Workbook
from openpyxl.styles import Font


HEADERS = [
    "Property Name",
    "Phone",
    "Website",
    "Address",
    "Rating",
    "Review Count",
    "Place ID",
    "Primary Type",
    "Chain",
    # "Booking.com",
    # "MakeMyTrip",
    # "Agoda",
    # "Expedia",
    # "Goibibo",
    # "Yatra",
    # "Cleartrip",
    # "EaseMyTrip",
    # "OTA Count",
    # "OTA Platforms",
    "Lead Score",
    "Qualification",
]


def export_to_excel(leads, filename="ratebotai_hotel_leads.xlsx"):
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Hotel Leads"

    for column, header in enumerate(HEADERS, start=1):
        cell = sheet.cell(row=1, column=column, value=header)
        cell.font = Font(bold=True)

    for row_number, lead in enumerate(leads, start=2):
        values = [
            lead.get("hotel_name"),
            lead.get("phone"),
            lead.get("website"),
            lead.get("address"),
            lead.get("rating"),
            lead.get("review_count"),
            lead.get("place_id"),
            lead.get("primary_type"),
            lead.get("chain"),

            # "YES" if lead.get("booking_com") else "NO",
            # "YES" if lead.get("makemytrip") else "NO",
            # "YES" if lead.get("agoda") else "NO",
            # "YES" if lead.get("expedia") else "NO",
            # "YES" if lead.get("goibibo") else "NO",
            # "YES" if lead.get("yatra") else "NO",
            # "YES" if lead.get("cleartrip") else "NO",
            # "YES" if lead.get("easemytrip") else "NO",

            # lead.get("ota_count"),
            # lead.get("ota_platforms"),
            lead.get("lead_score"),
            lead.get("qualification"),
        ]

        for column, value in enumerate(values, start=1):
            sheet.cell(
                row=row_number,
                column=column,
                value=value,
            )

    # Basic column widths
    widths = {
        "A": 35,
        "B": 20,
        "C": 50,
        "D": 70,
        "E": 10,
        "F": 15,
        "G": 35,
        "H": 20,
        "I": 10,
        # "J": 15,
        # "K": 15,
        # "L": 12,
        # "M": 12,
        # "N": 12,
        # "O": 12,
        # "P": 12,
        # "Q": 15,
        # "R": 12,
        # "S": 50,
        "T": 12,
        "U": 55,
    }

    for column, width in widths.items():
        sheet.column_dimensions[column].width = width

    sheet.freeze_panes = "A2"
    sheet.auto_filter.ref = sheet.dimensions

    workbook.save(filename)

    print(f"Excel file created: {filename}")