from scipy.spatial import KDTree
import numpy as np
from skimage import color
from typing import Dict, Tuple, List
import logging
from backend.app.core.mapping.clothing_mappings import COLOR_FAMILY_MAPPING


class ColorMatcher:
    """Efficient color matching using KD-Trees for fast nearest neighbor searches."""
     
    def __init__(self, color_mapping: Dict[str, Tuple[int, int, int]]):
        self.logger = logging.getLogger(__name__)
        self.logger.info("Initializing ClothingMatcher with color mapping.")

        self.color_mapping = color_mapping
        self.color_names = list(color_mapping.keys())

        # Create reverse mapping for quick lookups
        self.color_to_family = {}
        for family, colors in COLOR_FAMILY_MAPPING.items():
            for color_name in colors:
                self.color_to_family[color_name] = family

        # Convert all RGB values to LAB at initialization time
        self._precompute_lab_values()


    def _precompute_lab_values(self):
        """Precompute LAB Values for all reference colors and build KDTree""" 
        self.logger.debug("Precomputing LAB values for color mapping.")

        # Extract RGB values as a numpy array
        rgb_values = np.array(list(self.color_mapping.values()))

        # Normalize RGB values to 0-1 range
        normalized_rgb = rgb_values / 255.0

         # Convert all colors to LAB
        self.lab_values = np.array([
            color.rgb2lab(rgb.reshape(1, 1, 3))[0][0] 
            for rgb in normalized_rgb
        ])
        
        # Precompute HSV values
        self.hsv_values = np.array([
            color.rgb2hsv(rgb.reshape(1, 1, 3))[0][0]
            for rgb in normalized_rgb
        ])
        
        # Build KDTree for fast nearest neighbor search
        self.lab_tree = KDTree(self.lab_values)
        
        self.logger.debug(f"Built KDTree with {len(self.color_names)} colors")
    

    def find_color_match(self, rgb: Tuple[int, int, int]) -> Dict[str, str]:
        """Find both the specific color and its general family for an RGB value.
        
        Returns:
            A dictionary with 'specific_color' and 'color_family' keys
        """
        self.logger.debug(f"Finding color match for RGB: {rgb}")
        
        # Get the specific color
        specific_color = self._find_closest_color(rgb)
        
        # Get the color family
        color_family = self._get_color_family(specific_color)
        
        result = {
            "specific_color": specific_color,
            "color_family": color_family
        }
        
        self.logger.debug(f"Color match for RGB {rgb}: {result}")
        return result
    

    def _get_color_family(self, specific_color: str) -> str:
        """Get the general color family for a specific color name."""
        if specific_color in self.color_to_family:
            return self.color_to_family[specific_color]
        else:
            self.logger.warning(f"No color family found for '{specific_color}'")
            # Default to the specific color if no family mapping exists
            return specific_color
    
    
    def _find_closest_color(self, rgb: Tuple[int, int, int]) -> str:
        """Find the nearest color using KDTree in LAB color space."""
        self.logger.debug(f"Finding closest color for RGB: {rgb}")
        
        for color_name, color_value in self.color_mapping.items():
            if rgb == color_value:
                self.logger.debug(f"Exact color match found: {color_name}")
                return color_name
        
        # Convert queried RGB to LAB and HSV
        rgb_normalized = np.array(rgb) / 255.0
        lab_color = color.rgb2lab(rgb_normalized.reshape(1, 1, 3))[0][0]
        hsv_color = color.rgb2hsv(rgb_normalized.reshape(1, 1, 3))[0][0]

        # Query the KDTree for the nearest neighbors
        distances, indices = self.lab_tree.query(lab_color, k=3)

        if distances[0] < 15:
            closest_color = self.color_names[indices[0]]
            self.logger.debug(f"Closest color found: {closest_color} with distance {distances[0]}")
            return closest_color
        
        # For each candidate, calculate a weighted distance that better handles edge cases
        best_match = None
        best_score = float('inf')

        for idx, lab_ditances in zip(indices, distances):
            name = self.color_names[idx]
            hsv_ref = self.hsv_values[idx]

            # Calculate HSV component distances
            # Hue is circular (0-1), so we need special handling
            h_dist = min(abs(hsv_color[0] - hsv_ref[0]), 1 - abs(hsv_color[0] - hsv_ref[0]))
            s_dist = abs(hsv_color[1] - hsv_ref[1])
            v_dist = abs(hsv_color[2] - hsv_ref[2])

            # Weight hue more for saturated colors, value more for dark/light colors
            if hsv_color[1] > 0.7:
                hsv_distance = h_dist * 2.0 + s_dist * 1.0 + v_dist * 0.5
            elif hsv_color[2] < 0.3:
                hsv_distance = h_dist * 0.5 + s_dist * 0.5 + v_dist * 2.0
            else:
                hsv_distance = h_dist * 1.0 + s_dist * 1.0 + v_dist * 1.0
            
            # Combined score (LAB + HSV)
            combined_distance = (lab_ditances * 0.7) + (hsv_distance * 10)

            if combined_distance < best_score:
                best_score = combined_distance
                best_match = name
        
        self.logger.debug(f"Nearest color for {rgb} is {best_match} with distance {best_score}")
        return best_match
    

    def get_color_characteristics(self, rgb: Tuple[int, int, int]) -> Dict[str, bool]:
        """Analyze color characteristics based on HSV values."""
        rgb_normalized = np.array(rgb) / 255.0
        hsv_color = color.rgb2hsv(rgb_normalized.reshape(1, 1, 3))[0][0]
        h, s, v = hsv_color
        
        return {
            "is_light": v > 0.7,
            "is_dark": v < 0.3,
            "is_saturated": s > 0.7,
            "is_muted": s < 0.3,
            "is_warm": (h < 0.1 or h > 0.8),  # reds, oranges, yellows
            "is_cool": (0.4 < h < 0.7),       # greens, blues
            "is_neutral": s < 0.15,
            "is_pastel": s < 0.5 and v > 0.7,
            "is_vibrant": s > 0.7 and v > 0.7
        }
    

    #TODO
    def get_complementary_colors(self, color_family: str, specific_color: str = None) -> List[str]:
        """Get complementary color families that would work well with the given color."""
        pass 
        

            
