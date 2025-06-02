import os
from dotenv import load_dotenv
 
load_dotenv()
 
LLAMA_MODEL_NAME = os.getenv("OLLAMA_MODEL", "deepseek-r1:1.5b")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_INDEX_NAME = "dynamic-pricing-index"
FLIPKART_BASE_URL = "https://www.flipkart.com/"
AMAZON_BASE_URL = "https://www.amazon.in/"