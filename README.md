# eBay Scraper

`ebay-dl.py` takes a search term, gets ten pages of eBay search results, extracts every listing, and saves them as a JSON file named after the search term.

## Setup

```
pip install requests beautifulsoup4
```

## Usage

Normal mode (downloads the first 10 pages of live results with `requests`):

```
python ebay-dl.py "drill press"
```

Offline mode (reads `page-1.html` through `page-10.html` from a folder, as UTF-8, instead of making requests):

```
python ebay-dl.py "garden tools" --pages-dir practice-pages
```

The search term can also be given as `--search "drill press"`.

### CSV output (`--csv`)

By default the output is JSON. Add `--csv` to save a CSV file instead; the file is then named `SEARCH_TERM.csv`:

```
python ebay-dl.py "drill press" --csv
python ebay-dl.py "garden tools" --pages-dir practice-pages --csv
```

The CSV has a header row (`name,price,status,shipping,free_returns,items_sold`) followed by one row per listing, with prices and shipping in cents. Missing values are empty cells. `--csv` can be combined with `--pages-dir`.

## Output format

The output file is `SEARCH_TERM.json`, a list of dictionaries with these keys:

| Key | Type | Meaning |
| --- | --- | --- |
| `name` | string | Name of the item |
| `price` | integer | Price in cents (if a range is listed, the first price is used) |
| `status` | string | Condition, such as `Brand New` or `Pre-Owned` |
| `shipping` | integer | Shipping cost in cents; `0` for free shipping |
| `free_returns` | boolean | Whether the item has free returns |
| `items_sold` | integer | Number of items sold |

Money is stored as integer cents, never as floats. If a listing is missing a value, the key is still present with `null` (Python `None`).

## How the code is organized

- `fetch_page(term, page)` downloads one page of live results and returns the HTML as a string.
- `read_page(pages_dir, page)` reads one saved page from a folder and returns the HTML as a string.
- `extract_items(html)` takes an HTML string (from either source) and returns a list of listing dictionaries, using Beautiful Soup.
- `main()` reads the command-line arguments, loops over pages 1 to 10, and writes the JSON file.

## Saved searches

Live eBay returned `403 Client Error: Forbidden` when I ran `python ebay-dl.py "drill press"`, so I could not download live results. **All three saved outputs below use the artificial practice data in `practice-pages`, not real eBay listings.**

Commands I ran:

```
python ebay-dl.py "drill press" --pages-dir practice-pages
python ebay-dl.py "garden tools" --pages-dir practice-pages
python ebay-dl.py "trowel" --pages-dir practice-pages
```

I also generated a CSV version of each search with the `--csv` flag:

```
python ebay-dl.py "drill press" --pages-dir practice-pages --csv
python ebay-dl.py "garden tools" --pages-dir practice-pages --csv
python ebay-dl.py "trowel" --pages-dir practice-pages --csv
```

| Output files | Search term | Data source |
| --- | --- | --- |
| `drill press.json`, `drill press.csv` | drill press | Artificial practice data |
| `garden tools.json`, `garden tools.csv` | garden tools | Artificial practice data |
| `trowel.json`, `trowel.csv` | trowel | Artificial practice data |

The files have the same contents across search terms because the practice listings are the same for every search term. Only the filenames differ, since each filename comes from the term given on the command line.

## Assignment

This project follows the instructions here: [Project 2: Web Scraping](https://csci40.rtealwitter.com/projects/02_webscraping/project.html)