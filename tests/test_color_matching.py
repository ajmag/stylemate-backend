import unittest
import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import the necessary modules
from backend.app.core.manager.color_matching_manager import ColorMatcher
from backend.app.core.mapping.clothing_mappings import COLOR_MAPPING

class TestSimpleColorMatcher(unittest.TestCase):
    """Simple test suite for hierarchical color matching."""

    def setUp(self):
        """Set up the test case."""
        self.color_matcher = ColorMatcher(COLOR_MAPPING)
    
    def test_basic_color_family_identification(self):
        """Test basic mapping of colors to their families."""
        # Basic test cases with common colors
        test_cases = [
            ((220, 50, 50), "red"),       # Red -> Red family
            ((25, 50, 120), "navy"),      # Navy -> Navy family
            ((210, 180, 140), "tan"),     # Tan -> Tan family
            ((0, 128, 0), "green"),       # Green -> Green family
            ((255, 255, 0), "yellow")     # Yellow -> Yellow family
        ]
        
        for rgb, expected_family in test_cases:
            result = self.color_matcher.find_color_match(rgb)
            self.assertEqual(result["color_family"], expected_family,
                            f"Expected color family {expected_family} for RGB {rgb}, got {result['color_family']}")
    
    def test_color_characteristics(self):
        """Test basic detection of color characteristics."""
        # Test case for a vibrant red color
        rgb = (255, 0, 0)
        characteristics = self.color_matcher.get_color_characteristics(rgb)
        
        # Check key characteristics
        self.assertTrue(characteristics["is_vibrant"], 
                       f"RGB {rgb} should be identified as vibrant")
        self.assertTrue(characteristics["is_saturated"], 
                       f"RGB {rgb} should be identified as saturated")
        self.assertTrue(characteristics["is_warm"], 
                       f"RGB {rgb} should be identified as warm")
        
        # Test case for a dark color
        rgb = (20, 20, 50)
        characteristics = self.color_matcher.get_color_characteristics(rgb)
        self.assertTrue(characteristics["is_dark"], 
                       f"RGB {rgb} should be identified as dark")
    
    def test_specific_and_family_match(self):
        """Test that specific colors and their families are correctly identified."""
        for specific_color, rgb_value in COLOR_MAPPING.items():
            result = self.color_matcher.find_color_match(rgb_value)
            
            # Verify specific color match
            self.assertEqual(result["specific_color"], specific_color,
                            f"Expected specific color {specific_color} for RGB {rgb_value}")
            
            # Verify the color has a family
            self.assertIsNotNone(result["color_family"],
                                f"Color {specific_color} should have a family assigned")
            
            # Verify family match through direct method
            direct_family = self.color_matcher._get_color_family(specific_color)
            self.assertEqual(result["color_family"], direct_family,
                            f"Color family mismatch: got {result['color_family']} from match but {direct_family} from direct lookup")

if __name__ == '__main__':
    unittest.main()