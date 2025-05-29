import os
from typing import List, Dict, Any
from dotenv import load_dotenv

load_dotenv()

class Settings:
    # API Keys
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    PINECONE_API_KEY: str = os.getenv("PINECONE_API_KEY", "")
    PINECONE_ENVIRONMENT: str = os.getenv("PINECONE_ENVIRONMENT", "gcp-starter")
    
    # Model Configuration
    LLM_MODEL: str = "gemini-2.0-flash-exp"
    TEMPERATURE: float = 0.1
    MAX_TOKENS: int = 4096
    
    # Scraping Configuration
    MAX_WEBSITES: int = 3
    REQUEST_TIMEOUT: int = 30
    USER_AGENT: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    
    # Vector Database Configuration
    PINECONE_INDEX_NAME: str = "pricing-data"
    VECTOR_DIMENSION: int = 768
    
    # Target Websites for Scraping
    TARGET_WEBSITES: List[str] = [
        "amazon.com",
        "flipkart.com",
        "myntra.com"
    ]
    
    # Electronic Device Categories
    SUPPORTED_CATEGORIES: List[str] = [
        "smartphones",
        "laptops",
        "tablets",
        "smartwatches",
        "headphones",
        "cameras",
        "gaming_consoles",
        "speakers",
        "monitors",
        "televisions"
    ]
    
    # Pricing Strategy Parameters
    PROFIT_MARGIN_RANGE: Dict[str, float] = {
        "min": 0.05,  # 5%
        "max": 0.30   # 30%
    }
    
    COMPETITIVE_THRESHOLD: float = 0.15  # 15% price difference threshold
    
    # Rate Limiting
    REQUESTS_PER_MINUTE: int = 60
    SCRAPING_DELAY: float = 2.0  # seconds between requests
    
    @classmethod
    def validate_config(cls) -> bool:
        """Validate that all required configuration is present"""
        required_keys = ["GEMINI_API_KEY", "PINECONE_API_KEY"]
        missing_keys = [key for key in required_keys if not getattr(cls, key)]
        
        if missing_keys:
            raise ValueError(f"Missing required environment variables: {missing_keys}")
        
        return True

# Create global settings instance
settings = Settings()