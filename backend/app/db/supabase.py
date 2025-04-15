from supabase import create_client, Client
from app.config import settings

def get_supabase_client() -> Client:
    """Create and return a Supabase client."""
    if not settings.SUPABASE_URL or not settings.SUPABASE_KEY:
        raise ValueError("Supabase URL and key must set in enviorment variables.")
    
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)

# Create a Supabase client instance for reuse
supabase_client = get_supabase_client()