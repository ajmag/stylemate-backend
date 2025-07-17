import logging
from typing import Dict, Any, List, Optional

from backend.app.core.agents.vision_agent import VisionProcessingAgent
from backend.app.core.agents.recommendation_agent import RecommendationAgent 
from backend.app.db.supabasedb import SupaBaseClient
from backend.app.db.chromadb import ChromaDBClient


class RecommendationService:
    """
    Service for handling recommendation operations.
    This contains all the business logic separated from the API routes.
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)

        # Constants - move these to config later
        self._testing_user_id = "test_user"
        self._bucket_name = "clothing-images"
        self._collection_name = "clothing_items"
        self._database_name = "clothing_items"


    async def get_outfit_recommendation(self,
                                        image_data: bytes,
                                        file_name: str,
                                        user_id: str, 
                                        limit: int = 5, 
                                        recommendation_type: str = "outfit"):
        """
        Process an image and get recommendations based on it.
        """

        try:
            # Step 1: Process the image with Vision Agent
            self.logger.info("Processing image with VisionProcessingAgent")

            vision_agent = RecommendationAgent()
            vision_result = vision_agent.run(
                query_item={image_data}, 
                user_id=user_id
            )

            # Step 2: Get recommendations using RecommendationAgent
            self.logger.info("Getting recommendations with RecommendationAgent")

            recommendation_agent = RecommendationAgent()
            recommendations = await recommendation_agent.run(
                query_item=vision_result,
                user_id =user_id,
                bucket_name = self._bucket_name,
                limit=5,
                collection_name= self._collection_name,
                recommendation_type= recommendation_type,
            )

            # Step 3: Return structured response
            return {
                "query_item": vision_result["fashion_metadata"],
                "recommendations": recommendations,
                "recommendation_type": recommendation_type,
                "total_found": len(recommendations) if recommendations else 0
            }
            
        except Exception as e:
            self.logger.exception(f"Error getting recommendations from image: {str(e)}")
            raise RuntimeError(f"Error getting recommendations from image: {str(e)}")



