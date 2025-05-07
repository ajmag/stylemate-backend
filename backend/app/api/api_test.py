from fastapi import APIRouter, UploadFile, File, HTTPException
import logging
from backend.app.core.agents.vision_agent import VisionProcessingAgent

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/test-vision-api")
async def test_vision_api(file: UploadFile = File(...)):
    """Test the vision API with a sample image."""
    try:
        # Read the image data from the uploaded file
        image_data = await file.read()
        
        # Initialize the VisionProcessingAgent
        agent = VisionProcessingAgent()
        
        # Process the image and get metadata and embeddings
        result = await agent.run({"image_data": image_data})
        
        return {
            "success": True,
            "fashion_metadata" : result["fashion_metadata"],
            "classification_result": {
                "labels": result["classification_result"].get("labels", []),
                "objects": result["classification_result"].get("objects", []),
                "colors": result["classification_result"].get("colors", [])
            },
            "embeddings": result["embeddings"][:10] if "embeddings" in result else None,
            "message": "Image processed successfully"
        }
    
    except Exception as e:
        logger.exception(f"Error processing image: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing image: {str(e)}")
