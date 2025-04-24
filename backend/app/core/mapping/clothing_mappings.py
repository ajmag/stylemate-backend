# app/core/mapping/clothing_mapping.py
from app.models.clothing import ClothingType, ClothingCategory, Season, Occasion

# Mapping of keywords to clothing types
CLOTHING_TYPE_MAPPING = {
    ClothingType.TOP: ["shirt", "t-shirt", "blouse", "top", "polo", "sweater", "sweatshirt", "hoodie", "tank"],
    ClothingType.BOTTOM: ["pants", "trousers", "jeans", "slacks", "shorts", "skirt"],
    ClothingType.DRESS: ["dress", "gown", "frock", "jumper"],
    ClothingType.OUTERWEAR: ["jacket", "coat", "blazer", "suit", "cardigan", "vest", "outerwear"],
    ClothingType.FOOTWEAR: ["shoes", "sneakers", "boots", "footwear", "sandals", "heels", "loafers"],
    ClothingType.ACCESSORY: ["hat", "cap", "scarf", "tie", "belt", "bag", "purse", "jewelry", "watch", "gloves", "sunglasses"]
}

# Mapping of keywords to more specific clothing categories
CLOTHING_CATEGORY_MAPPING = {
    ClothingType.TOP: {
        ClothingCategory.TSHIRT: ["t-shirt", "tee", "t shirt", "crew neck", "v-neck", "graphic tee", "cotton shirt"],
        ClothingCategory.SHIRT: ["button", "button-up", "button-down", "collar", "formal shirt", "dress shirt", "oxford", "business shirt"],
        ClothingCategory.BLOUSE: ["blouse", "women's top", "ruffle", "peplum", "silk top", "satin top"],
        ClothingCategory.SWEATER: ["sweater", "jumper", "pullover", "knit", "cardigan", "turtleneck", "cashmere"],
        ClothingCategory.TANK: ["tank top", "sleeveless", "camisole", "spaghetti strap", "muscle shirt"],
        ClothingCategory.POLO: ["polo", "golf shirt", "tennis shirt", "collared knit", "pique"],
        ClothingCategory.HOODIE: ["hoodie", "hooded", "sweatshirt", "fleece top", "pullover hoodie", "zip-up hoodie"]
    },
    ClothingType.BOTTOM: {
        ClothingCategory.PANTS: ["pants", "trousers", "slacks", "chinos", "khakis", "dress pants", "work pants"],
        ClothingCategory.JEANS: ["jeans", "denim", "blue jeans", "jean", "denim pants", "skinny jeans", "boot cut"],
        ClothingCategory.SHORTS: ["shorts", "short pants", "cargo shorts", "jean shorts", "athletic shorts", "bermuda"],
        ClothingCategory.SKIRT: ["skirt", "midi skirt", "mini skirt", "maxi skirt", "pleated skirt", "a-line skirt"],
        ClothingCategory.LEGGINGS: ["leggings", "tights", "yoga pants", "spandex", "compression pants", "stretch pants"]
    },
    ClothingType.DRESS: {
        ClothingCategory.CASUAL_DRESS: ["casual dress", "day dress", "sundress", "t-shirt dress", "shift dress"],
        ClothingCategory.FORMAL_DRESS: ["formal dress", "evening dress", "gown", "cocktail dress", "party dress"],
        ClothingCategory.MAXI_DRESS: ["maxi dress", "long dress", "floor-length dress", "full-length dress"],
        ClothingCategory.MINI_DRESS: ["mini dress", "short dress", "above knee dress"]
    },
    ClothingType.OUTERWEAR: {
        ClothingCategory.JACKET: ["jacket", "lightweight jacket", "bomber", "windbreaker", "denim jacket"],
        ClothingCategory.COAT: ["coat", "winter coat", "overcoat", "long coat", "peacoat", "trench coat"],
        ClothingCategory.BLAZER: ["blazer", "sport coat", "suit jacket", "tailored jacket"],
        ClothingCategory.VEST: ["vest", "gilet", "waistcoat", "sleeveless jacket", "puffer vest"],
        ClothingCategory.CARDIGAN: ["cardigan", "open sweater", "button sweater", "knit jacket"]
    },
    ClothingType.FOOTWEAR: {
        ClothingCategory.SNEAKERS: ["sneakers", "athletic shoes", "trainers", "tennis shoes", "running shoes"],
        ClothingCategory.BOOTS: ["boots", "ankle boots", "winter boots", "hiking boots", "combat boots", "chelsea boots"],
        ClothingCategory.DRESS_SHOES: ["dress shoes", "formal shoes", "oxfords", "loafers", "brogues", "wingtips"],
        ClothingCategory.SANDALS: ["sandals", "flip flops", "slides", "open-toe", "strappy sandals"],
        ClothingCategory.HEELS: ["heels", "high heels", "pumps", "stilettos", "block heels", "wedges"]
    },
    ClothingType.ACCESSORY: {
        ClothingCategory.HAT: ["hat", "cap", "beanie", "baseball cap", "fedora", "sun hat", "winter hat"],
        ClothingCategory.SCARF: ["scarf", "neck scarf", "muffler", "winter scarf", "silk scarf"],
        ClothingCategory.BAG: ["bag", "purse", "handbag", "backpack", "tote", "shoulder bag", "clutch"],
        ClothingCategory.JEWELRY: ["jewelry", "necklace", "bracelet", "earrings", "ring", "watch", "pendant"],
        ClothingCategory.BELT: ["belt", "waist belt", "leather belt", "buckle"],
        ClothingCategory.SUNGLASSES: ["sunglasses", "shades", "eyewear", "sun protection", "glasses"],
        ClothingCategory.GLOVES: ["gloves", "mittens", "hand covering", "winter gloves", "leather gloves"]
    }
   
}

