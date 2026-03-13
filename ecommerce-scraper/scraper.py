"""
E-Commerce Product Scraper
Author: Talha Kiris
Description: A professional web scraper that extracts product data from e-commerce websites.
             Supports multiple output formats (CSV, Excel, JSON) and includes data cleaning.
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
import json
import csv
import time
import random
import logging
from datetime import datetime
from typing import List, Dict, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scraper.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class EcommerceScraper:
    """
    A versatile e-commerce scraper that extracts product information
    from websites using BeautifulSoup and Requests.
    
    Features:
    - Configurable delays to respect rate limits
    - Multiple output formats (CSV, Excel, JSON)
    - Built-in data cleaning and validation
    - Error handling and retry logic
    - Detailed logging
    """
    
    def __init__(self, base_url: str, delay: float = 1.5):
        """
        Initialize the scraper.
        
        Args:
            base_url: The base URL of the e-commerce website
            delay: Delay between requests in seconds (default: 1.5)
        """
        self.base_url = base_url
        self.delay = delay
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                          '(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
        })
        self.products: List[Dict] = []
        self.errors: List[Dict] = []
        logger.info(f"Scraper initialized for: {base_url}")
    
    def fetch_page(self, url: str, retries: int = 3) -> Optional[BeautifulSoup]:
        """
        Fetch a page and return parsed BeautifulSoup object.
        Includes retry logic for failed requests.
        
        Args:
            url: URL to fetch
            retries: Number of retry attempts
            
        Returns:
            BeautifulSoup object or None if failed
        """
        for attempt in range(retries):
            try:
                time.sleep(self.delay + random.uniform(0, 0.5))
                response = self.session.get(url, timeout=15)
                response.raise_for_status()
                logger.info(f"Successfully fetched: {url}")
                return BeautifulSoup(response.text, 'html.parser')
            except requests.RequestException as e:
                logger.warning(f"Attempt {attempt + 1}/{retries} failed for {url}: {e}")
                if attempt == retries - 1:
                    self.errors.append({
                        'url': url,
                        'error': str(e),
                        'timestamp': datetime.now().isoformat()
                    })
                    logger.error(f"All retries failed for: {url}")
                    return None
                time.sleep(2 ** attempt)  # Exponential backoff
    
    def parse_product(self, product_element: BeautifulSoup, selectors: Dict) -> Dict:
        """
        Parse a single product element using provided CSS selectors.
        
        Args:
            product_element: BeautifulSoup element containing product data
            selectors: Dictionary mapping field names to CSS selectors
            
        Returns:
            Dictionary containing parsed product data
        """
        product = {}
        
        for field, selector in selectors.items():
            try:
                element = product_element.select_one(selector)
                if element:
                    if field == 'image':
                        product[field] = element.get('src', '') or element.get('data-src', '')
                    elif field == 'link':
                        product[field] = element.get('href', '')
                    elif field == 'price':
                        product[field] = self.clean_price(element.get_text(strip=True))
                    elif field == 'rating':
                        product[field] = self.clean_rating(element.get_text(strip=True))
                    else:
                        product[field] = element.get_text(strip=True)
                else:
                    product[field] = None
            except Exception as e:
                logger.warning(f"Error parsing field '{field}': {e}")
                product[field] = None
        
        product['scraped_at'] = datetime.now().isoformat()
        return product
    
    def scrape_category(self, category_url: str, selectors: Dict, 
                        product_container: str, max_pages: int = 10,
                        next_page_selector: str = None) -> List[Dict]:
        """
        Scrape all products from a category with pagination support.
        
        Args:
            category_url: URL of the category page
            selectors: CSS selectors for product fields
            product_container: CSS selector for product container
            max_pages: Maximum number of pages to scrape
            next_page_selector: CSS selector for next page button
            
        Returns:
            List of product dictionaries
        """
        current_url = category_url
        page = 1
        
        while current_url and page <= max_pages:
            logger.info(f"Scraping page {page}: {current_url}")
            soup = self.fetch_page(current_url)
            
            if not soup:
                break
            
            products = soup.select(product_container)
            logger.info(f"Found {len(products)} products on page {page}")
            
            for product_elem in products:
                product_data = self.parse_product(product_elem, selectors)
                if product_data.get('name'):  # Only add if name exists
                    self.products.append(product_data)
            
            # Find next page
            if next_page_selector:
                next_button = soup.select_one(next_page_selector)
                if next_button and next_button.get('href'):
                    current_url = self.base_url + next_button['href']
                    page += 1
                else:
                    break
            else:
                break
        
        logger.info(f"Total products scraped: {len(self.products)}")
        return self.products
    
    @staticmethod
    def clean_price(price_text: str) -> float:
        """Clean and convert price text to float."""
        if not price_text:
            return 0.0
        cleaned = ''.join(c for c in price_text if c.isdigit() or c in '.,')
        cleaned = cleaned.replace(',', '.')
        try:
            return round(float(cleaned), 2)
        except ValueError:
            return 0.0
    
    @staticmethod
    def clean_rating(rating_text: str) -> float:
        """Clean and convert rating text to float."""
        if not rating_text:
            return 0.0
        cleaned = ''.join(c for c in rating_text if c.isdigit() or c in '.,')
        cleaned = cleaned.replace(',', '.')
        try:
            return round(float(cleaned), 1)
        except ValueError:
            return 0.0
    
    def clean_data(self) -> pd.DataFrame:
        """
        Clean and validate scraped data.
        
        Returns:
            Cleaned pandas DataFrame
        """
        if not self.products:
            logger.warning("No products to clean")
            return pd.DataFrame()
        
        df = pd.DataFrame(self.products)
        
        # Remove duplicates
        initial_count = len(df)
        df = df.drop_duplicates(subset=['name'], keep='first')
        removed = initial_count - len(df)
        if removed > 0:
            logger.info(f"Removed {removed} duplicate products")
        
        # Remove products without names
        df = df.dropna(subset=['name'])
        
        # Fill missing values
        if 'price' in df.columns:
            df['price'] = pd.to_numeric(df['price'], errors='coerce').fillna(0)
        if 'rating' in df.columns:
            df['rating'] = pd.to_numeric(df['rating'], errors='coerce').fillna(0)
        
        # Sort by price descending
        if 'price' in df.columns:
            df = df.sort_values('price', ascending=False)
        
        df = df.reset_index(drop=True)
        logger.info(f"Cleaned data: {len(df)} products remaining")
        return df
    
    def export_csv(self, filename: str = 'products.csv') -> str:
        """Export data to CSV format."""
        df = self.clean_data()
        df.to_csv(filename, index=False, encoding='utf-8-sig')
        logger.info(f"Data exported to CSV: {filename}")
        return filename
    
    def export_excel(self, filename: str = 'products.xlsx') -> str:
        """Export data to Excel format with formatting."""
        df = self.clean_data()
        
        with pd.ExcelWriter(filename, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Products', index=False)
            
            # Auto-adjust column widths
            worksheet = writer.sheets['Products']
            for idx, col in enumerate(df.columns):
                max_length = max(
                    df[col].astype(str).map(len).max(),
                    len(col)
                ) + 2
                worksheet.column_dimensions[chr(65 + idx)].width = min(max_length, 50)
        
        logger.info(f"Data exported to Excel: {filename}")
        return filename
    
    def export_json(self, filename: str = 'products.json') -> str:
        """Export data to JSON format."""
        df = self.clean_data()
        data = {
            'metadata': {
                'source': self.base_url,
                'total_products': len(df),
                'scraped_at': datetime.now().isoformat(),
                'errors': len(self.errors)
            },
            'products': df.to_dict('records')
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Data exported to JSON: {filename}")
        return filename
    
    def get_summary(self) -> Dict:
        """Get a summary of the scraping results."""
        df = self.clean_data()
        summary = {
            'total_products': len(df),
            'total_errors': len(self.errors),
            'source': self.base_url,
        }
        
        if 'price' in df.columns and len(df) > 0:
            summary.update({
                'avg_price': round(df['price'].mean(), 2),
                'min_price': round(df['price'].min(), 2),
                'max_price': round(df['price'].max(), 2),
            })
        
        if 'rating' in df.columns and len(df) > 0:
            summary.update({
                'avg_rating': round(df['rating'].mean(), 1),
            })
        
        return summary


# ============================================================
# DEMO: Shows how the scraper works with sample data
# ============================================================

def run_demo():
    """
    Demonstrate the scraper with sample e-commerce data.
    This simulates what the scraper does on a real website.
    """
    print("=" * 60)
    print("   E-COMMERCE PRODUCT SCRAPER - DEMO")
    print("   Author: Talha Kiris")
    print("=" * 60)
    
    # Create scraper instance
    scraper = EcommerceScraper(base_url="https://example-shop.com")
    
    # Simulated product data (in real usage, this comes from web pages)
    sample_products = [
        {"name": "MacBook Pro 16 M3 Max", "price": 3499.99, "rating": 4.8, 
         "category": "Laptops", "stock": "In Stock", "brand": "Apple",
         "description": "Apple M3 Max chip, 36GB RAM, 1TB SSD"},
        {"name": "Dell XPS 15", "price": 1899.99, "rating": 4.6,
         "category": "Laptops", "stock": "In Stock", "brand": "Dell",
         "description": "Intel i9, 32GB RAM, 1TB SSD, 4K OLED"},
        {"name": "Samsung Galaxy S24 Ultra", "price": 1299.99, "rating": 4.7,
         "category": "Smartphones", "stock": "In Stock", "brand": "Samsung",
         "description": "256GB, Titanium, AI Features"},
        {"name": "iPhone 15 Pro Max", "price": 1199.99, "rating": 4.9,
         "category": "Smartphones", "stock": "Low Stock", "brand": "Apple",
         "description": "256GB, Natural Titanium, A17 Pro"},
        {"name": "Sony WH-1000XM5", "price": 349.99, "rating": 4.8,
         "category": "Headphones", "stock": "In Stock", "brand": "Sony",
         "description": "Wireless Noise Cancelling, 30hr Battery"},
        {"name": "LG OLED C3 65 inch", "price": 1799.99, "rating": 4.7,
         "category": "TVs", "stock": "In Stock", "brand": "LG",
         "description": "4K OLED, 120Hz, webOS, Dolby Atmos"},
        {"name": "iPad Air M2", "price": 599.99, "rating": 4.6,
         "category": "Tablets", "stock": "In Stock", "brand": "Apple",
         "description": "11-inch, M2 chip, 128GB, Wi-Fi"},
        {"name": "Logitech MX Master 3S", "price": 99.99, "rating": 4.7,
         "category": "Accessories", "stock": "In Stock", "brand": "Logitech",
         "description": "Wireless Mouse, 8K DPI, USB-C"},
        {"name": "ASUS ROG Strix G16", "price": 1599.99, "rating": 4.5,
         "category": "Laptops", "stock": "In Stock", "brand": "ASUS",
         "description": "RTX 4070, i9-13980HX, 16GB RAM"},
        {"name": "AirPods Pro 2", "price": 249.99, "rating": 4.8,
         "category": "Headphones", "stock": "In Stock", "brand": "Apple",
         "description": "USB-C, Active Noise Cancellation"},
        {"name": "Samsung 49 inch Odyssey G9", "price": 1099.99, "rating": 4.4,
         "category": "Monitors", "stock": "Low Stock", "brand": "Samsung",
         "description": "DQHD, 240Hz, 1ms, Curved"},
        {"name": "Corsair K100 RGB", "price": 229.99, "rating": 4.6,
         "category": "Accessories", "stock": "In Stock", "brand": "Corsair",
         "description": "Mechanical Keyboard, Cherry MX Speed"},
        {"name": "Google Pixel 8 Pro", "price": 999.99, "rating": 4.5,
         "category": "Smartphones", "stock": "In Stock", "brand": "Google",
         "description": "256GB, AI Camera, Tensor G3"},
        {"name": "Nintendo Switch OLED", "price": 349.99, "rating": 4.7,
         "category": "Gaming", "stock": "In Stock", "brand": "Nintendo",
         "description": "7-inch OLED, 64GB, White"},
        {"name": "Dyson V15 Detect", "price": 749.99, "rating": 4.6,
         "category": "Home", "stock": "In Stock", "brand": "Dyson",
         "description": "Cordless Vacuum, Laser Detection"},
    ]
    
    # Add timestamp to each product
    for product in sample_products:
        product['scraped_at'] = datetime.now().isoformat()
    
    # Load products into scraper
    scraper.products = sample_products
    
    print(f"\n[+] Scraped {len(sample_products)} products")
    
    # Clean data
    df = scraper.clean_data()
    print(f"[+] Cleaned data: {len(df)} unique products")
    
    # Export to all formats
    scraper.export_csv('output/products.csv')
    print("[+] Exported to CSV: output/products.csv")
    
    scraper.export_json('output/products.json')
    print("[+] Exported to JSON: output/products.json")
    
    try:
        scraper.export_excel('output/products.xlsx')
        print("[+] Exported to Excel: output/products.xlsx")
    except ImportError:
        print("[!] openpyxl not installed, skipping Excel export")
    
    # Print summary
    summary = scraper.get_summary()
    print(f"\n{'=' * 60}")
    print("   SCRAPING SUMMARY")
    print(f"{'=' * 60}")
    print(f"   Total Products: {summary['total_products']}")
    print(f"   Average Price:  ${summary.get('avg_price', 'N/A')}")
    print(f"   Price Range:    ${summary.get('min_price', 'N/A')} - ${summary.get('max_price', 'N/A')}")
    print(f"   Average Rating: {summary.get('avg_rating', 'N/A')}/5.0")
    print(f"   Errors:         {summary['total_errors']}")
    print(f"{'=' * 60}")
    
    # Show data preview
    print(f"\n   TOP 5 PRODUCTS BY PRICE:")
    print("-" * 60)
    for i, row in df.head().iterrows():
        print(f"   {i+1}. {row['name']}")
        print(f"      Price: ${row['price']} | Rating: {row['rating']}/5.0 | {row['stock']}")
        print()
    
    # Category breakdown
    print(f"\n   PRODUCTS BY CATEGORY:")
    print("-" * 60)
    category_counts = df['category'].value_counts()
    for cat, count in category_counts.items():
        avg_price = df[df['category'] == cat]['price'].mean()
        print(f"   {cat}: {count} products (avg ${avg_price:.2f})")
    
    print(f"\n[+] Demo complete! Check the 'output' folder for exported files.")


if __name__ == "__main__":
    import os
    os.makedirs('output', exist_ok=True)
    run_demo()
