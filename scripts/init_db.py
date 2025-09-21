#!/usr/bin/env python
"""Initialize database with schema."""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from database.client import SupabaseClient
from config import settings

def init_database():
    """Initialize database with schema."""
    print("Initializing database...")
    
    # Test connection
    client = SupabaseClient()
    if not client.client:
        print("Error: Could not connect to Supabase")
        print("Please check your SUPABASE_URL and SUPABASE_KEY in .env")
        return False
    
    print("✓ Connected to Supabase")
    
    # Note: Tables should be created using the SQL migrations in Supabase dashboard
    print("\nPlease run the SQL migrations in database/migrations/ in your Supabase SQL editor:")
    print("1. Go to your Supabase project dashboard")
    print("2. Navigate to SQL Editor")
    print("3. Copy and run the contents of database/migrations/001_initial_schema.sql")
    
    return True

if __name__ == "__main__":
    success = init_database()
    if success:
        print("\nDatabase initialization complete!")
    else:
        print("\nDatabase initialization failed!")
        sys.exit(1)