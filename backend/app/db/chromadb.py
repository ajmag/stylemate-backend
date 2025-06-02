import os
import chromadb
from backend.app.config import settings
import logging
import numpy as np
from io import BytesIO
from PIL import Image


class ChromaDBClient:
    """ChromaDB client for managing collections and embeddings."""

    def __init__(self):
        """Initialize the ChromaDB client."""
        self.logger = logging.getLogger(__name__)
        self.logger.info("ChromaDBClient initialized")

        os.makedirs(settings.CHROMA_DB_DIR, exist_ok=True)
        self.client = chromadb.PersistentClient(path=settings.CHROMA_DB_DIR)

        # self.clip_embedding_function = get_embedding_class()


    def get_or_create_collection(self, collection_name: str) -> chromadb.Collection:
        """
        Get or create a collection in the database.
        
        This collection will work with pre-computed embeddings.
        
        Args:
            collection_name: Name of the collection
            
        Returns:
            ChromaDB collection
        """
        self.logger.info(f"Getting or creating collection: {collection_name}")
        return self.client.get_or_create_collection(name=collection_name)
    

    def get_or_create_multimodal_collection(self, collection_name: str) -> chromadb.Collection:
        """
        Get or create a multimodal collection using OpenCLIP.
        
        Args:
            collection_name: Name of the collection
            
        Returns:
            ChromaDB multimodal collection
        """
        self.logger.info(f"Getting or creating multimodal collection: {collection_name}")
        return self.client.get_or_create_collection(name=collection_name, 
                                                    embedding_function=self.clip_embedding_function)
    

    @staticmethod
    def convert_bytes_to_image(image_data: bytes) -> np.ndarray:
        """
        Convert image bytes to numpy array for ChromaDB.
        
        Args:
            image_data: Binary image data
            
        Returns:
            numpy array representation of the image
        """
        # Convert the uploaded image bytes into a PIL Image object
        # This allows for further manipulation and ensures compatibility with CLIP  
        image = Image.open(BytesIO(image_data))
        
        # Ensure the image is in RGB format (required by CLIP models)
        # If the image is in a different mode (e.g., grayscale or CMYK), convert it to RGB
        if image.mode != "RGB":
            image = image.convert("RGB")
            
        # Convert the PIL Image object into a NumPy array
        # This prepares the image data for processing by machine learning models like CLIP
        return np.array(image)