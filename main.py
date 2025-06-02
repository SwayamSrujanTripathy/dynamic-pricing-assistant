import streamlit as st
import logging
import asyncio
from dotenv import load_dotenv
import os
from agents.competitor_scraper import CompetitorScraperAgent
from agents.price_optimizer import PriceOptimizerAgent
from agents.impact_simulator import ImpactSimulatorAgent
from tools.web_scraper import web_scraper
from tools.vector_db_tools import store_in_pinecone
import json
 
# Load .env file
load_dotenv()
 
logging.basicConfig(level=logging.INFO, handlers=[logging.FileHandler('app.log', encoding='utf-8'), logging.StreamHandler()])
logger = logging.getLogger(__name__)
 
async def main():
    st.set_page_config(page_title="Dynamic Pricing Assistant", layout="wide")
    st.title("Dynamic Pricing Assistant")
 
    tools = [web_scraper, store_in_pinecone]
    tool_names = [tool.name for tool in tools]
 
    with st.form("pricing_form"):
        product = st.text_input("Product", placeholder="e.g., Samsung Galaxy A54")
        specifications = st.text_input("Specifications", placeholder="e.g., 8GB RAM, 256GB storage")
        submit = st.form_submit_button("Analyze Pricing")
 
    if submit and product and specifications:
        query = f"Product: {product}, Specifications: {specifications}"
        logger.info(f"Processing query: {query}")
 
        try:
            competitor_agent = CompetitorScraperAgent()
            price_optimizer = PriceOptimizerAgent()
            impact_simulator = ImpactSimulatorAgent()
 
            logger.info("Running CompetitorScraperAgent")
            competitor_result = await asyncio.to_thread(competitor_agent.execute, query)
            products = competitor_result.get("products", [])
            logger.info(f"Scraped {len(products)} products")
 
            if not products:
                logger.warning("No products found from scraper")
 
            logger.info("Running PriceOptimizerAgent")
            price_result = price_optimizer.execute(products, query)
            logger.info(f"PriceOptimizerAgent result: {json.dumps(price_result, indent=2)}")
 
            suggested_price = price_result.get("suggested_price", "₹0")
            strategy = price_result.get("strategy", "No price data available")
 
            logger.info("Running ImpactSimulatorAgent")
            impact_query = f"{query}, price: {suggested_price}"
            impact_result = impact_simulator.execute(impact_query, products)
            logger.info(f"ImpactSimulatorAgent result: {json.dumps(impact_result, indent=2)}")
 
            st.subheader("Launch Price Recommendation")
            st.write(f"- **Suggested Launch Price**: {suggested_price}")
            st.write(f"- **Strategy**: {strategy}")
 
            st.subheader("Launch Impact Analysis")
            impact = impact_result.get("impact", "Cannot estimate impact: No valid price provided")
            st.write(f"- **Sales & Satisfaction Impact**: {impact}")
 
        except Exception as e:
            logger.error(f"Main error: {str(e)}")
            st.error(f"Error processing query: {str(e)}")
 
if __name__ == "__main__":
    asyncio.run(main())
 