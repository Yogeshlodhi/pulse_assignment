import argparse
import json
import os
from datetime import datetime
from scrapers.g2 import scrape_g2

from scrapers.capterra import scrape_capterra

def parse_args():
    parser = argparse.ArgumentParser(description="Scrape reviews from G2/Capterra")
    
    parser.add_argument(
        "--company",
        required=True,
        help=(
            "Company slug or name:\n"
            "  - For G2: just the company name (e.g., 'slack')\n"
            "  - For Capterra: full slug like '135003/slack' (from the URL)"
        )
    )
    
    parser.add_argument("--start_date", required=True, help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end_date", required=True, help="End date (YYYY-MM-DD)")
    parser.add_argument("--source", required=True, choices=["g2", "capterra"], help="Review source")
    return parser.parse_args()

def main():
    args = parse_args()
    start_date = datetime.strptime(args.start_date, "%Y-%m-%d")
    end_date = datetime.strptime(args.end_date, "%Y-%m-%d")


    if args.source == "g2":
        reviews = scrape_g2(args.company.lower(), start_date, end_date)
    elif args.source == "capterra":
        reviews = scrape_capterra(args.company.lower(), start_date, end_date)
    else:
        print("Unsupported source")
        return

    if not os.path.exists("output"):
        os.makedirs("output")

    safe_company = args.company.lower().replace("/", "-")
    
    file_name = f"output/{safe_company}_{args.source}_reviews.json"
    with open(file_name, "w", encoding="utf-8") as f:
        json.dump(reviews, f, indent=2, ensure_ascii=False)

    print(f"Saved {len(reviews)} reviews to {file_name}")

if __name__ == "__main__":
    main()
