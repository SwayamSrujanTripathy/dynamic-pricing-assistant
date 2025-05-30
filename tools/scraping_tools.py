from langchain.tools import tool
import requests
from bs4 import BeautifulSoup
from config.settings import FLIPKART_BASE_URL
 
@tool
def scrape_flipkart(query: str) -> str:
    """Scrape Flipkart for product pricing based on the query."""
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
                results.append({"name": name.text.strip(), "price": price.text.strip()})
       
        return str(results) if results else "No products found."
    except Exception as e:
        return f"Error scraping Flipkart: {str(e)}"