import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.app.db.supabasedb import SupaBaseClient

def test_supabase_connection():
    try:
        # Instantiate the Supabase client
        supa_client = SupaBaseClient()
        
        # Attempt to get the Supabase client
        client = supa_client.get_supabase_client()
        
        # If successful, print a success message
        print("Supabase connection established successfully!")
    except Exception as e:
        # Print any errors encountered during connection
        print(f"Failed to establish Supabase connection: {e}")

if __name__ == "__main__":
    test_supabase_connection()