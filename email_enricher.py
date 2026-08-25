from lead_enrichment import (
    enrich_excel,
)


INPUT_FILE = (
    "ratebotai_mahabaleshwar_leads2.xlsx"
)


OUTPUT_FILE = (
    "ratebotai_mahabaleshwar_leads_enriched.xlsx"
)


if __name__ == "__main__":

    enrich_excel(
        input_file=INPUT_FILE,
        output_file=OUTPUT_FILE,
    )