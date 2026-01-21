"""
Supabase Client Initialization
"""
import os
import streamlit as st
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def get_supabase_client() -> Client:
    """
    Initialize and return Supabase client.
    Uses Streamlit secrets in production, .env in development.
    """
    # Try Streamlit secrets first (for deployed app)
    try:
        url = st.secrets.get("SUPABASE_URL")
        key = st.secrets.get("SUPABASE_KEY")
        if url and key:
            return create_client(url, key)
    except Exception:
        pass
    
    # Fallback to environment variables (for local development)
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    
    if not url or not key:
        st.error("⚠️ Supabase credentials not configured. Please set SUPABASE_URL and SUPABASE_KEY.")
        st.stop()
    
    return create_client(url, key)


# Singleton client instance
@st.cache_resource
def init_supabase() -> Client:
    """
    Cached Supabase client to avoid reconnection on each rerun.
    """
    return get_supabase_client()
