from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Query
from typing import Dict, Any
import logging

from backend.app.services.recommendation_service import RecommendationService

router = APIRouter()
logger = logging.getLogger(__name__)

def get_recommendation_service() -> RecommendationService:
    return RecommendationService()


@router.post("/complete-outfit", response_model=Dict[str, Any])
async def get_recommendations(
    file: UploadFile = File(...),
    user_id: str  = "test_user",
    limit: int = Query(5, ge=1, le=5),
    recommendation_type: str = Query("outfit", regex="^(outfit|similar)$"), # has to be one of these 
    recommendation_service: RecommendationService = Depends(get_recommendation_service)):

    """
    This will process the image and return recommendations based on it.
    
    - file: Image file to get recommendations for
    - user_id: User identifier (hardcoded for testing)
    - limit: Maximum number of recommendations to return (1-20)
    - recommendation_type: Type of recommendations (outfit, similar, color_match)
    """
    try:
        # Validate file type
        if not file.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="File must be an image")
        
        # Read the image data
        image_data = await file.read()

        result = await RecommendationService.get_outfit_recommendation(
            image_data=image_data,
            file_name=file.filename,
            user_id=user_id,
            limit=limit,
            recommendation_type=recommendation_type
        )

        return {
            "success": True,
            "message": "Recommendations retrieved successfully",
            **result
        }
    
    except HTTPException as e:
        logger.error(f"HTTP error during recommendations: {e.detail}")
        raise e
    except Exception as e:
        logger.error(f"Error getting recommendations: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting recommendations: {str(e)}")