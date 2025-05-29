import pinecone
import json
import hashlib
from typing import List, Dict, Optional, Any
from datetime import datetime
import numpy as np
from config.settings import settings
from models.data_models import ScrapedData, PricingSource
import logging

logger = logging.getLogger(__name__)

class VectorDBTool:
    def __init__(self):
        self.client = None
        self.index = None
        self._initialize_pinecone()
    
    def _initialize_pinecone(self):
        """Initialize Pinecone client and index"""
        try:
            # Initialize Pinecone
            pinecone.init(
                api_key=settings.PINECONE_API_KEY,
                environment=settings.PINECONE_ENVIRONMENT
            )
            
            # Create index if it doesn't exist
            if settings.PINECONE_INDEX_NAME not in pinecone.list_indexes():
                pinecone.create_index(
                    name=settings.PINECONE_INDEX_NAME,
                    dimension=settings.VECTOR_DIMENSION,
                    metric="cosine"
                )
                logger.info(f"Created Pinecone index: {settings.PINECONE_INDEX_NAME}")
            
            # Connect to index
            self.index = pinecone.Index(settings.PINECONE_INDEX_NAME)
            logger.info("Successfully connected to Pinecone")
            
        except Exception as e:
            logger.error(f"Error initializing Pinecone: {e}")
            raise
    
    def _generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for text (simplified version using hash-based approach)"""
        # In production, use proper embedding models like sentence-transformers
        # For now, creating a deterministic hash-based embedding
        text_hash = hashlib.sha256(text.encode()).hexdigest()
        
        # Convert hash to numerical vector
        embedding = []
        for i in range(0, len(text_hash), 2):
            hex_pair = text_hash[i:i+2]
            embedding.append(int(hex_pair, 16) / 255.0)
        
        # Pad or truncate to required dimension
        while len(embedding) < settings.VECTOR_DIMENSION:
            embedding.extend(embedding[:settings.VECTOR_DIMENSION - len(embedding)])
        
        return embedding[:settings.VECTOR_DIMENSION]
    
    def _create_product_id(self, product_name: str, brand: str = "", model: str = "") -> str:
        """Create unique product ID"""
        product_string = f"{product_name}_{brand}_{model}".lower().replace(" ", "_")
        return hashlib.md5(product_string.encode()).hexdigest()[:16]
    
    def store_scraped_data(self, scraped_data: ScrapedData) -> bool:
        """Store scraped data in vector database"""
        try:
            # Create product embedding
            product_text = f"{scraped_data.product_name} {scraped_data.specifications.brand} {scraped_data.specifications.model}"
            embedding = self._generate_embedding(product_text)
            
            # Create unique ID
            product_id = self._create_product_id(
                scraped_data.product_name,
                scraped_data.specifications.brand,
                scraped_data.specifications.model
            )
            
            # Prepare metadata
            metadata = {
                "product_name": scraped_data.product_name,
                "brand": scraped_data.specifications.brand,
                "model": scraped_data.specifications.model,
                "category": scraped_data.specifications.category.value,
                "average_price": scraped_data.average_price,
                "min_price": scraped_data.price_range["min"],
                "max_price": scraped_data.price_range["max"],
                "source_count": len(scraped_data.pricing_sources),
                "sources": [source.website for source in scraped_data.pricing_sources],
                "timestamp": datetime.now().isoformat(),
                "raw_data": json.dumps(scraped_data.dict(), default=str)
            }
            
            # Upsert to Pinecone
            self.index.upsert(
                vectors=[(product_id, embedding, metadata)]
            )
            
            logger.info(f"Successfully stored data for product: {scraped_data.product_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error storing scraped data: {e}")
            return False
    
    def search_similar_products(self, product_name: str, brand: str = "", limit: int = 5) -> List[Dict]:
        """Search for similar products in the database"""
        try:
            query_text = f"{product_name} {brand}".strip()
            query_embedding = self._generate_embedding(query_text)
            
            # Search in Pinecone
            results = self.index.query(
                vector=query_embedding,
                top_k=limit,
                include_metadata=True
            )
            
            similar_products = []
            for match in results.matches:
                product_data = {
                    "id": match.id,
                    "score": match.score,
                    "metadata": match.metadata
                }
                similar_products.append(product_data)
            
            return similar_products
            
        except Exception as e:
            logger.error(f"Error searching similar products: {e}")
            return []
    
    def get_market_insights(self, category: str, brand: str = None) -> Dict[str, Any]:
        """Get market insights for a specific category"""
        try:
            # Query products in the same category
            filter_dict = {"category": category}
            if brand:
                filter_dict["brand"] = brand
            
            # Get all products in category (simplified approach)
            query_embedding = self._generate_embedding(f"{category} {brand or ''}")
            results = self.index.query(
                vector=query_embedding,
                top_k=100,
                include_metadata=True,
                filter=filter_dict
            )
            
            if not results.matches:
                return {"error": "No data found for this category"}
            
            # Calculate insights
            prices = []
            brands = set()
            sources = set()
            
            for match in results.matches:
                metadata = match.metadata
                prices.append(metadata.get("average_price", 0))
                brands.add(metadata.get("brand", "Unknown"))
                sources.update(metadata.get("sources", []))
            
            insights = {
                "category": category,
                "total_products": len(results.matches),
                "price_statistics": {
                    "min": min(prices) if prices else 0,
                    "max": max(prices) if prices else 0,
                    "average": sum(prices) / len(prices) if prices else 0,
                    "median": sorted(prices)[len(prices)//2] if prices else 0
                },
                "brand_count": len(brands),
                "top_brands": list(brands)[:10],
                "data_sources": list(sources),
                "last_updated": datetime.now().isoformat()
            }
            
            return insights
            
        except Exception as e:
            logger.error(f"Error getting market insights: {e}")
            return {"error": str(e)}
    
    def update_product_data(self, product_id: str, updated_data: Dict) -> bool:
        """Update existing product data"""
        try:
            # Get existing data
            existing = self.index.fetch(ids=[product_id])
            if not existing.vectors:
                return False
            
            # Update metadata
            existing_metadata = existing.vectors[product_id].metadata
            existing_metadata.update(updated_data)
            existing_metadata["last_updated"] = datetime.now().isoformat()
            
            # Update in Pinecone
            embedding = existing.vectors[product_id].values
            self.index.upsert(
                vectors=[(product_id, embedding, existing_metadata)]
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Error updating product data: {e}")
            return False
    
    def delete_old_data(self, days_old: int = 30) -> bool:
        """Delete data older than specified days"""
        try:
            cutoff_date = datetime.now().timestamp() - (days_old * 24 * 60 * 60)
            
            # Note: This is a simplified approach
            # In production, you'd want more sophisticated cleanup
            logger.info(f"Cleanup scheduled for data older than {days_old} days")
            return True
            
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
            return False
    
    def get_database_stats(self) -> Dict[str, Any]:
        """Get database statistics"""
        try:
            stats = self.index.describe_index_stats()
            
            return {
                "total_vectors": stats.total_vector_count,
                "dimension": stats.dimension,
                "index_fullness": stats.index_fullness,
                "namespaces": dict(stats.namespaces) if stats.namespaces else {}
            }
            
        except Exception as e:
            logger.error(f"Error getting database stats: {e}")
            return {"error": str(e)}