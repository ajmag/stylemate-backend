from supabase import create_client, Client
from backend.app.config import settings
from typing import Dict, Any, List 
import logging


class SupaBaseClient():
    """Supabas Client class to handle insertion and retireval logic."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.logger.info("Inititalizing Supabase client")
        self.client = None


    def get_supabase_client(self) -> Client:
        """Create and return a Supabase client."""
        if not self.client:
            if not settings.SUPABASE_URL or not settings.SUPABASE_KEY:
                self.logger.error("Supabase URL and key must be set in environment variables.")
                raise ValueError("Supabase URL and key must be set in environment variables.")
            
            self.client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
            self.logger.info("Supabase client created successfully")
        
        return self.client
    

    async def add_image_to_bucket(self, 
                                  file_path: str, 
                                  bucket_name: str, 
                                  image_data : bytes, 
                                  file_type: str = "image/jpeg") -> Dict[str, Any]:
        """Upload an image to Supabase Storage bucket.
    
        Args:
            file_path: The path where the file will be stored (e.g. 'user-123/image.jpg')
            bucket_name: The name of the storage bucket (e.g. 'clothing_images')
            image_data: The binary image data as bytes
            content_type: MIME type of the image (default: image/jpeg)
        
        Returns:
            The response from Supabase, example below

            {
                'Id': '12345abc-def6-7890-ghij-klmnopqrstuv',
                'Key': 'uploads/shirt_001.jpg',
                'path': 'uploads/shirt_001.jpg',
                'fullPath': 'images/uploads/shirt_001.jpg'
            }
        """
        
        try:
            return (self.client.storage
                        .from_(bucket_name)
                        .upload(file=image_data,
                                path=file_path,
                                file_options={"content-type": file_type})
                        )
        except Exception as e:
            self.logger.error(f"Error adding a image to supabase: {str(e)}")
            raise RuntimeError(f"Error adding a image to subabase: {str(e)}") 


    async def add_metadata_into_db(self, 
                                  clothing_data: Dict[str, Any], 
                                  image_path: str, 
                                  table_name: str) -> Dict[str, Any]:
        """Adds the metadata into the db.
        
        Args: 
            clothing_data : The metadata created from the vision api
            image_path : The path for image in the bucket 
            table_name : The table created for clothing metdata 

        Returns: 
            The response from supabase, example below 

            {
                'data': [
                    {
                        'id': 42,
                        'clothing_type': 'shirt',
                        'color': 'blue',
                        'brand': 'Nike', 
                        'file_path': 'uploads/shirt_001.jpg',
                        'created_at': '2025-05-29T14:30:00.123456+00:00',
                        'updated_at': '2025-05-29T14:30:00.123456+00:00'
                    }
                ],
                'count': 1
            }

        """

        clothing_table_input : Dict[str, Any] = (
            { 
                "user_id" : clothing_data["user_id"],
                "name" : "A clothing item", #FIXME
                "type" : clothing_data["clothing_type"],
                "category" : clothing_data["category"],
                "color_primary" : clothing_data["color_primary"],
                "color_primary_family" : clothing_data["color_primary_family"],
                "color_secondary" : clothing_data["color_secondary"],
                "color_secondary_family" : clothing_data["color_secondary_family"],
                "pattern" : clothing_data["pattern"],
                "seasons" : self.serialize_string(clothing_data["seasons"]), # need to be an array
                "occasions" : self.serialize_string(clothing_data["occasions"]), # need to be an array
                "description" : clothing_data["description"],
                "image_path" : image_path
            }
        )

        try: 
            response = (
                self.client.table(table_name)
                .insert(clothing_table_input)
                .execute()
            )

        except Exception as e:
            self.logger.error(f"Error adding metada into tabel {table_name}")
            raise RuntimeError(f"Error adding metada into tabel {table_name}")

        if not response.data:
            raise Exception("Data inserted into db is null, error occured during table insertion.")
        
        return response
    

    async def update_db(self, table_name : str, item_id: str , db_column: str) -> Dict[str, Any]:
        """This function updates the column within db to new item id."""
        try: 
            return self.client.table(table_name).update(
                {db_column: item_id}
            ).eq("id", item_id).execute()
        
        except Exception as e:
            self.logger.error(f"Error updating table {table_name} with {item_id}")
            raise RuntimeError(f"Error updating table {table_name} with {item_id}") 
    

    async def get_data_from_table(self, table_name: str, 
                                  select_columns: str, 
                                  filter_column : str,
                                  filter_value: Any) -> Dict[str, Any]:
        """This method allows you to fetch data from the specified tables name.
        
        Args:
            table_name : The table we want to look at
            select_columns : The column we want to look at
            filter_column : What we want to filter the query based on
            filter_value : Actual value to filter for
        
        Returns:
            An API response from supabase, Example below 

            "db_embedding_id": [
                {
                    "embedding_id": "some-id-here"
                }

        """

        try:
            response = (
                self.client.table(table_name)
                .select(select_columns)
                .eq(filter_column, filter_value)
                .execute()
            )

            return response.data

        except Exception as e:
            self.logger.error(f"Error trying to fetch {select_columns} from {table_name} where {filter_column}={filter_value}: {e}")
            raise RuntimeError(f"Error getting data from table -> {e}")
            

    def get_public_url(self, bucket_name : str, file_path: str) -> str:
        """This take the file path and grabs the public url so that the image can be returned to front end."""

        try:
            return (self.client.storage
                        .from_(bucket_name)
                        .get_public_url(file_path))
        
        except Exception as e:
            self.logger.error(f"Error trying to get public URL from file path: {file_path}")
            raise RuntimeError(f"Error trying to get public URL from file path {file_path}")
        

    def serialize_string(self, metadata_str : str) -> List[str]:
        """This takes the string metadata and split them into a list for supabase compatibility."""
        return [item.strip() for item in metadata_str.split(",")]
