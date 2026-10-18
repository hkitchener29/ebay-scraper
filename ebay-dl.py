import argparse
import csv
import json
import re
import time
from pathlib import Path

import requests
from bs4 import BeautifulSoup

BASE_URL = "https://www.ebay.com/sch/i.html"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
}
NUM_PAGES = 10


# ---------------------------------------------------------------------------
# Getting HTML (two sources, same output: an HTML string)
# ---------------------------------------------------------------------------
def fetch_page(term, page):
    """Download one page of live results."""
    params = {"_nkw": term, "_pgn": page}
    response = requests.get(BASE_URL, params=params, headers=HEADERS, timeout=30)
    response.raise_for_status()
    return response.text


def read_page(pages_dir, page):
    """Read page-N.html from a folder as UTF-8."""
    path = Path(pages_dir) / f"page-{page}.html"
    return path.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Extracting data (takes an HTML string, knows nothing about where it came from)
# ---------------------------------------------------------------------------
MONEY_RE = re.compile(r"\$\s*([\d,]+)(?:\.(\d{1,2}))?")


def money_to_cents(text):
    match = MONEY_RE.search(text)  # first dollar amount only
    if not match:
        return None
    dollars = int(match.group(1).replace(",", ""))
    cents = int((match.group(2) or "0").ljust(2, "0"))
    return dollars * 100 + cents


def clean(text):
    return re.sub(r"\s+", " ", text).strip()


def parse_name(card):
    tag = card.select_one(".s-item__title, .s-card__title")
    if tag is None:
        return None
    name = clean(tag.get_text(" "))
    name = re.sub(r"^New Listing\s*", "", name)
    name = re.sub(r"\s*Opens in a new window or tab$", "", name)
    return name or None


def parse_price(card):
    tag = card.select_one(".s-item__price, .s-card__price")
    return money_to_cents(tag.get_text(" ")) if tag else None


def parse_status(card):
    tag = card.select_one(".SECONDARY_INFO, .s-card__subtitle")
    if tag is None:
        return None
    return clean(re.split(r"[·|]", tag.get_text(" "))[0]) or None


def parse_shipping(text):
    """0 if free, cents if a cost is listed, None if nothing is listed."""
    if re.search(r"free\s+(delivery|shipping)", text, re.IGNORECASE):
        return 0
    match = re.search(r"\+?\s*(\$\s*[\d,]+(?:\.\d{1,2})?)\s*(delivery|shipping)",
                      text, re.IGNORECASE)
    if match:
        return money_to_cents(match.group(1))
    return None


def parse_free_returns(text):
    return bool(re.search(r"free returns", text, re.IGNORECASE))


def parse_items_sold(text):
    """Number sold, or None if the listing doesn't say."""
    match = re.search(r"([\d,]+)\+?\s+sold", text, re.IGNORECASE)
    return int(match.group(1).replace(",", "")) if match else None


def parse_card(card):
    """Build one listing dict. Missing fields stay in the dict as None."""
    name = parse_name(card)
    if name is None or name.lower() == "shop on ebay":
        return None  # not a real listing

    text = clean(card.get_text(" "))
    return {
        "name": name,
        "price": parse_price(card),
        "status": parse_status(card),
        "shipping": parse_shipping(text),
        "free_returns": parse_free_returns(text),
        "items_sold": parse_items_sold(text),
    }


def extract_items(html):
    """Take an HTML string, return a list of listing dictionaries."""
    soup = BeautifulSoup(html, "html.parser")
    items = []
    for card in soup.select("li.s-item, li.s-card"):
        item = parse_card(card)
        if item is not None:
            items.append(item)
    return items


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="Scrape eBay search results.")
    parser.add_argument("search_term", nargs="?", help="the search term")
    parser.add_argument("--search", help="the search term (alternative form)")
    parser.add_argument(
        "--pages-dir",
        help="read page-1.html ... page-10.html from this folder "
             "instead of downloading",
    )
    parser.add_argument(
        "--csv",
        action="store_true",
        help="save the output as CSV instead of JSON",
    )
    args = parser.parse_args()

    term = args.search or args.search_term
    if not term:
        parser.error("please give a search term")

    items = []
    for page in range(1, NUM_PAGES + 1):
        if args.pages_dir:
            html = read_page(args.pages_dir, page)
        else:
            html = fetch_page(term, page)
            time.sleep(1)  # be polite to the server
        items.extend(extract_items(html))
        print(f"Page {page}: {len(items)} items so far")

    if args.csv:
        filename = f"{term}.csv"
        fieldnames = ["name", "price", "status", "shipping",
                      "free_returns", "items_sold"]
        # newline="" stops Python from adding blank lines between rows
        with open(filename, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(items)  # None is written as an empty cell
    else:
        filename = f"{term}.json"
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(items, f, indent=2, ensure_ascii=False)
    print(f"Saved {len(items)} items to {filename}")


if __name__ == "__main__":
    main()