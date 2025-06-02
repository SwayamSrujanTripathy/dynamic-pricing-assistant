from langchain.tools import tool
from pinecone import Pinecone
import os
import logging
from langchain_huggingface import HuggingFaceEmbeddings
 
logger = logging.getLogger(__name__)
 
# Initialize Pinecone
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
index_name = "dynamic-pricing-index"
index = pc.Index(index_name)
 
# Initialize embeddings
embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
 
@tool
def store_in_pinecone(data: dict) -> dict:
    """
    Store product data in Pinecone vector database.
   
    Args:
        data (dict): Product data with product_name, price, specifications, and platform.
   
    Returns:
        dict: Status of storage operation.
    """
    try:
        product_id = f"{data.get('product_name', 'unknown')}_{data.get('platform', 'unknown')}"
        text = f"{data.get('product_name', '')} {data.get('price', '')} {data.get('specifications', '')}"
        vector = embeddings.embed_query(text)
       
        metadata = {
            "product_name": data.get("product_name", ""),
            "price": data.get("price", ""),
            "platform": data.get("platform", ""),
            "ram": data.get("specifications", {}).get("ram", ""),
            "storage": data.get("specifications", {}).get("storage", "")
        }
       
        index.upsert(vectors=[(product_id, vector, metadata)])
        logger.info(f"Stored product in Pinecone: {product_id}")
        return {"status": "success", "product_id": product_id}
   
    except Exception as e:
        logger.error(f"Pinecone storage error: {e}")
        return {"status": "error", "error": str(e)}
 
@tool
def query_pinecone(query: str) -> dict:
    """
    Query Pinecone for similar products.
   
    Args:
        query (str): Search query.
   
    Returns:
        dict: Matching products.
    """
    try:
        vector = embeddings.embed_query(query)
        results = index.query(vector=vector, top_k=5, include_metadata=True)
       
        matches = [
            {
                "product_name": match["metadata"]["product_name"],
                "price": match["metadata"]["price"],
                "platform": match["metadata"]["platform"],
                "specifications": {
                    "ram": match["metadata"]["ram"],
                    "storage": match["metadata"]["storage"]
                }
            }
            for match in results["matches"]
        ]
       
        logger.info(f"Queried Pinecone for: {query}")
        return {"matches": matches}
   
    except Exception as e:
        logger.error(f"Pinecone query error: {e}")
        return {"status": "error", "error": str(e)}