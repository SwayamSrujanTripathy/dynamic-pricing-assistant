from langchain.tools import tool
import requests
from bs4 import BeautifulSoup
import urllib.parse
import logging
 
logger = logging.getLogger(__name__)
 
@tool
def web_scraper(query: str) -> dict:
    """
    Scrape Amazon.in for product prices and specifications based on the query.
   
    Args:
        query (str): Search query (e.g., "Product: samsung, Specifications: S9000").
   
    Returns:
        dict: Dictionary with scraped products (name, price, specs) or error.
    """
    try:
        # Parse query
        clean_query = query.lower()
        search_terms = ""
        if 'product:' in clean_query and 'specifications:' in clean_query:
            product = clean_query.split('product:')[1].split(',')[0].strip()
            specs = clean_query.split('specifications:')[1].strip()
            search_terms = f"{product} {specs}"
        else:
            search_terms = query
 
        # Encode query
        encoded_query = urllib.parse.quote(search_terms)
        url = f"https://www.amazon.in/s?k={encoded_query}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
        }
 
        logger.info(f"Scraping Amazon.in: {url}")
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
 
        soup = BeautifulSoup(response.text, 'html.parser')
        products = []
 
        # Parse listings
        listings = soup.find_all('div', {'data-component-type': 's-search-result'}, limit=5)
        for item in listings:
            try:
                name_elem = item.find('span', class_='a-size-medium a-color-base a-text-normal')
                price_elem = item.find('span', class_='a-price-whole')
                if name_elem and price_elem:
                    name = name_elem.text.strip()
                    price = f"₹{price_elem.text.strip().replace(',', '')}"
                    # Placeholder specs (Amazon.in may not list full specs in search)
                    specs = "Specifications not available in search results"
                    products.append({"product_name": name, "price": price, "specifications": specs})
            except AttributeError:
                continue
 
        if not products:
            logger.warning(f"No products found for query: {search_terms}")
            return {"error": "No products found", "products": []}
 
        logger.info(f"Scraped {len(products)} products")
        return {"products": products}
 
    except requests.HTTPError as e:
        logger.error(f"HTTP error: {e}")
        return {"error": str(e), "products": []}
    except Exception as e:
        logger.error(f"Scraping error: {e}")
        return {"error": str(e), "products": []}