import os
import chromadb
from app.config import settings

def create_chromadb_client() -> chromadb.Client:
    """Create and return chromadb client"""

    # make sure directory exists - will use on local for initial dev
    os.makedirs(settings.CHROMA_DB_DIR, exist_ok=True)

    # create the persistent client
    return chromadb.PersistentClient(path=settings.CHROMA_DB_DIR)

def get_or_create_collection(client, collection_name="clothing_items"):
    """Gets an existing collection or creates a new one if it doesn't exist"""
    
    return client.get_or_create_collection(name=collection_name)


chroma_client = create_chromadb_client()
clothing_collection = get_or_create_collection(chroma_client)