from langchain.tools import tool
import requests
from bs4 import BeautifulSoup
from config.settings import FLIPKART_BASE_URL
from models.data_models import PricingSource, ProductCategory, ProductSpecifications
import json
import os
import datetime

@tool
def web_scraper(query: str) -> str:
    """Scrape Flipkart for product pricing and specifications based on the query and save to data/scraped_data/."""
    try:
        # Format query for Flipkart search
        search_query = query.replace(" ", "+")
        url = f"{FLIPKART_BASE_URL}/search?q={search_query}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, "html.parser")
        products = soup.find_all("div", {"class": "_1AtVbE"})
        
        results = []
        for product in products[:3]:  # Limit to first 3 results
            name = product.find("a", {"class": "IRpwTa"}) or product.find("div", {"class": "_4rR01T"})
            price = product.find("div", {"class": "_30jeq3"}) or product.find("div", {"class": "_30jeq3 _1_WHN1"})
            if name and price:
                # Create data model instances
                specs = {"price": price.text.strip()}
                product_spec = ProductSpecifications(
                    name=name.text.strip(),
                    specs=specs,
                    category=ProductCategory(name="Unknown")
                )
                results.append({
                    "source": PricingSource(source="Flipkart", url=url),
                    "product": product_spec.__dict__
                })
        
        if results:
            # Save to data/scraped_data/ with timestamp
            os.makedirs("data/scraped_data", exist_ok=True)
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            file_path = f"data/scraped_data/scrape_{timestamp}.json"
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(results, f, indent=2, default=lambda o: o.__dict__)
            return str(results)
        return "No products found."
    except Exception as e:
        return f"Error scraping Flipkart: {str(e)}"