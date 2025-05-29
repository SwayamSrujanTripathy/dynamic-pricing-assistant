from langchain.tools import tool
from pinecone import Pinecone, ServerlessSpec
from config.settings import PINECONE_API_KEY, PINECONE_ENVIRONMENT, PINECONE_INDEX_NAME
import uuid
import numpy as np

@tool
def store_in_pinecone(data: str) -> str:
    """Store scraped data in Pinecone vector database."""
    try:
        pc = Pinecone(api_key=PINECONE_API_KEY)
        index_name = PINECONE_INDEX_NAME
        
        # Create index if it doesn't exist
        if index_name not in pc.list_indexes().names():
            pc.create_index(
                name=index_name,
                dimension=128,  # Simple dimension for text embeddings
                metric="cosine",
                spec=ServerlessSpec(cloud="aws", region=PINECONE_ENVIRONMENT)
            )
        
        index = pc.Index(index_name)
        
        # Generate a simple embedding (random for simplicity; replace with actual embeddings if needed)
        embedding = np.random.rand(128).tolist()
        vector_id = str(uuid.uuid4())
        
        # Store data
        index.upsert(vectors=[(vector_id, embedding, {"text": data})])
        return f"Data stored in Pinecone with ID: {vector_id}"
    except Exception as e:
        return f"Error storing in Pinecone: {str(e)}"

@tool
def query_pinecone(query: str) -> str:
    """Query Pinecone for relevant pricing data."""
    try:
        pc = Pinecone(api_key=PINECONE_API_KEY)
        index = pc.Index(PINECONE_INDEX_NAME)
        
        # Generate a query embedding (random for simplicity)
        query_embedding = np.random.rand(128).tolist()
        
        # Query Pinecone
        results = index.query(vector=query_embedding, top_k=3, include_metadata=True)
        matches = [match["metadata"]["text"] for match in results["matches"]]
        return str(matches) if matches else "No relevant data found in Pinecone."
    except Exception as e:
        return f"Error querying Pinecone: {str(e)}"