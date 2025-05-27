from typing import Dict, Any
import asyncio
from .base import Agent
from google.cloud import vision
from google.api_core.exceptions import GoogleAPICallError
from backend.app.core.manager.metadata_manager import ClothingMetadataManager
from backend.app.core.manager.embedding_manager import ClothingEmbeddingManager

agent_name = "vision_agent"

class VisionProcessingAgent(Agent):
    """Agent responsible for processing clothing images. Returns metadata and embeddings."""

    def __init__(self):
        super().__init__(agent_name)
        self.client = vision.ImageAnnotatorClient()
        self.metadata_manager = ClothingMetadataManager()
        self.embedding_manager = ClothingEmbeddingManager()     


    async def run(self, input_data: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Process an image and extract clothing information."""

        image_data = input_data.get("image_data")
        if not image_data:
            raise ValueError("No image data provided")
        
        # Step 1: Get image classification from external api call
        self.logger.info("Analyzing image with vision api")
        classification_result = await self._classify_image(image_data)

        # Step 2: Extract clothing metadata
        fashion_metadata = self.metadata_manager.extract_clothing_metadata(classification_result, user_id)
        self.logger.info(f"Extracted fashion metadata: {fashion_metadata}")

        # Step 3: Get embeddings for similarity search
        self.logger.info("Generating image embedding")
        embeddings = self.embedding_manager.generate_embedding(fashion_metadata, classification_result)

        return {
            "fashion_metadata": fashion_metadata,
            "embeddings": embeddings,
            "classification_result": classification_result
        }


    async def _classify_image(self, image_data: bytes) -> Dict[str, Any]:
        """Sends the image data to google's vision api for classification."""

        # creates an image object to pass to the vision api
        vision_image = vision.Image(content=image_data)

        # features to be requested
        features = [
            vision.Feature(type_=vision.Feature.Type.LABEL_DETECTION, max_results=10),
            vision.Feature(type_=vision.Feature.Type.IMAGE_PROPERTIES, max_results=5),
            vision.Feature(type_=vision.Feature.Type.OBJECT_LOCALIZATION, max_results=10)
        ]

        image_request = vision.AnnotateImageRequest(image=vision_image, features=features)

        # offloads the synchronous function to a thread
        try:
            response = await asyncio.to_thread(
                self.client.annotate_image,
                image_request
            )
        except GoogleAPICallError as e:
            self.logger.error("Failed to use annotate_image call")
            raise RuntimeError(f"Vision API call failed: {e}")
        
        # Convert to dictionary format
        result = {
            "labels": [
                {
                    "description": label.description.lower(),
                    "score": label.score
                } for label in response.label_annotations
            ],
            "colors": [
                {
                    "color": {
                        "red": color.color.red,
                        "green": color.color.green,
                        "blue": color.color.blue
                    },
                    "score": color.score,
                    "pixel_fraction": color.pixel_fraction
                } for color in response.image_properties_annotation.dominant_colors.colors
            ],
            "objects": [
                {
                    "name": obj.name.lower(),
                    "score": obj.score,
                    "bounding_poly": [[vertex.x, vertex.y] for vertex in obj.bounding_poly.normalized_vertices]
                } for obj in response.localized_object_annotations
            ]
        }
        self.logger.debug(f"Vision API response: {result}")
        return result
    
    
    