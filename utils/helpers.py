import json
import os
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

def save_scraped_data(products: list, platform: str, product_name: str, specs: str) -> None:
    """
    Save scraped product data to a JSON file in data/scraped_data/.
    
    Args:
        products (list): List of product dictionaries with name, price, specifications, platform.
        platform (str): Platform name (e.g., 'Amazon.in', 'Flipkart.com').
        product_name (str): Name of the product (e.g., 'Samsung Galaxy A54').
        specs (str): Specifications (e.g., '8GB RAM, 256GB storage').
    """
    try:
        os.makedirs("data/scraped_data", exist_ok=True)
        timestamp = int(datetime.now().timestamp())
        safe_product_name = "".join(c for c in product_name if c.isalnum() or c in (" ", "_")).replace(" ", "_").lower()
        filename = f"data/scraped_data/scraped_{safe_product_name}_{platform.lower().replace('.', '_')}_{timestamp}.json"
        
        data = {
            "platform": platform,
            "product_name": product_name,
            "specifications": specs,
            "products": products,
            "timestamp": datetime.now().isoformat()
        }
        
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        logger.info(f"Saved scraped data to {filename}")
    except Exception as e:
        logger.error(f"Error saving scraped data: {str(e)}")

def log_error(message: str) -> None:
    """
    Log an error message to the application log.
    
    Args:
        message (str): Error message to log.
    """
    logger.error(f"Scraping error: {message}")