DEFAULT_CATEGORIES =  {
        ClothingType.TOP: ClothingCategory.SHIRT,
        ClothingType.BOTTOM: ClothingCategory.PANTS,
        ClothingType.DRESS: ClothingCategory.CASUAL_DRESS,
        ClothingType.OUTERWEAR: ClothingCategory.JACKET,
        ClothingType.FOOTWEAR: ClothingCategory.SNEAKERS,
        ClothingType.ACCESSORY: ClothingCategory.BAG
    }

# Color name mapping with RGB ranges
COLOR_MAPPING = {
    "red": (220, 50, 50),
    "dark_red": (150, 20, 20),
    "blue": (50, 100, 200),
    "light_blue": (135, 206, 235),
    "navy": (25, 50, 120),
    "sky_blue": (160, 195, 231),  
    "green": (50, 180, 50),
    "dark_green": (20, 80, 20),
    "light_green": (150, 230, 150),
    "yellow": (230, 220, 50),
    "orange": (230, 130, 50),
    "purple": (150, 50, 150),
    "lavender": (180, 150, 220),
    "pink": (255, 150, 180),
    "light_pink": (255, 200, 220),
    "brown": (140, 90, 40),
    "tan": (210, 180, 140),
    "black": (30, 30, 30),
    "gray": (128, 128, 128),
    "light_gray": (200, 200, 200),
    "white": (240, 240, 240),
    "beige": (245, 245, 220),
    "cream": (255, 250, 230)
}

# Pattern keywords mapping
PATTERN_KEYWORDS = {
    "solid": ["solid", "plain", "single color", "monochrome", "basic", "uniform"],
    "striped": ["stripe", "striped", "lines", "lined", "pinstripe", "vertical lines", "horizontal lines"],
    "checked": ["check", "checked", "plaid", "tartan", "gingham", "checkered", "houndstooth"],
    "polka_dot": ["polka dot", "dot", "spotted", "polka-dot", "dotted", "spots"],
    "floral": ["floral", "flower", "botanical", "flowery", "roses", "daisy", "blooms", "petals"],
    "graphic": ["graphic", "print", "logo", "text", "image", "picture", "slogan", "artwork"],
    "animal": ["animal print", "leopard", "zebra", "snake", "crocodile", "tiger stripe", "cheetah"],
    "geometric": ["geometric", "triangle", "square", "circle", "diamond", "abstract", "shapes"],
    "camo": ["camouflage", "camo", "military print", "army pattern"],
    "tie_dye": ["tie dye", "tie-dye", "dyed", "psychedelic"]
}

# Season mappings
SEASON_MAPPING = {
    Season.SPRING: ["spring", "light jacket", "floral", "pastel", "raincoat", "windbreaker", "light", "transitional"],
    Season.SUMMER: ["summer", "beach", "lightweight", "linen", "shorts", "tank top", "sandals", "tropical", "breathable", "thin"],
    Season.FALL: ["fall", "autumn", "flannel", "corduroy", "light coat", "light sweater", "layering", "september", "october"],
    Season.WINTER: ["winter", "wool", "heavy coat", "down jacket", "thick", "warm", "knit", "thermal", "fleece", "snow", "boots", "december"]
    }

# Fabric-based season association 
SEASON_FABRIC_MAPPING = {
    Season.SPRING: ["cotton", "linen", "silk", "denim"],
    Season.SUMMER: ["cotton", "linen", "silk"],
    Season.FALL: ["denim", "leather", "wool", "fleece"],
    Season.WINTER: ["leather", "wool", "fleece"]
}

# Simple color-season associations
COLOR_SEASON_MAPPING = {
    Season.SPRING: ["pastel", "mint", "light_green", "light_blue", "coral", "pink"],
    Season.SUMMER: ["yellow", "orange", "hot_pink", "bright", "turquoise", "sky_blue"],
    Season.FALL: ["burgundy", "olive", "mustard", "orange", "brown", "dark_green"],
    Season.WINTER: ["navy", "dark_red", "black", "white", "gray", "silver"]
    }
 
# Occasion mappings
OCCASION_MAPPING = {
    Occasion.CASUAL: ["casual", "everyday", "relaxed", "lounge", "weekend", "street", "comfort", "leisure"],
    Occasion.FORMAL: ["formal", "evening", "gown", "tuxedo", "elegant", "black tie", "ceremony", "fancy", "upscale"],
    Occasion.BUSINESS: ["business", "office", "professional", "work", "corporate", "suit", "blazer", "interview"],
    Occasion.SPORT: ["sport", "athletic", "gym", "workout", "running", "exercise", "performance", "fitness", "active"],
    Occasion.SPECIAL: ["party", "wedding", "celebration", "festive", "holiday", "special occasion", "event", "cocktail"]
}