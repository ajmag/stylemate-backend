import logging
import json
import uuid
from typing import Dict, Any, List, Optional

from backend.app.core.agents.vision_agent import VisionProcessingAgent
from backend.app.db.supabasedb import SupaBaseClient 
from backend.app.db.chromadb import ChromaDBClient  

class ClothingService:

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        #Hard coded now but will be replaced with config or env vars
        self._bucket_name = "clothing-images"
        self._database_name = "clothing_items"
        self._collection_name = "clothing_items"


    async def process_and_store_clothing_item(
            self,
            image_data: bytes,
            file_name: str,
            content_type: str,
            user_id: str) -> Dict[str, Any]:
        """Process an image and store it in both Supabase and ChromaDB."""
       
        try:
            # Process the image and get metadata and embeddings
            vision_agent = VisionProcessingAgent()
            self.logger.info("Processing image with vision agent")
            vision_result = await vision_agent.run(
                input_data={"image_data": image_data},
                user_id=user_id
            )
            self.logger.info(f"Vision agent processed image: {vision_result}")

            # steps to add the image and user_id/item_id into supabase here  
            sb_client = SupaBaseClient()
            sb_client.get_supabase_client()

            # Generate a unique file path for the image
            file_path = f"{user_id}/{uuid.uuid4()}.{file_name.split('.')[-1]}"
            self.logger.info(f"Uploading image to storage: {file_path}")

            storage_response = await sb_client.add_image_to_bucket(
                file_path, 
                self._bucket_name, 
                image_data, 
                content_type
            )
            self.logger.debug(f"Storage response: {storage_response}")
       
            # Add image metadata into database
            self.logger.info("Adding metadata to database")
            db_response = await sb_client.add_metadata_into_db(
                vision_result["fashion_metadata"], 
                file_path, 
                self._database_name
            )

            item_id = db_response.data[0]["id"]
            
            # Update the database record with embedding_id = item_id 
            await sb_client.update_db(self._database_name, item_id, "embedding_id")

            #store metadata results into chromadb
            self.logger.info("Storing embeddings in ChromaDB")
            db_client = ChromaDBClient()
            chroma_collection = db_client.get_or_create_collection(self._collection_name)

            chroma_collection.add(
                ids=[item_id],
                embeddings=[vision_result["embeddings"]],
                metadatas=[vision_result["fashion_metadata"]],
                documents=[json.dumps(vision_result["classification_result"])]
            )

            # Get public URL and embedding_id 
            image_url = sb_client.get_public_url(self._bucket_name, file_path)
            db_embedding_id = await sb_client.get_data_from_table(
                self._database_name, "embedding_id", "id", item_id
            )

            # Return structured response
            return {
                "item_id": item_id,
                "image_url": image_url,
                "db_response": db_response.data[0],
                "db_embedding_id": db_embedding_id,
                "fashion_metadata": vision_result["fashion_metadata"],
                "classification_result": {
                    "labels": vision_result["classification_result"].get("labels", []),
                    "objects": vision_result["classification_result"].get("objects", []),
                    "colors": vision_result["classification_result"].get("colors", [])
                },
                "embeddings": vision_result["embeddings"][:10] if "embeddings" in vision_result else None
            }

        except Exception as e:
            self.logger.exception(f"Error processing and storing clothing item: {str(e)}")
            raise RuntimeError(f"Error processing and storing clothing item: {str(e)}")
    