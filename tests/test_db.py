"""Tests for database connectivity and operations."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import sys
from datetime import datetime

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from database.client import SupabaseClient

class TestDatabaseClient:
    """Test Supabase database client."""
    
    def setup_method(self):
        """Set up test client."""
        with patch('database.client.create_client'):
            self.db_client = SupabaseClient()
    
    def test_client_initialization(self):
        """Test database client initialization."""
        with patch('database.client.settings') as mock_settings:
            mock_settings.supabase_url = "https://test.supabase.co"
            mock_settings.supabase_key = "test_key"  # Changed from supabase_key
            
            with patch('database.client.create_client') as mock_create:
                mock_client = MagicMock()
                mock_create.return_value = mock_client
                
                # Just create the client - it will call _initialize() automatically
                client = SupabaseClient()
                # Don't call client._initialize() again!
                
                mock_create.assert_called_once_with(
                    "https://test.supabase.co",
                    "test_key"
                )
    
    def test_save_category(self):
        """Test saving category to database."""
        # Mock Supabase client
        mock_table = MagicMock()
        self.db_client.client = MagicMock()
        self.db_client.client.table.return_value = mock_table
        mock_table.upsert.return_value.execute.return_value = None
        
        # Test data
        category = {
            'tag': 'dance',
            'description': 'Dance videos and choreography',
            'keywords': ['dance', 'choreography', 'moves'],
            'embedding': [0.1, 0.2, 0.3]
        }
        
        # Save category
        self.db_client.save_category(category)
        
        # Verify
        self.db_client.client.table.assert_called_with('categories')
        mock_table.upsert.assert_called_once()
        
        # Check that the data includes required fields
        call_args = mock_table.upsert.call_args[0][0]
        assert call_args['tag'] == 'dance'
        assert call_args['description'] == 'Dance videos and choreography'
        assert call_args['keywords'] == ['dance', 'choreography', 'moves']
        assert 'created_at' in call_args
    
    def test_get_categories(self):
        """Test retrieving categories from database."""
        # Mock response
        mock_response = MagicMock()
        mock_response.data = [
            {'tag': 'dance', 'description': 'Dance content'},
            {'tag': 'comedy', 'description': 'Funny videos'}
        ]
        
        mock_table = MagicMock()
        self.db_client.client = MagicMock()
        self.db_client.client.table.return_value = mock_table
        mock_table.select.return_value.execute.return_value = mock_response
        
        # Get categories
        categories = self.db_client.get_categories()
        
        # Verify
        assert len(categories) == 2
        assert categories[0]['tag'] == 'dance'
        assert categories[1]['tag'] == 'comedy'
    
    def test_save_user_profile(self):
        """Test saving user profile to database."""
        # Mock Supabase client
        mock_table = MagicMock()
        self.db_client.client = MagicMock()
        self.db_client.client.table.return_value = mock_table
        mock_table.upsert.return_value.execute.return_value = None
        
        # Test data
        profile = {
            'username': 'testuser',
            'user_id': '123456',
            'sec_uid': 'sec123',
            'bio': 'Test bio',
            'follower_count': 1000,
            'following_count': 500,
            'video_count': 50,
            'tags': [
                {'tag': 'dance', 'affinity': 0.8, 'reason': 'Frequent dance posts'},
                {'tag': 'music', 'affinity': 0.6, 'reason': 'Music-related content'}
            ]
        }
        
        # Save profile
        self.db_client.save_user_profile(profile)
        
        # Verify user profile was saved
        assert self.db_client.client.table.call_count >= 1
        first_call = self.db_client.client.table.call_args_list[0]
        assert first_call[0][0] == 'user_profiles'
    
    def test_get_user_profile(self):
        """Test retrieving user profile from database."""
        # Mock user data response
        mock_user_response = MagicMock()
        mock_user_response.data = {
            'username': 'testuser',
            'user_id': '123456',
            'follower_count': 1000
        }
        
        # Mock tags response
        mock_tags_response = MagicMock()
        mock_tags_response.data = [
            {'tag': 'dance', 'affinity': 0.8},
            {'tag': 'music', 'affinity': 0.6}
        ]
        
        # Setup mock client
        mock_table = MagicMock()
        self.db_client.client = MagicMock()
        self.db_client.client.table.return_value = mock_table
        
        # Setup chained calls for user profile
        mock_select = MagicMock()
        mock_table.select.return_value = mock_select
        mock_eq = MagicMock()
        mock_select.eq.return_value = mock_eq
        mock_single = MagicMock()
        mock_eq.single.return_value = mock_single
        mock_single.execute.return_value = mock_user_response
        
        # Setup chained calls for tags (reusing mock_table)
        mock_order = MagicMock()
        mock_eq.order.return_value = mock_order
        mock_order.execute.return_value = mock_tags_response
        
        # Get profile
        profile = self.db_client.get_user_profile('testuser')
        
        # Verify
        assert profile is not None
        assert profile['username'] == 'testuser'
        assert profile['follower_count'] == 1000
        assert len(profile['tags']) == 2
    
    def test_save_recommendations(self):
        """Test saving recommendations to database."""
        # Mock Supabase client
        mock_table = MagicMock()
        self.db_client.client = MagicMock()
        self.db_client.client.table.return_value = mock_table
        mock_table.insert.return_value.execute.return_value = None
        
        # Test data
        recommendations = [
            {
                'video_id': '123',
                'description': 'Test video 1',
                'author': 'user1',
                'url': 'https://tiktok.com/123',
                'score': 0.85,
                'scores': {
                    'virality': 0.8,
                    'relevance': 0.9,
                    'engagement': 0.85
                },
                'matched_tags': ['dance', 'music']
            },
            {
                'video_id': '456',
                'description': 'Test video 2',
                'author': 'user2',
                'url': 'https://tiktok.com/456',
                'score': 0.75,
                'scores': {
                    'virality': 0.7,
                    'relevance': 0.8,
                    'engagement': 0.75
                },
                'matched_tags': ['comedy']
            }
        ]
        
        # Save recommendations
        self.db_client.save_recommendations('testuser', recommendations)
        
        # Verify
        assert mock_table.insert.call_count == 2
    
    def test_save_and_load_result(self):
        """Test saving and loading pipeline results."""
        # Mock for saving
        mock_table = MagicMock()
        self.db_client.client = MagicMock()
        self.db_client.client.table.return_value = mock_table
        mock_table.upsert.return_value.execute.return_value = None
        
        # Test save
        test_data = {'test': 'data', 'value': 42}
        self.db_client.save_result(
            pipeline='test_pipeline',
            key='test_key',
            data=test_data,
            metadata={'version': 1}
        )
        
        # Verify save
        self.db_client.client.table.assert_called_with('pipeline_results')
        mock_table.upsert.assert_called_once()
        
        # Mock for loading
        mock_response = MagicMock()
        mock_response.data = {'data': test_data}
        
        mock_select = MagicMock()
        mock_table.select.return_value = mock_select
        mock_eq1 = MagicMock()
        mock_select.eq.return_value = mock_eq1
        mock_eq2 = MagicMock()
        mock_eq1.eq.return_value = mock_eq2
        mock_single = MagicMock()
        mock_eq2.single.return_value = mock_single
        mock_single.execute.return_value = mock_response
        
        # Test load
        result = self.db_client.load_result(
            pipeline='test_pipeline',
            key='test_key'
        )
        
        # Verify load
        assert result == test_data
    
    def test_database_error_handling(self):
        """Test error handling for database operations."""
        # Mock client to raise exception
        self.db_client.client = MagicMock()
        self.db_client.client.table.side_effect = Exception("Database error")
        
        # Test that methods handle errors gracefully
        categories = self.db_client.get_categories()
        assert categories == []
        
        profile = self.db_client.get_user_profile('testuser')
        assert profile is None
        
        result = self.db_client.load_result('pipeline', 'key')
        assert result is None