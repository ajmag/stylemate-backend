from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from typing import Dict, Any
import logging
from backend.app.services.clothing_simple_service import ClothingService

router = APIRouter()
logger = logging.getLogger(__name__)

# Simple dependency injection to get the ClothingService instance
def get_clothing_service() -> ClothingService:
    return ClothingService()


@router.post("/upload", response_model=Dict[str, Any])
async def upload_clothing_image(
    file: UploadFile = File(...),
    user_id: str  = "test_user",
    clothing_service: ClothingService = Depends(get_clothing_service)):

    """
    Upload and process a new clothing item.
    
    - file: Image file of the clothing item
    - user_id: User identifier (hardcoded now but will change when auth is setup)

    Returns the processed clothing item with metadata and storage info.
    """
    try: 
        if not file.content_type.startswith('image/'):
                raise HTTPException(status_code=400, detail="File must be an image")
            
        # Read the image data
        image_data = await file.read()

        result = await clothing_service.process_and_store_clothing_item(
            image_data=image_data,
            file_name=file.filename,
            content_type=file.content_type,
            user_id=user_id
        )

        if not result:
            raise HTTPException(status_code=500, detail="Error processing clothing image")
        
        return {
            "success": True,
            "message": "Clothing item uploaded successfully",
            **result # Spread all the service results
        }
    
    except HTTPException:
        logger.error(f"HTTP error during upload: {e.detail}")
        raise e
    except Exception as e:
        logger.error(f"Unexpected Error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
    
