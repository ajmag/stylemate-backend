from typing import Dict, Any, List
from .base import Agent
import chromadb
from backend.app.db.chromadb import ChromaDBClient
from backend.app.models.clothing import RecommendationType
import json
import numpy as np
 

agent_name = "recommendation_agent"

class RecommendationAgent(Agent):
    """Agent responsible for generating clothing recommendations based on user preferences."""

    def __init__(self):
        super().__init__(agent_name)
        self.logger.info("RecommendationAgent initialized")
        self.db_client = ChromaDBClient()
    

    async def run(self, 
                  query_item: Dict[str,Any], 
                  user_id : str, 
                  collection_name : str, 
                  limit: int = 5, 
                  recommendation_type : str = "complementary") -> List[Dict[str, Any]]:
        """
        Get clothing recommendations based on a query item.

        Args:
            query_item: The item to base recommendations on (with embeddings)
            user_id: The user ID for filtering their wardrobe
            limit: Maximum number of recommendations to return
            recommendation_type: Type of recommendation ("similar", "complementary", "outfit")

        Returns:
            List of recommended clothing items
        """
        self.logger.info(f"Getting {recommendation_type} recommendations for user {user_id}")

        query_embedding = query_item.get("embeddings", "")
        if not query_embedding:
            self.logger.error("No embeddings found in the query item")
            raise ValueError("Query item must contain embeddings")
        
        clothing_metadata = query_item.get("fashion_metadata", "") # not working FIXME
        clothing_type = clothing_metadata.get("clothing_type", "") 
        if not clothing_type:
            self.logger.error("No clothing type found")
            raise ValueError("Query item must contain a clothing type")

        collection = self.db_client.get_or_create_collection(collection_name)

        # based on the recommendation type, we will filter the results
        if recommendation_type == RecommendationType.SIMILAR:
            return await self._get_similar_items(collection, query_embedding, limit, user_id)
        elif recommendation_type == RecommendationType.OUTFIT:
            return await self._get_outfit(collection, query_embedding, user_id, limit, clothing_type)
        else:
            raise ValueError(f"Unknown recommendation type: {recommendation_type}")
        
    
    async def _get_similar_items(self, collection: chromadb.Collection, 
                                 query_embedding: List[float], 
                                 limit: int, 
                                 user_id: str) -> List[Dict[str, Any]]:
        """Get similar items based on the query embedding."""
        self.logger.info("Getting similar items")

        try:
            similar_items = collection.query(
                query_embeddings=[query_embedding],
                n_results=limit,
                where={"user_id": user_id},
                include=["metadatas", "distances"]  
            )
            self.logger.info(f"Found similar items {similar_items}")
            
            return self._format_results(similar_items)
        
        except Exception as e:
            self.logger.error(f"Error querying similar items for user {user_id}: {str(e)}")
            raise RuntimeError(f"Error querying similar items for user {user_id}: {str(e)}")

    
    async def _get_outfit(self, 
                          collection: chromadb.Collection, 
                          query_embedding: List[float], 
                          user_id: str, 
                          limit: int, 
                          clothing_type: str) -> List[Dict[str, Any]]: #FIXME 
        """Create a simple outfit based on the queired clothing items."""
        self.logger.info("Creating a simple outfit")

        try:
            outfit_items = collection.query(
                query_embeddings=[query_embedding],
                n_results=limit,
                where={
                    "$and": [
                            {"user_id": "test_user"},
                            {"clothing_type": {"$ne": "bottom"}}
                        ]
                    },
                include=["metadatas", "distances"]
            )
            self.logger.info(f"Found items for outfit items {outfit_items}")
            
            return self._format_results(outfit_items)
        
        except Exception as e:
            self.logger.error(f"Error querying similar items for user {user_id}: {str(e)}")
            raise RuntimeError(f"Error querying similar items for user {user_id}: {str(e)}")        
    

    def _format_results(self, results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Format the results from the database query."""
        formatted_results = []
        
        # to get the single query results we need to get the first element of the list since chromadb returns a list of lists
        ids = results.get("ids", [])[0]
        metadatas = results.get("metadatas", [])[0]
        distances = results.get("distances", [[]])[0]

        for index, item_id in enumerate(ids):
           metadata = metadatas[index] if index < len(metadatas) else {}
           distance = distances[index] if index < len(distances) else None
           
           try:
               formatted_results.append({
                   "item_id": item_id,
                   "metadata": metadata,
                   "distance": distance
                   })
           
           except json.JSONDecodeError:
                self.logger.error(f"Error decoding items : {item_id}")
                formatted_results.append({
                "item_id": item_id,
                "metadata": metadata
             })

        return formatted_results