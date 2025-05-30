from langchain.tools import tool
import os
from pinecone import Pinecone, ServerlessSpec
import logging
import json
from datetime import datetime
 
logger = logging.getLogger(__name__)
 
def initialize_pinecone():
    """Initialize Pinecone client and ensure index exists."""
    api_key = os.getenv("PINECONE_API_KEY")
    if not api_key:
        logger.error("PINECONE_API_KEY not found")
        return None
 
    pc = Pinecone(api_key=api_key)
    index_name = "dynamic-pricing-index"
 
    if index_name not in [idx["name"] for idx in pc.list_indexes()]:
        logger.info(f"Creating Pinecone index: {index_name}")
        try:
            pc.create_index(
                name=index_name,
                dimension=384,
                metric="cosine",
                spec=ServerlessSpec(cloud="aws", region="us-west-2")
            )
        except Exception as e:
            logger.error(f"Failed to create index: {e}")
            return None
 
    return pc.Index(index_name)
 
@tool
def store_in_pinecone(data: dict) -> bool:
    """
    Store scraped product data in Pinecone or fallback to JSON.
   
    Args:
        data (dict): Product data (product_name, price, specifications).
   
    Returns:
        bool: True if stored, False otherwise.
    """
    try:
        index = initialize_pinecone()
        if index is None:
            logger.warning("Falling back to JSON")
            os.makedirs("data/scraped_data", exist_ok=True)
            with open(f"data/scraped_data/scrape_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json", "w") as f:
                json.dump(data, f)
            return True
 
        vector = [0.1] * 384  # Placeholder embedding
        metadata = {"price": data["price"], "specifications": data.get("specifications", "")}
        index.upsert(vectors=[(data["product_name"], vector, metadata)])
        logger.info(f"Stored in Pinecone: {data['product_name']}")
        return True
 
    except Exception as e:
        logger.error(f"Pinecone store error: {e}")
        os.makedirs("data/scraped_data", exist_ok=True)
        with open(f"data/scraped_data/scrape_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json", "w") as f:
            json.dump(data, f)
        return True
 
@tool
def query_pinecone(query: str) -> list:
    """
    Query Pinecone for product data or fallback to JSON.
   
    Args:
        query (str): Search query.
   
    Returns:
        list: List of products (product_name, price, specifications).
    """
    try:
        index = initialize_pinecone()
        if index is None:
            logger.warning("Falling back to JSON")
            import glob
            files = glob.glob("data/scraped_data/scrape_*.json")
            if files:
                with open(max(files, key=os.path.getctime)) as f:
                    return [json.load(f)]
            return []
 
        vector = [0.1] * 384  # Placeholder
        results = index.query(vector=vector, top_k=5, include_metadata=True)
        return [
            {
                "product_name": r["id"],
                "price": r["metadata"]["price"],
                "specifications": r["metadata"].get("specifications", "")
            }
            for r in results["matches"]
        ]
 
    except Exception as e:
        logger.error(f"Pinecone query error: {e}")
        return []
 