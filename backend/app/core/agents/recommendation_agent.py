from typing import Dict, Any, List
from .base import Agent
import chromadb
from backend.app.db.chromadb import ChromaDBClient
from backend.app.db.supabasedb import SupaBaseClient
from backend.app.models.clothing import RecommendationType
import json
 

agent_name = "recommendation_agent"

class RecommendationAgent(Agent):
    """Agent responsible for generating clothing recommendations based on user preferences."""

    def __init__(self):
        super().__init__(agent_name)
        self.logger.info("RecommendationAgent initialized")
        self.db_client = ChromaDBClient()
        self.spa_client = SupaBaseClient()
    

    async def run(self, 
                  query_item: Dict[str,Any], 
                  user_id : str, 
                  collection_name : str, 
                  bucket_name: str,
                  limit: int = 5, 
                  recommendation_type : str = "complementary") -> List[Dict[str, Any]]:
        """
        Get clothing recommendations based on a query item.

        Args:
            query_item: The item to base recommendations on (with embeddings)
            {
                "fashion_metadata": fashion_metadata,
                "embeddings": embeddings,
                "classification_result": classification_result
            }
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
        if not clothing_metadata:
            self.logger.error("No fashion metadata found in the query item")
            raise ValueError("Query item must contain fashion metadata")
        
        clothing_type = clothing_metadata.get("clothing_type", "") 
        if not clothing_type:
            self.logger.error("No clothing type found")
            raise ValueError("Query item must contain a clothing type")
        
        clothing_occasions = clothing_metadata.get("occasions", "")
        clothing_occasions = '{' + clothing_occasions + '}'
        
        if not clothing_occasions:
            self.logger.warning("No occasions found, defaulting to ['casual']")
            clothing_occasions = "casual"
        
        clothing_seasons = clothing_metadata.get("seasons", "")
        clothing_seasons = '{' + clothing_seasons + '}'
        if not clothing_seasons:
            self.logger.warning("No seasons found, defaulting to ['all']")
            clothing_seasons = "all"

        self.logger.info(f"Query item details: query_embedding: {query_embedding}, clothing_type: {clothing_type}, clothing_occasion: {clothing_occasions}, clothing_season: {clothing_seasons}")

        chroma_collection = self.db_client.get_or_create_collection(collection_name)
        supabase_client = self.spa_client  # Use the SupaBaseClient instance directly

        # based on the recommendation type, we will filter the results
        if recommendation_type == RecommendationType.SIMILAR:
            return await self._get_similar_items(chroma_collection, 
                                                 query_embedding, 
                                                 limit, 
                                                 user_id)
        
        elif recommendation_type == RecommendationType.OUTFIT:
            return await self._get_outfit(chroma_collection, 
                                          supabase_client, 
                                          query_embedding, 
                                          user_id, 
                                          limit, 
                                          clothing_type, 
                                          clothing_occasions, 
                                          clothing_seasons,
                                          bucket_name)
        else:
            raise ValueError(f"Unknown recommendation type: {recommendation_type}")


    async def _get_outfit(self, 
                          chromadb_collection: chromadb.Collection, 
                          supabase_client: SupaBaseClient,  # Changed type hint to SupaBaseClient
                          user_item_embedding: List[float], 
                          user_id: str, 
                          limit: int, 
                          clothing_type: str,
                          clothing_occasions: List[str],
                          clothing_seasons: List[str],
                          bucket_name: str) -> List[Dict[str, Any]]: 
        """Create a simple outfit based on the queired clothing items."""
        self.logger.info(f"Creating a simple outfit for user {user_id} which is a {clothing_type} and has these ocasions -> {clothing_occasions} as well for these season -> {clothing_seasons}")

        # Query the supabase database for clothing items that match the user's wardrobe and the specified filters
        supabase_query_result = supabase_client.get_supabase_client().table("clothing_items").select("embedding_id", "image_path").filter(
            "user_id", "eq", user_id
        ).filter(
            "type", "neq", clothing_type  # Exclude the same clothing type
        ).filter(
            "occasions", "ov", clothing_occasions
        ).filter(
            "seasons", "ov",  clothing_seasons
        ).execute()

        self.logger.info(f"Supabase query result found {len(supabase_query_result.data)} matching clothing items -> {supabase_query_result.data}")

        if not supabase_query_result.data:
            raise ValueError("No clothing items data found in the user's wardrobe matching the supabase query")
        
        # Extract the embedding IDs from the supabase query result to use in the ChromaDB query
        embedding_ids = [item["embedding_id"] for item in supabase_query_result.data]

        if not embedding_ids:
            self.logger.error("No embedding IDs found in the supabase query result")
            raise ValueError("No embedding IDs found in the supabase query result")
        
        self.logger.info(f"Embedding IDs for outfit recommendations: {embedding_ids}, total count: {len(embedding_ids)}")

        # Query the ChromaDB collection for similar items based on the user's item embedding
        try:
            n_results = min(limit, len(embedding_ids))
            self.logger.info(f"Requesting {n_results} results from ChromaDB (limit: {limit}, available ids: {len(embedding_ids)})")
            
            outfit_items = chromadb_collection.query(
                query_embeddings=[user_item_embedding],
                ids=embedding_ids,  # Use the embedding IDs from the supabase query
                n_results=n_results,
                include=["metadatas", "distances"]
            )

            recommended_ids = outfit_items.get("ids",[[]])
            self.logger.info(f"Found {len(recommended_ids[0])} number of items for outfit recommendations -> {outfit_items}")
            
            if not outfit_items or len(outfit_items.get("ids", [[]])[0]) == 0:
                raise ValueError("No outfit items found in the user's wardrobe matching query from chromadb")

            self.logger.info(f"Recommended IDs for outfit: {recommended_ids}")

            file_paths = self._get_file_paths_from_recommendation(
                supabase_query_result.data, 
                recommended_ids[0], 
                bucket_name
            )

            # go through and get each of the url paths of recommendation items to return to users
            image_urls = []
            for file_path in file_paths:
                # Use your wrapper method
                image_url = supabase_client.get_public_url(bucket_name, file_path)
                image_urls.append(image_url)
            
            if not image_urls:
                raise ValueError("Could not get the urls from the recommendations")
            
            self.logger.info(f"Got these urls from the reccommedations {image_urls}")

            outfit_items["image_urls"] = image_urls

            return self._format_results(outfit_items)
        
        except Exception as e:
            raise RuntimeError(f"Error querying for outfit recommendations for user {user_id}: {str(e)} from chromadb and supabase")


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
    

    def _get_file_paths_from_recommendation(self, supabase_data: List[Dict[str, Any]], recommended_ids: List[str], bucket_name: str) -> List[str]:
        """Get file paths for the recommended items."""
        file_paths = []
        for item in supabase_data:
            if item.get("embedding_id") in recommended_ids:
                file_paths.append(item.get("image_path"))
        return file_paths


    def _format_results(self, results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Format the results from the database query."""
        formatted_results = []
        
        # to get the single query results we need to get the first element of the list since chromadb returns a list of lists
        ids = results.get("ids", [])[0]
        metadatas = results.get("metadatas", [])[0]
        distances = results.get("distances", [[]])[0]
        image_urls = results.get("image_urls", [])

        for index, item_id in enumerate(ids):
           metadata = metadatas[index] if index < len(metadatas) else {}
           distance = distances[index] if index < len(distances) else None
           image_url = image_urls[index] if index < len(image_urls) else None
           
           try:
               formatted_results.append({
                   "item_id": item_id,
                   "metadata": metadata,
                   "distance": distance,
                   "image_url": image_url
                   })
           
           except json.JSONDecodeError:
                self.logger.error(f"Error decoding items : {item_id}")
                formatted_results.append({
                "item_id": item_id,
                "metadata": metadata
             })

        self.logger.info(f"New formatted results {formatted_results}")
        return formatted_results