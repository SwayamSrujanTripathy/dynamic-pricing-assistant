from langchain.tools import tool
import requests
from bs4 import BeautifulSoup
import urllib.parse
import logging
import re
import time
import os
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from playwright.async_api import async_playwright
from utils.helpers import save_scraped_data, log_error
 
logger = logging.getLogger(__name__)
 
@tool
async def web_scraper(query: str) -> dict:
    """
    Scrape Amazon.in or Flipkart.com for the top product matching the product name and specifications.
   
    Args:
        query (str): Search query (e.g., "Samsung Galaxy A54, Specifications: 8GB RAM, 256GB storage site:amazon.in").
   
    Returns:
        dict: Scraped products with product_name, price (INR), specifications, and platform.
    """
    try:
        clean_query = re.sub(r'\s+', ' ', query.lower().strip())
        platform = "amazon.in" if "site:amazon.in" in clean_query else "flipkart.com"
        search_terms = clean_query.replace(f"site:{platform}", "").strip()
        specs_dict = {"ram": "unknown", "storage": "unknown"}
        product_name = "unknown"
 
        # Parse product name and specifications
        if ',' in search_terms:
            parts = [p.strip() for p in search_terms.split(',', 1)]
            product_name = parts[0].replace("product:", "").strip()
            specs = parts[1].replace("specifications:", "").strip() if len(parts) > 1 else ""
            search_terms = f"{product_name} {specs}".replace(",", " ").strip()
            spec_parts = [s.strip().lower() for s in specs.split(',')]
            for part in spec_parts:
                if "gb" in part.lower():
                    if "ram" in part.lower():
                        specs_dict["ram"] = re.sub(r'\s+', '', part)
                    elif "storage" in part.lower() or re.search(r'\d+\s*gb', part, re.IGNORECASE):
                        specs_dict["storage"] = re.sub(r'\s+', '', part)
        else:
            product_name = search_terms.replace("product:", "").strip()
            specs = ""
 
        # Construct search URL
        encoded_query = urllib.parse.quote(search_terms)
        url = f"https://www.{platform}/s?k={encoded_query}" if platform == "amazon.in" else f"https://www.flipkart.com/search?q={encoded_query}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "Referer": f"https://www.{platform}/",
            "Cookie": "session-id=123-4567890-1234567; i18n-prefs=INR;"
        }
 
        # Setup retry strategy with exponential backoff
        session = requests.Session()
        retries = Retry(total=7, backoff_factor=3, status_forcelist=[429, 500, 502, 503, 504])
        session.mount("https://", HTTPAdapter(max_retries=retries))
 
        logger.info(f"Scraping {platform}: {url}")
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            await page.set_extra_http_headers(headers)
            await page.goto(url, timeout=60000)
            content = await page.content()
            await browser.close()
 
        # Save raw HTML for debugging
        os.makedirs("data/scraped_data", exist_ok=True)
        timestamp = int(time.time())
        html_file = f"data/scraped_data/raw_{platform}_{timestamp}.html"
        with open(html_file, "w", encoding="utf-8") as f:
            f.write(content)
        logger.info(f"Saved raw HTML to {html_file}")
 
        soup = BeautifulSoup(content, 'html.parser')
        products = []
 
        # Scrape Amazon.in
        if platform == "amazon.in":
            listings = soup.find_all('div', class_=re.compile('s-result-item|s-main-slot'), limit=15)
            count = 0
            for item in listings:
                try:
                    name_elem = item.find('span', class_=re.compile('a-size-medium|a-text-normal'))
                    price_elem = item.find('span', class_=re.compile('a-price-whole|a-price'))
                    if name_elem and price_elem:
                        name = name_elem.text.strip().lower()
                        if product_name.lower() in name:
                            ram_match = re.search(r'8\s*gb|8gb|8\s*GB|8\s*G', name, re.IGNORECASE)
                            storage_match = re.search(r'256\s*gb|256gb|256\s*GB|256\s*G', name, re.IGNORECASE)
                            if ram_match and storage_match:
                                price_text = price_elem.text.strip().replace(',', '').replace('₹', '')
                                price = f"₹{price_text}"
                                if '$' in price_text:
                                    price_val = float(re.sub(r'[^\d.]', '', price_text)) * 85
                                    price = f"₹{int(price_val):,}"
                                product_data = {
                                    "product_name": name_elem.text.strip(),
                                    "price": price,
                                    "specifications": specs_dict,
                                    "platform": "Amazon.in"
                                }
                                products.append(product_data)
                                count += 1
                                if count >= 1:
                                    break
                except Exception as e:
                    log_error(f"Skipping Amazon.in listing: {e}")
                    continue
        # Scrape Flipkart.com
        else:
            listings = soup.find_all('div', class_=re.compile('_2kHMtA|_4ddWXP'), limit=15)
            count = 0
            for item in listings:
                try:
                    name_elem = item.find('div', class_=re.compile('_4rR01T|syl9yP'))
                    price_elem = item.find('div', class_=re.compile('_30jeq3|_1_WHN1'))
                    if name_elem and price_elem:
                        name = name_elem.text.strip().lower()
                        if product_name.lower() in name:
                            ram_match = re.search(r'8\s*gb|8gb|8\s*GB|8\s*G', name, re.IGNORECASE)
                            storage_match = re.search(r'256\s*gb|256gb|256\s*GB|256\s*G', name, re.IGNORECASE)
                            if ram_match and storage_match:
                                price_text = price_elem.text.strip().replace('₹', '').replace(',', '')
                                price = f"₹{price_text}"
                                if '$' in price_text:
                                    price_val = float(re.sub(r'[^\d.]', '', price_text)) * 85
                                    price = f"₹{int(price_val):,}"
                                product_data = {
                                    "product_name": name_elem.text.strip(),
                                    "price": price,
                                    "specifications": specs_dict,
                                    "platform": "Flipkart.com"
                                }
                                products.append(product_data)
                                count += 1
                                if count >= 1:
                                    break
                except Exception as e:
                    log_error(f"Skipping Flipkart.com listing: {e}")
                    continue
 
        if products:
            save_scraped_data(products, platform, product_name, specs)
            logger.info(f"Scraped {len(products)} products from {platform}")
            return {"products": products}
 
        logger.warning(f"No products found for query: {search_terms} on {platform}")
        return {"error": [], "products": []}
 
    except Exception as e:
        logger.error(f"Scraping error: {e}")
        return {"error": f"Error: {str(e)}", "products": []}