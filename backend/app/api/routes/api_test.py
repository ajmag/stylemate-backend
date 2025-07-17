from fastapi import APIRouter, UploadFile, File, HTTPException, Query
import logging
from backend.app.core.agents.vision_agent import VisionProcessingAgent
from backend.app.core.agents.recommendation_agent import RecommendationAgent
from backend.app.db.chromadb import ChromaDBClient
from backend.app.db.supabasedb import SupaBaseClient
import uuid
import json


router = APIRouter()
logger = logging.getLogger(__name__)

_collection_name = "test_collection_v1"
_testing_user_id = "test_user"
_test_collection_name = "test_collection_v2"

_data_base_name = "clothing_items"
_bucket_name = "clothing-images"


@router.post("/test-vision-api")
async def test_vision_api(file: UploadFile = File(...),
                          tags=["vision"]):
    """Test the vision API with a sample image. This will process the image and store the result in ChromaDB."""
    try:
        # Read the image data from the uploaded file
        image_data = await file.read()
        
        # Initialize the VisionProcessingAgent
        agent = VisionProcessingAgent()
        
        # Process the image and get metadata and embeddings
        result = await agent.run({"image_data": image_data}, user_id=_testing_user_id)

        # steps to add the image and user_id/item_id into supabase here  
        sb_client = SupaBaseClient()
        sb_client.get_supabase_client() # now client is init 

        # Generate a unique file path for the image
        file_path = f"{_testing_user_id}/{uuid.uuid4()}.{file.filename.split(".")[-1]}"
        file_type = file.content_type

        # add image into storage bucket -> user_id/image.png 
        storage_response = await sb_client.add_image_to_bucket(file_path, 
                                                               _bucket_name, 
                                                               image_data, 
                                                               file_type)
        print(f"storage response: {storage_response}")

        # add image metadata into db, path/user id will be harcoded until auth is created 
        db_response = await sb_client.add_metadat_into_db(result["fashion_metadata"], 
                                                    file_path, 
                                                    _data_base_name)

        item_id = db_response.data[0]["id"]

        # Update the database record with embedding_id = item_id 
        await sb_client.update_db(_data_base_name, item_id, "embedding_id")

        # Store metadata results into chromadb
        db_client = ChromaDBClient()
        collection = db_client.get_or_create_collection(_collection_name)
    
        # add the item with the same id as the embedding_id in supabase
        try:
            collection.add(
                ids=[item_id],
                embeddings=[result["embeddings"]],
                metadatas=[result["fashion_metadata"]],
                documents=[json.dumps(result["classification_result"])],
            )

        except Exception as e:
            logger.error(f"Error adding item to collection: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error adding item to collection: {str(e)}")

        # get the public url from storage to be returned to front end 
        image_url = sb_client.get_public_url(_bucket_name, file_path)
        # this will get the emebdding_id where the id is equal to the recently created item)
        db_embedding_id = await sb_client.get_data_from_table(_data_base_name, "embedding_id", "id", item_id )
       
        # Return the result of the processing
        return {
            "success": True,
            "image_url": image_url,
            "db_response" : db_response.data[0],
            "db_embedding_id" : db_embedding_id,
            "fashion_metadata" : result["fashion_metadata"],
            "classification_result": {
                "labels": result["classification_result"].get("labels", []),
                "objects": result["classification_result"].get("objects", []),
                "colors": result["classification_result"].get("colors", [])
            },
            "embeddings": result["embeddings"][:10] if "embeddings" in result else None,
            "message": "Image processed and inserted successfully"
        }
    
    except Exception as e:
        logger.exception(f"Error processing image: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing image: {str(e)}")
    


@router.post("/test-getting-recommendations")
async def test_getting_recommendations(file: UploadFile = File(...), 
                                       tags=["recommendations"]):
    """Test getting recommendations pipeline. This will process the image and return recommendations.""" 

    try: 
        image_data = await file.read()

        vision_agent = VisionProcessingAgent()
        vision_result = await vision_agent.run({"image_data": image_data}, user_id=_testing_user_id)

        recommendation_agent = RecommendationAgent()
        recommendations = await recommendation_agent.run(
            query_item=vision_result,
            user_id =_testing_user_id,
            bucket_name = _bucket_name,
            limit=5,
            collection_name=_collection_name,
            recommendation_type="outfit",
        )

        return {
            "success": True,
            "query_item": vision_result["fashion_metadata"],
            "recommendations": recommendations,
            "message": "Recommendations generated successfully"
        }
    except Exception as e:
        logger.exception(f"Error getting recommendations: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting recommendations: {str(e)}")
    
    
#########################################################################################################################################################################################################################################################################################################################

# This endpoint is for testing the Vision API with CLIP embeddings

