from enum import Enum
from typing import Optional, List
from pydantic import BaseModel, Field
from datetime import datetime
from uuid import UUID, uuid4

class ClothingType(str, Enum):
    """Types of clothing items."""
    TOP = "top"
    BOTTOM = "bottom"
    DRESS = "dress"
    OUTERWEAR = "outerwear"
    FOOTWEAR = "footwear"
    ACCESSORY = "accessory"

class ClothingCategory(str, Enum):
    """More specific categories of clothing."""
    # Tops
    TSHIRT = "t-shirt"
    SHIRT = "shirt"
    BLOUSE = "blouse"
    SWEATER = "sweater"
    # Bottoms
    PANTS = "pants"
    JEANS = "jeans"
    SHORTS = "shorts"
    SKIRT = "skirt"
    # This can be expanded as needed

class Season(str, Enum):
    """Seasons for clothing items."""
    SPRING = "spring"
    SUMMER = "summer"
    FALL = "fall"
    WINTER = "winter"
    ALL = "all"

class Occasion(str, Enum):
    """Occasions for clothing items."""
    CASUAL = "casual"
    FORMAL = "formal"
    BUSINESS = "business"
    SPORT = "sport"
    SPECIAL = "special"

class ClothingBase(BaseModel):
    """Base model for clothing items."""
    name: str
    type: ClothingType
    category: ClothingCategory
    color_primary: str
    color_secondary: Optional[str] = None
    pattern: Optional[str] = None
    seasons: List[Season] = [Season.ALL]
    occasions: List[Occasion] = [Occasion.CASUAL]
    description: Optional[str] = None

class ClothingCreate(ClothingBase):
    """Model for creating a clothing item."""
    
    # Additional fields for creation
    # maybe add image_file 
    pass

class ClothingDB(ClothingBase):
    """Model to store in subabase db."""
    id: UUID = Field(default_factory=uuid4)
    user_id: str
    image_path: str 
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    embedding_id: Optional[str] = None  # Reference to vector in ChromaDB

class ClothingResponse(ClothingDB):
    """Model for API responses."""
    # Add any additional fields for responses
    image_url: str
    
    # allows automatic conversion from ORM objects to this Pydantic model
    class Config:
        orm_mode = True