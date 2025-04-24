import logging
from typing import Dict, Any, List
from app.models.clothing import ClothingType, Season, Occasion

class ClothingEmbeddingManager:
    """Manager for handling clothing image embeddings.
    We will use a simple embedding method for the MVP of the project.
    In the future, we can use more advanced methods like CLIP or other models.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.logger.info("ClothingEmbeddingManager initialized")

    def generate_embedding(self, metadata: Dict[str, Any], api_result: Dict[str, Any]) -> List[float]:
        """Genereate a simple embedding for the clothing image."""
        self.logger.info("Generating embedding")

        embedding = [0.0] * 64

        # Incorporate label information (first 10 dimensions)
        for index, label in enumerate(api_result.get("labels", [])[:10]):
            embedding[index] = label.get("score", 0.0)
        
        # Incorporate object detection information (next 5 dimensions)
        for index, obj in enumerate(api_result.get("objects", [])[:5]):
            embedding[index + 10] = obj.get("score", 0.0)
        
        # Incorporate color information (next 6 dimensions)
        colors = api_result.get("colors", [])
        for index, color in enumerate(colors[:2]):
            base_idx = 15 + (index * 3)
            # Normalize color values to [0, 1]
            embedding[base_idx] = color["color"]["red"] / 255
            embedding[base_idx + 1] = color["color"]["green"] / 255
            embedding[base_idx + 2] = color["color"]["blue"] / 255

        # Incorporate clothing type one-hot encoding (next 6 dimensions)
        clothing_type = metadata.get("clothing_type", "")
        if clothing_type:
            type_index = 21 + list(ClothingType).index(clothing_type) # will get the index of the clothing type to set
            if type_index < 27:  # Safety check
                embedding[type_index] = 1.0
        
        # Incorporate pattern one-hot encoding (next 10 dimensions)
        pattern = metadata.get("pattern", "")
        if pattern:
            # Define a mapping for patterns to indices in expected order 
            patterns = [ 
                "solid", "striped", "checked", "polka_dot", "floral",
                "graphic", "animal", "geometric", "camo", "tie_dye"
            ]
            if pattern in patterns:
                pattern_index = 27 + patterns.index(pattern)
                embedding[pattern_index] = 1.0
        
        # Incorporate seasons (next 5 dimensions)
        seasons = metadata.get("seasons", [])
        seasons_mapping = {
            Season.SPRING : 37,
            Season.SUMMER : 38,
            Season.FALL : 39,
            Season.WINTER : 40,
            Season.ALL : 41
        }
        for season in seasons:
            if season in seasons_mapping:
                embedding[seasons_mapping[season]] = 1.0

        # Incorporate occasions (next 5 dimensions)
        ocasions = metadata.get("occasions", [])
        occasions_mapping = {
            Occasion.CASUAL : 42,
            Occasion.FORMAL : 43,
            Occasion.BUSINESS : 44,
            Occasion.SPORT : 45,
            Occasion.SPECIAL : 46
        }
        for occasion in ocasions:
            if occasion in occasions_mapping:
                embedding[occasions_mapping[occasion]] = 1.0
        
        # Normalize the embedding
        norm = sum(x ** 2 for x in embedding) ** 0.5 # Calculating euclidean norm/magnitude
        if norm > 0:
            embedding = [x / norm for x in embedding] # Normalize to unit vector
         
        self.logger.info(f"Embedding generated successfully : {embedding}")
        return embedding


        