@router.post("/test-vision-api-clip-embedding")
async def test_vision_api(file: UploadFile = File(...),
                          tags=["clip-embedding"]):
    """test the vision api w/ clip embedding. This will process the image and store the result in ChromaDB."""

    try:
        # Read the image data from the uploaded file
        image_data = await file.read()
        
        # Initialize the VisionProcessingAgent
        agent = VisionProcessingAgent()
        
        # Process the image and get metadata and embeddings
        result = await agent.run({"image_data": image_data}, user_id=_testing_user_id)

        # Store the result in ChromaDB
        db_client = ChromaDBClient()

        # create collection
        collection = db_client.get_or_create_multimodal_collection(_test_collection_name)
        
        # convert image to numpy array 
        image_array = db_client.convert_bytes_to_image(image_data)

        item_id = "item_" + str(uuid.uuid4())

        try:
            collection.add(
                ids=[item_id],
                images= image_array, # Pass the image directly - OpenCLIP will embed it
                metadatas=[result["fashion_metadata"]],
            )

        except Exception as e:
            logger.error(f"Error adding item to CLIP collection: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error adding item to collection: {str(e)}")
         
        # Return the result of the processing
        return {
            "success": True,
            "item_id": item_id,
            "fashion_metadata": result["fashion_metadata"],
            "message": "Image processed and inserted with CLIP embeddings successfully"
        }
    
    except Exception as e:
        logger.exception(f"Error processing image: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing image: {str(e)}")


@router.post("/test-multimodal-recommendations")
async def test_multimodal_recommendations(file: UploadFile = File(...), 
                                          tags=["recommendations"]):
    """Test getting recommendations pipeline. This will process the image and return recommendations.""" 
    
    try: 
        image_data = await file.read()
        
        vision_agent = VisionProcessingAgent()
        vision_result = await vision_agent.run({"image_data": image_data}, user_id=_testing_user_id)

        recommendation_agent = RecommendationAgent()
        recommendations = await recommendation_agent.get_recommendations_with_clip(
            image_data=image_data,  # Pass the raw image
            user_id =_testing_user_id,
            limit=10,
            collection_name=_test_collection_name,
            recommendation_type="similar"
        )

        return {
            "success": True,
            "query_item": vision_result["fashion_metadata"],
            "recommendations": recommendations,
            "message": "CLIP-based Recommendations generated successfully"
        }
    
    except Exception as e:
        logger.exception(f"Error getting recommendations: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting recommendations: {str(e)}")


@router.post("/compare-recommendation-approaches")
async def compare_recommendation_approaches(
                                            file: UploadFile = File(...),
                                            limit: int = Query(5, description="Number of recommendations to return"),
                                            tags=["comparison"]):
    """Compare custom embedding vs CLIP-based recommendations."""
    try:
        # Read the image data
        image_data = await file.read()
        
        # Process the image to get metadata and custom embeddings
        vision_agent = VisionProcessingAgent()
        vision_result = await vision_agent.process_image({"image_data": image_data}, user_id=_testing_user_id)
        
        # Get recommendations using custom embeddings
        custom_agent = RecommendationAgent()
        custom_recommendations = await custom_agent.get_recommendations(
            query_item=vision_result,
            user_id=_testing_user_id,
            collection_name=_collection_name,
            limit=limit,
            recommendation_type="similar"
        )
        
        # Get recommendations using CLIP
        multimodal_agent = RecommendationAgent()
        clip_recommendations = await multimodal_agent.get_recommendations_with_clip(
            image_data=image_data,
            user_id=_testing_user_id, 
            collection_name=_test_collection_name,
            limit=limit,
            recommendation_type="similar"
        )
        
        return {
            "success": True,
            "query_item": vision_result["fashion_metadata"],
            "custom_recommendations": custom_recommendations,
            "clip_recommendations": clip_recommendations,
            "message": "Comparison completed successfully"
        }
    except Exception as e:
        logger.exception(f"Error comparing recommendation approaches: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error comparing recommendation approaches: {str(e)}")
    

@router.post("/delete-collections")
def delete_collections():

    try:
        db_client = ChromaDBClient()

        collection_names = db_client.client.list_collections()

        deleted_collections = []

        for collection in collection_names:
            collection_name = collection.name
            db_client.client.delete_collection(name=collection_name)
            deleted_collections.append(collection_name)
        
        
        return {
            "success": True,
            "deleted_collections": deleted_collections,
            "message": f"Successfully deleted {len(deleted_collections)} collections"
        }
    except Exception as e:
        logger.exception(f"Error deleting collections: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error deleting collections: {str(e)}")
    


@router.post("/test-getting-recommendations")
async def test_getting_recommendations(file: UploadFile = File(...), 
                                       tags=["recommendations"]):
    """Test getting recommendations pipeline. This will process the image and return recommendations.""" 

    try: 
        image_data = await file.read()

        vision_agent = VisionProcessingAgent()
        vision_result = await vision_agent.run({"image_data": image_data}, user_id=_testing_user_id)

        recommendation_agent = RecommendationAgent()
        recommendations = await recommendation_agent.run(
            query_item=vision_result,
            user_id =_testing_user_id,
            limit=10,
            collection_name=_collection_name,
            recommendation_type="outfit"
        )

        return {
            "success": True,
            "query_item": vision_result["fashion_metadata"],
            "recommendations": recommendations,
            "message": "Recommendations generated successfully"
        }
    except Exception as e:
        logger.exception(f"Error getting recommendations: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting recommendations: {str(e)}")
    
    
