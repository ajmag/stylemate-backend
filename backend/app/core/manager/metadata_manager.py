from typing import Dict, Any, List, Tuple
import logging
from app.core.mapping.clothing_mappings import (CLOTHING_TYPE_MAPPING, CLOTHING_CATEGORY_MAPPING, DEFAULT_CATEGORIES, COLOR_MAPPING, PATTERN_KEYWORDS,SEASON_MAPPING, SEASON_FABRIC_MAPPING, COLOR_SEASON_MAPPING, OCCASION_MAPPING)
from app.models.clothing import ClothingType, ClothingCategory, Season, Occasion
from skimage import color
import numpy as np


class ClothingMetadataManager:

    def __init__(self):
        """Initialize the clothing metadata manager."""
        self.logger = logging.getLogger(__name__)
        self.logger.info("ClothingMetadataManager initialized")

    def extract_clothing_metadata(self, api_result: Dict[str, Any]) -> Dict[str, Any]: 
            """Extract clothing type, category, color, pattern from API results."""
            self.logger.info("Starting metadata extraction")

            result = {
                "clothing_type": ClothingType.TOP,  # Default type
                "category": ClothingCategory.SHIRT,  # Default category
                "color_primary": "black",  # Default color
                "color_secondary": None,
                "pattern": "solid",  # Default pattern
                "seasons": [Season.ALL],  # Default season
                "occasions": [Occasion.CASUAL],  # Default occasion
                "description": None
            }

            clothing_type = self._determine_clothing_type(api_result)
            if clothing_type:
                result["clothing_type"] = clothing_type
            
            clothing_category = self._determine_clothing_category(api_result, clothing_type)
            if clothing_category:
                result["category"] = clothing_category
            
            clothing_colors = self._extract_dominant_colors(api_result)
            if clothing_colors:
                result["color_primary"] = clothing_colors[0]
                if len(clothing_colors) > 1: 
                    result["color_secondary"] = clothing_colors[1]
            
            clothing_pattern = self._determine_pattern(api_result)
            if clothing_pattern:
                result["pattern"] = clothing_pattern

            clothing_season = self._determine_seasons(api_result)
            if clothing_season:
                result["seasons"] = clothing_season
            
            clothing_occasion = self._determine_occasions(api_result, result["clothing_type"], result["pattern"])
            if clothing_occasion:
                result["occasions"] = clothing_occasion
            
            result["description"] = self._generate_description(result)

            self.logger.info(f"Extracted metadata: {result}")
            return result
    

    def _process_vision_labels(self, api_result: Dict[str, Any], keyword_mapping: Dict, object_weight: float = 1.5) -> Dict[Any, float]:
            """Generic method to process labels and objects against a keyword mapping."""
            self.logger.debug(f"Processing vision labels with keyword mapping: {list(keyword_mapping.keys())}")

            scores = {category: 0.0 for category in keyword_mapping.keys()}

            # Process labels
            for label in api_result.get("labels", []):
                label_name = label["description"]
                label_score = label["score"]

                for category, keywords in keyword_mapping.items():
                    if any(keyword in label_name for keyword in keywords):
                        scores[category] += label_score

            #Process objects 
            for obj in api_result.get("objects", []):
                obj_name = obj["name"]
                obj_score = obj["score"]
            
                for category, keywords in keyword_mapping.items():
                    if any(keyword in obj_name for keyword in keywords):
                        # objects are more reliable so are weighted more
                        scores[category] += obj_score * object_weight
            
            self.logger.debug(f"Processed scores: {scores}")
            return scores


    def _determine_clothing_type(self, api_result: Dict[str, Any]) -> ClothingType:
        """Identify clothing type from Vision API results."""
        self.logger.debug("Determining clothing type")

        # Mapping of Vision API labels/objects to our ClothingType enum
        clothing_type_keywords = CLOTHING_TYPE_MAPPING

        # Dict to keep scores from api results
        types_score = self._process_vision_labels(api_result, clothing_type_keywords)
        
        # return the clothing type with highest score
        if any(types_score.values()):
            self.logger.debug(f"Clothing type scores: {types_score}")
            return max(types_score.items(), key=lambda x: x[1])[0]
        
        # default return 
        return ClothingType.TOP


    def _get_default_category(self, clothing_type: ClothingType) -> ClothingCategory:
        """Return a default category for a given clothing type."""
        self.logger.debug(f"Getting default category for clothing type: {clothing_type}")

        default_categories = DEFAULT_CATEGORIES
        return default_categories.get(clothing_type, ClothingCategory.SHIRT)


    def _determine_clothing_category(self, api_result: Dict[str, Any], clothing_type: ClothingType) -> ClothingCategory:
        """Determine specific clothing category based on labels and detected clothing type."""
        self.logger.debug(f"Determining clothing category for type: {clothing_type}")
        
        
        # Mapping of keywords to specific categories based on clothing type
        category_keywords = CLOTHING_CATEGORY_MAPPING

        # If we don't have mappings for this clothing type, return a default
        if clothing_type not in category_keywords:
            return self._get_default_category(clothing_type)

        category_scores = self._process_vision_labels(api_result, category_keywords[clothing_type])
        
        # Find the category with the highest score
        if any(category_scores.values()):
            self.logger.debug(f"Clothing category scores: {category_scores}")
            return max(category_scores.items(), key=lambda x: x[1])[0]

        # Return a default category for the detected clothing type
        self.logger.debug(f"No specific category detected, defaulting to {self._get_default_category(clothing_type)}")
        return self._get_default_category(clothing_type)


    def _find_closest_color(self, rgb: Tuple[int, int, int]) -> str:
        """Find the nearest color using a simple Euclidean distance."""
        self.logger.debug(f"Finding closest color for RGB: {rgb}")
        
        color_reference = COLOR_MAPPING
        min_dist = float("inf")
        nearest_color = "unknown"
        lab_color = color.rgb2lab([[rgb]])[0][0]

        for color_name, color_value in color_reference.items():
            lab_ref = color.rgb2lab([[color_value]])[0][0]

            # Calculate delta E (color difference)
            distance = np.sqrt(sum((lab_color - lab_ref) ** 2))

            if distance < min_dist:
                min_dist = distance
                nearest_color = color_name
        
        if min_dist > 25:
            self.logger.warning(f"Poor color match for {rgb}: {nearest_color} with distance {min_dist}")
    
        self.logger.debug(f"Nearest color for {rgb} is {nearest_color} with distance {min_dist}")
        return nearest_color


    def _extract_dominant_colors(self, api_result: Dict[str, Any]) -> List[str]:
        """Extract dominant colors from Vision API results."""
        self.logger.debug("Extracting dominant colors")

        color_results = api_result.get("colors", [])

        if not color_results:
            return ["unknown"]
        
        named_colors = []

        for color_data in color_results[:5]:
            rgb = (
                int(color_data["color"]["red"]),
                int(color_data["color"]["green"]),
                int(color_data["color"]["blue"])
            )

            color_name = self._find_closest_color(rgb)

            if color_name not in named_colors:
                named_colors.append(color_name)

        self.logger.debug(f"Extracted colors: {named_colors}") 
        return named_colors


    def _determine_pattern(self, api_result: Dict[str, Any]) -> str:
        """Determine if the clothing has patterns."""
        self.logger.debug("Determining pattern")
        
        pattern_keywords = PATTERN_KEYWORDS

        pattern_scores = self._process_vision_labels(api_result, pattern_keywords)

        colors = api_result.get("colors", [])

        if len(colors) >= 2:
            pixel_fractions = [color["pixel_fraction"] for color in colors[:3]]

            # For 2 colors
            if len(colors) == 2:
                # If two colors have relatively similar prominence (neither dominates)
                if max(pixel_fractions) < 0.7 and min(pixel_fractions) > 0.2:
                    for pattern in pattern_scores:
                        # Gives a boost to all pattern not solid 
                        if pattern != "solid":
                            pattern_scores[pattern] += 0.2
            
            # For 3+ color patterns 
            else:
                if max(pixel_fractions) < 0.5 and min(pixel_fractions) > 0.1:
                    for pattern in pattern_scores:
                        if pattern != "solid":
                            pattern_scores[pattern] += 0.2

        if any(pattern_scores.values()):
            self.logger.debug(f"Pattern scores: {pattern_scores}")
            return max(pattern_scores.items(), key=lambda x: x[1])[0]
        
        # return default pattern 
        self.logger.debug("No pattern detected, defaulting to solid")
        return "solid"


    def _determine_seasons(self, api_result: Dict[str, Any]) -> List[Season]:
        """Determine appropriate seasons for the clothing item."""
        self.logger.debug("Determining seasons")

        season_keywords = SEASON_MAPPING
        fabric_mapping = SEASON_FABRIC_MAPPING
        color_mapping = COLOR_SEASON_MAPPING

        season_scores = {season: 0.0 for season in Season}

        # Process direct season keywords
        keyword_scores = self._process_vision_labels(api_result, SEASON_MAPPING)
        for season, score in keyword_scores.items():
            season_scores[season] += score
        
        # Process fabrics 
        fabric_scores = self._process_vision_labels(api_result, SEASON_FABRIC_MAPPING, 0.3)
        for season, score in fabric_scores.items():
            season_scores[season] += score

        # Consider color information for seasonal hints
        colors = self._extract_dominant_colors(api_result)

        # Process top two colors
        for color_name in colors[:2]:
            for season, seasonal_color in color_mapping.items():
                if color_name in seasonal_color:
                    season_scores[season] += 0.2
        
        detected_seasons = [season for season, score in season_scores.items() if score > 0.2]
        
        if not detected_seasons:
            self.logger.debug("No specific seasons detected, defaulting to all seasons")
            return[Season.ALL]

        self.logger.debug(f"Season scores: {season_scores}")
        return detected_seasons
        
        
    def _determine_occasions(self, api_result: Dict[str, Any], clothing_type: ClothingType, pattern: str) -> List[Occasion]:
        """Determine appropriate occasions for the clothing item."""
        self.logger.debug(f"Determining occasions for type={clothing_type}, pattern={pattern}")


        occasion_mapping = OCCASION_MAPPING

        occasion_scores = self._process_vision_labels(api_result, occasion_mapping)

        # Apply heuristics based on clothing type and pattern
        self._apply_occasion_heuristics(occasion_scores, clothing_type, pattern)

        # Get occasions with scores above a threshold (0.15)
        detected_occasions = [occasion for occasion, score in occasion_scores.items() if score > 0.15]

        # Default to casual if no occasions are detected
        if not detected_occasions:
            self.logger.debug("No specific occasions detected, defaulting to casual")
            return [Occasion.CASUAL]
        
        self.logger.debug(f"Occasion scores: {occasion_scores}")
        return detected_occasions


        
    def _apply_occasion_heuristics(self, occasion_scores: Dict[Occasion, float], clothing_type: ClothingType, pattern: str):
        """Apply heuristic rules to occasion scores based on clothing type and pattern."""
        self.logger.debug("Applying occasion heuristics")

        # Default casual boost - most clothes work for casual settings
        occasion_scores[Occasion.CASUAL] += 0.1
        
        # Type-based rules
        if clothing_type == ClothingType.TOP:
            occasion_scores[Occasion.CASUAL] += 0.1
            occasion_scores[Occasion.BUSINESS] += 0.1
        elif clothing_type == ClothingType.BOTTOM:
            occasion_scores[Occasion.BUSINESS] += 0.1
        elif clothing_type == ClothingType.DRESS:
            occasion_scores[Occasion.FORMAL] += 0.2
            occasion_scores[Occasion.SPECIAL] += 0.2
        elif clothing_type == ClothingType.OUTERWEAR:
            occasion_scores[Occasion.CASUAL] += 0.1
            occasion_scores[Occasion.BUSINESS] += 0.1
        elif clothing_type == ClothingType.FOOTWEAR:
            occasion_scores[Occasion.CASUAL] += 0.1
            occasion_scores[Occasion.BUSINESS] += 0.1
        elif clothing_type == ClothingType.ACCESSORY:
            occasion_scores[Occasion.SPECIAL] += 0.1
            occasion_scores[Occasion.FORMAL] += 0.1
        
        # Pattern-based rules
        if pattern == "solid":
            for occasion in Occasion:
                occasion_scores[occasion] += 0.1
        elif pattern == "graphic":
            occasion_scores[Occasion.CASUAL] += 0.3
            occasion_scores[Occasion.SPORT] += 0.2
            occasion_scores[Occasion.FORMAL] -= 0.2  # Reduce formal score
            occasion_scores[Occasion.BUSINESS] -= 0.1  # Reduce business score
        elif pattern == "floral":
            occasion_scores[Occasion.CASUAL] += 0.2
            occasion_scores[Occasion.SPECIAL] += 0.1
        elif pattern == "striped":
            occasion_scores[Occasion.BUSINESS] += 0.2
            occasion_scores[Occasion.CASUAL] += 0.1
        elif pattern == "checked":
            occasion_scores[Occasion.BUSINESS] += 0.2
            occasion_scores[Occasion.CASUAL] += 0.2
        elif pattern == "polka_dot":
            occasion_scores[Occasion.SPECIAL] += 0.2
            occasion_scores[Occasion.CASUAL] += 0.2
            occasion_scores[Occasion.FORMAL] -= 0.1
        elif pattern == "animal":
            occasion_scores[Occasion.CASUAL] += 0.2
            occasion_scores[Occasion.SPECIAL] += 0.1
            occasion_scores[Occasion.BUSINESS] -= 0.2
        
        # Special combinations for enhanced accuracy
        if clothing_type == ClothingType.TOP and pattern == "graphic":
            occasion_scores[Occasion.SPORT] += 0.1  # Graphic tees are often sporty
        if clothing_type == ClothingType.DRESS and pattern in ["solid", "floral"]:
            occasion_scores[Occasion.SPECIAL] += 0.1  # Solid/floral dresses for special occasions
        if clothing_type in [ClothingType.TOP, ClothingType.BOTTOM] and pattern == "solid":
            occasion_scores[Occasion.BUSINESS] += 0.1  # Solid tops/bottoms for business
        

    def _generate_description(self, metadata: Dict[str, Any]) -> str:
        """Generate a human-readable description of the clothing item."""
        self.logger.debug("Generating clothing description")
        
        # Extract key metadata
        color_primary = metadata.get("color_primary", "unknown")
        color_secondary = metadata.get("color_secondary")
        pattern = metadata.get("pattern", "solid")
        category = metadata.get("category", "item").value  # Get string value of enum
        clothing_type = metadata.get("clothing_type", "clothing")  
        seasons = metadata.get("seasons", [Season.ALL])
        occasions = metadata.get("occasions", [Occasion.CASUAL])

        if color_secondary:
            color_description = f"{color_primary} and {color_secondary}"
        else:
            color_description = color_primary
        
        # Format pattern description (only mention if not solid)
        pattern_description = f"{pattern}" if pattern != "solid" else ""

        # Base of the description
        description = f"A {color_description} {pattern_description} {category} {clothing_type}"

        # Add season information if specific
        if len(seasons) == 1 and seasons[0] != Season.ALL:
            description += f" for {seasons[0].value} wear"
        elif len(seasons) > 1 and Season.ALL not in seasons:
            season_list = [season.value for season in seasons]
            description += f" suitable for {', '.join(season_list[:-1])} and {season_list[-1]}"

        # Add occasion information (filtering out CASUAL since it's implied)
        filtered_occasions = [occasion for occasion in occasions if occasion != Occasion.CASUAL]
        if filtered_occasions:
            occasion_list = [occasion.value for occasion in filtered_occasions]
            if len(occasion_list) == 1:
                description += f", perfect for {occasion_list[0]} occasions"
            else:
                description += f", perfect for {', '.join(occasion_list[:-1])} and {occasion_list[-1]} occasions"

        self.logger.debug(f"Generated description: {description}") 
        return description