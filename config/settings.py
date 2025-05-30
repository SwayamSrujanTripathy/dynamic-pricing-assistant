import os
from dotenv import load_dotenv
 
load_dotenv()
 
# Ollama model name
LLAMA_MODEL_NAME = "deepseek-r1:1.5b"
 
# Pinecone settings
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_ENVIRONMENT = os.getenv("PINECONE_ENVIRONMENT")
PINECONE_INDEX_NAME = "pricing-data"
 
# Flipkart base URL
FLIPKART_BASE_URL = "https://www.amazon.in/"
 
 
 
 