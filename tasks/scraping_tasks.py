# from crewai import Task
# from tools.web_scraper import WebScraper
# from tools.vector_db import VectorDB
# import time

# def create_scraping_task(agent, product_name: str):
#     return Task(
#         description=f"""
#         Scrape pricing data for the product: {product_name}
        
#         Instructions:
#         1. Search for the product on Amazon, Best Buy, and Newegg
#         2. Extract pricing information, product titles, and URLs
#         3. If the product name is ambiguous, ask for clarification
#         4. Store the collected data in the vector database
#         5. Return a summary of the collected pricing data
        
#         Focus only on electronic devices and ensure data accuracy.
#         """,
#         agent=agent,
#         expected_output="Structured pricing data with product details, prices, and website sources stored in vector database"
#     )

# def execute_scraping_task(product_name: str):
#     """Execute the scraping task"""
#     scraper = WebScraper()
#     vector_db = VectorDB()
    
#     all_pricing_data = []
    
#     for website in ["amazon.com", "bestbuy.com", "newegg.com"]:
#         print(f"Scraping {website} for {product_name}...")
#         pricing_data = scraper.search_product(product_name, website)
        
#         if pricing_data:
#             all_pricing_data.extend(pricing_data)
#             time.sleep(2)  # Be respectful to websites
    
#     if all_pricing_data:
#         # Store in vector database
#         vector_db.store_pricing_data(product_name, all_pricing_data)
        
#         # Return summary
#         avg_price = sum(item['price'] for item in all_pricing_data) / len(all_pricing_data)
#         min_price = min(item['price'] for item in all_pricing_data)
#         max_price = max(item['price'] for item in all_pricing_data)
        
#         summary = {
#             "product_name": product_name,
#             "total_listings": len(all_pricing_data),
#             "average_price": avg_price,
#             "min_price": min_price,
#             "max_price": max_price,
#             "websites_scraped": list(set(item['website'] for item in all_pricing_data))
#         }
        
#         scraper.close()
#         return summary
#     else:
#         scraper.close()
#         return {"error": "No pricing data found. Please provide more specific product details."}