#########################################################################################################################################################################################################################################################################################################################

# This endpoint is for testing the Vision API with CLIP embeddings

@router.post("/test-vision-api-clip-embedding")
async def test_vision_api(file: UploadFile = File(...),
                          tags=["clip-embedding"]):
    """test the vision api w/ clip embedding. This will process the image and store the result in ChromaDB."""

    try:
        # Read the image data from the uploaded file
        image_data = await file.read()
        
        # Initialize the VisionProcessingAgent
        agent = VisionProcessingAgent()
        
        # Process the image and get metadata and embeddings
        result = await agent.run({"image_data": image_data}, user_id=_testing_user_id)

        # Store the result in ChromaDB
        db_client = ChromaDBClient()

        # create collection
        collection = db_client.get_or_create_multimodal_collection(_test_collection_name)
        
        # convert image to numpy array 
        image_array = db_client.convert_bytes_to_image(image_data)

        item_id = "item_" + str(uuid.uuid4())

        try:
            collection.add(
                ids=[item_id],
                images= image_array, # Pass the image directly - OpenCLIP will embed it
                metadatas=[result["fashion_metadata"]],
            )

        except Exception as e:
            logger.error(f"Error adding item to CLIP collection: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error adding item to collection: {str(e)}")
         
        # Return the result of the processing
        return {
            "success": True,
            "item_id": item_id,
            "fashion_metadata": result["fashion_metadata"],
            "message": "Image processed and inserted with CLIP embeddings successfully"
        }
    
    except Exception as e:
        logger.exception(f"Error processing image: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing image: {str(e)}")


@router.post("/test-multimodal-recommendations")
async def test_multimodal_recommendations(file: UploadFile = File(...), 
                                          tags=["recommendations"]):
    """Test getting recommendations pipeline. This will process the image and return recommendations.""" 
    
    try: 
        image_data = await file.read()
        
        vision_agent = VisionProcessingAgent()
        vision_result = await vision_agent.run({"image_data": image_data}, user_id=_testing_user_id)

        recommendation_agent = RecommendationAgent()
        recommendations = await recommendation_agent.get_recommendations_with_clip(
            image_data=image_data,  # Pass the raw image
            user_id =_testing_user_id,
            limit=10,
            collection_name=_test_collection_name,
            recommendation_type="similar"
        )

        return {
            "success": True,
            "query_item": vision_result["fashion_metadata"],
            "recommendations": recommendations,
            "message": "CLIP-based Recommendations generated successfully"
        }
    
    except Exception as e:
        logger.exception(f"Error getting recommendations: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting recommendations: {str(e)}")


@router.post("/compare-recommendation-approaches")
async def compare_recommendation_approaches(
                                            file: UploadFile = File(...),
                                            limit: int = Query(5, description="Number of recommendations to return"),
                                            tags=["comparison"]):
    """Compare custom embedding vs CLIP-based recommendations."""
    try:
        # Read the image data
        image_data = await file.read()
        
        # Process the image to get metadata and custom embeddings
        vision_agent = VisionProcessingAgent()
        vision_result = await vision_agent.process_image({"image_data": image_data}, user_id=_testing_user_id)
        
        # Get recommendations using custom embeddings
        custom_agent = RecommendationAgent()
        custom_recommendations = await custom_agent.get_recommendations(
            query_item=vision_result,
            user_id=_testing_user_id,
            collection_name=_collection_name,
            limit=limit,
            recommendation_type="similar"
        )
        
        # Get recommendations using CLIP
        multimodal_agent = RecommendationAgent()
        clip_recommendations = await multimodal_agent.get_recommendations_with_clip(
            image_data=image_data,
            user_id=_testing_user_id, 
            collection_name=_test_collection_name,
            limit=limit,
            recommendation_type="similar"
        )
        
        return {
            "success": True,
            "query_item": vision_result["fashion_metadata"],
            "custom_recommendations": custom_recommendations,
            "clip_recommendations": clip_recommendations,
            "message": "Comparison completed successfully"
        }
    except Exception as e:
        logger.exception(f"Error comparing recommendation approaches: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error comparing recommendation approaches: {str(e)}")
    

@router.post("/delete-collections")
def delete_collections():

    try:
        db_client = ChromaDBClient()

        collection_names = db_client.client.list_collections()

        deleted_collections = []

        for collection in collection_names:
            collection_name = collection.name
            db_client.client.delete_collection(name=collection_name)
            deleted_collections.append(collection_name)
        
        
        return {
            "success": True,
            "deleted_collections": deleted_collections,
            "message": f"Successfully deleted {len(deleted_collections)} collections"
        }
    except Exception as e:
        logger.exception(f"Error deleting collections: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error deleting collections: {str(e)}")
