# 🕷️ E-Commerce Product Scraper

A professional Python web scraper that extracts product data from e-commerce websites. Built with **BeautifulSoup**, **Requests**, and **Pandas**.

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)

## Features

- **Multi-page scraping** with automatic pagination
- **Configurable CSS selectors** — works with any e-commerce site
- **Multiple export formats** — CSV, Excel, JSON
- **Built-in data cleaning** — removes duplicates, validates prices
- **Rate limiting** — respects website limits with configurable delays
- **Retry logic** — automatic retries with exponential backoff
- **Detailed logging** — tracks every step of the scraping process
- **Error handling** — graceful failure with error reports

## Quick Start

### Installation

```bash
git clone https://github.com/yourusername/ecommerce-scraper.git
cd ecommerce-scraper
pip install -r requirements.txt
```

### Run Demo

```bash
python scraper.py
```

### Use with a Real Website

```python
from scraper import EcommerceScraper

# Initialize scraper
scraper = EcommerceScraper(
    base_url="https://example-shop.com",
    delay=1.5  # seconds between requests
)

# Define CSS selectors for the target website
selectors = {
    'name': '.product-title',
    'price': '.product-price',
    'rating': '.star-rating',
    'image': '.product-image img',
    'link': '.product-title a'
}

# Scrape products
products = scraper.scrape_category(
    category_url="https://example-shop.com/electronics",
    selectors=selectors,
    product_container='.product-card',
    max_pages=5
)

# Export results
scraper.export_csv('electronics.csv')
scraper.export_excel('electronics.xlsx')
scraper.export_json('electronics.json')

# View summary
print(scraper.get_summary())
```

## Output Examples

### CSV Output
| name | price | rating | category | stock | brand |
|------|-------|--------|----------|-------|-------|
| MacBook Pro 16 M3 Max | 3499.99 | 4.8 | Laptops | In Stock | Apple |
| Dell XPS 15 | 1899.99 | 4.6 | Laptops | In Stock | Dell |
| Samsung Galaxy S24 Ultra | 1299.99 | 4.7 | Smartphones | In Stock | Samsung |

### JSON Output
```json
{
  "metadata": {
    "source": "https://example-shop.com",
    "total_products": 15,
    "scraped_at": "2026-03-13T00:00:00",
    "errors": 0
  },
  "products": [...]
}
```

## Project Structure

```
ecommerce-scraper/
├── scraper.py          # Main scraper class
├── requirements.txt    # Python dependencies
├── README.md           # Documentation
└── output/             # Exported data files
    ├── products.csv
    ├── products.xlsx
    └── products.json
```

## Technologies

- **Python 3.8+**
- **BeautifulSoup4** — HTML parsing
- **Requests** — HTTP client
- **Pandas** — Data manipulation and export
- **openpyxl** — Excel export

## Author

**Talha Kiris** — Python Developer | Automation & Web Scraping

- GitHub: [@talha_kiris](https://github.com/talha_kiris)
- Fiverr: [talha_kiris](https://fiverr.com/talha_kiris)

## License

MIT License — feel free to use and modify.
