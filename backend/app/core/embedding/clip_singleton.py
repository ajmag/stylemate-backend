import open_clip, torch
from PIL import Image
import numpy as np
from chromadb import Documents, EmbeddingFunction, Embeddings


_MODEL = None
_PREPROCESS = None
"""This is a singleton setup if we want to use the clip model later for personalized recommendations."""

def get_clip(model_name: str = "ViT-B-32"):
    """Use the singleton pattern to create the CLIP model on creation only."""
    
    global _MODEL, _PREPROCESS

    if _MODEL is None:
        print("Loading CLIP once →", model_name)

        model, _, preprocess = open_clip.create_model_and_transforms(
            model_name, pretrained="laion2b_s34b_b79k"
        )

        model.eval().requires_grad_(False)
        
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        model.to(device) # make sure the modle actually is moved to gpu 

        _MODEL, _PREPROCESS = model, preprocess
    
    return _MODEL, _PREPROCESS 
   
    
def get_embedding_class():
    """Get a ChromaDB compatible embedding function using our singleton CLIP model"""
    model, preprocess = get_clip()

    class CLIPEmbeddingFunction(EmbeddingFunction):
        
        def __call__(self, input: Documents) -> Embeddings:
            """
            Convert input documents or images into embeddings.
            
            Args:
                input: Documents to embed (can contain images)
                
            Returns:
                Embeddings for the documents
            """
            if not input:
                return []

            if isinstance(input[0], np.ndarray): # assuming the numpy array for images 
                # process images
                processed_images = []
                
                for img_array in input:
                    # Convert numpy array to PIL Image
                    pil_img = Image.fromarray(img_array)

                    # apply preprocessing
                    tensor = preprocess(pil_img).unsqueeze(0)

                    processed_images.append(tensor)
                
                if processed_images:
                    image_batch = torch.cat(processed_images)

                    with torch.no_grad():
                        embeddings = model.encode_image(image_batch)

                        # Normalize
                        embeddings = embeddings / embeddings.norm(dim=-1, keepdim=True)

                        # Moves embeddings from GPU to CPU and converts pytorch tensor -> numpy arry -> python list 
                        return embeddings.cpu().numpy().tolist()
            
            # if not a image data
            return []

    return CLIPEmbeddingFunction()
            
    
