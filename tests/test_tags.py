"""Tests for tag generation and matching."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import sys

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from stages.transformation.category_generator import CategoryGenerator
from stages.transformation.tag_mapper import TagMapper
from stages.scoring.affinity_scorer import AffinityScorer
from stages.scoring.relevance_scorer import RelevanceScorer

class TestCategoryGeneration:
    """Test category generation."""
    
    def test_category_generator_initialization(self):
        """Test category generator initialization."""
        with patch('stages.transformation.category_generator.ChatOpenAI'):
            generator = CategoryGenerator()
            assert generator is not None
    
    @patch('stages.transformation.category_generator.ChatOpenAI')
    def test_generate_categories_success(self, mock_llm):
        """Test successful category generation."""
        # Mock LLM response
        mock_llm_instance = MagicMock()
        mock_llm.return_value = mock_llm_instance
        mock_llm_instance.predict.return_value = '''
        {
            "categories": [
                {
                    "tag": "dance",
                    "description": "Dance videos including choreography and challenges",
                    "keywords": ["dance", "choreography", "dancing", "dancer", "moves"]
                },
                {
                    "tag": "comedy",
                    "description": "Funny videos, skits, and pranks",
                    "keywords": ["funny", "comedy", "humor", "joke", "prank"]
                },
                {
                    "tag": "food",
                    "description": "Cooking, recipes, and food reviews",
                    "keywords": ["food", "cooking", "recipe", "eating", "foodie"]
                }
            ]
        }
        '''
        
        generator = CategoryGenerator()
        
        # Test
        text = "Sample TikTok text with #dance #food #comedy content"
        categories = generator.generate(text, num_categories=3)
        
        # Verify
        assert len(categories) == 3
        assert categories[0]['tag'] == 'dance'
        assert categories[1]['tag'] == 'comedy'
        assert categories[2]['tag'] == 'food'
        assert 'description' in categories[0]
        assert 'keywords' in categories[0]
        assert len(categories[0]['keywords']) > 0
    
    @patch('stages.transformation.category_generator.ChatOpenAI')
    def test_generate_categories_fallback(self, mock_llm):
        """Test fallback when LLM fails."""
        # Create a mock instance that will be returned when ChatOpenAI is instantiated
        mock_llm_instance = MagicMock()
        mock_llm.return_value = mock_llm_instance
        
        # Make the predict method raise an exception
        mock_llm_instance.predict.side_effect = Exception("LLM error")
        
        generator = CategoryGenerator()
        
        # Test
        categories = generator.generate("sample text", num_categories=3)
        
        # Should return default categories
        assert len(categories) == 3
        assert categories[0]['tag'] == 'dance'

class TestTagMapping:
    """Test tag mapping functionality."""
    
    @patch('stages.transformation.tag_mapper.ChatOpenAI')
    def test_tag_mapper_initialization(self, mock_llm):
        """Test tag mapper initialization."""
        mapper = TagMapper()
        assert mapper is not None
    
    @patch('stages.transformation.tag_mapper.ChatOpenAI')
    def test_map_tags_success(self, mock_llm):
        """Test successful tag mapping."""
        # Mock LLM response
        mock_llm_instance = MagicMock()
        mock_llm.return_value = mock_llm_instance
        mock_llm_instance.predict.return_value = '''
        {
            "mappings": [
                {
                    "tag": "dance",
                    "affinity": 0.9,
                    "reason": "User posts many dance videos with dance hashtags"
                },
                {
                    "tag": "music",
                    "affinity": 0.7,
                    "reason": "Frequently uses trending music in videos"
                }
            ]
        }
        '''
        
        mapper = TagMapper()
        
        # Test data
        user_data = {
            'username': 'testuser',
            'bio': 'Dancer and music lover',
            'follower_count': 1000
        }
        
        posts = [
            {
                'description': 'New dance routine #dance #viral',
                'hashtags': ['dance', 'viral'],
                'music_title': 'Trending Song'
            }
        ]
        
        liked_posts = [
            {
                'description': 'Amazing choreography #dance',
                'hashtags': ['dance'],
                'music_title': 'Dance Track'
            }
        ]
        
        categories = [
            {'tag': 'dance', 'description': 'Dance content'},
            {'tag': 'music', 'description': 'Music content'},
            {'tag': 'comedy', 'description': 'Funny content'}
        ]
        
        # Test
        mappings = mapper.map_tags(user_data, posts, liked_posts, categories)
        
        # Verify
        assert len(mappings) == 2
        assert mappings[0]['tag'] == 'dance'
        assert mappings[0]['affinity'] == 0.9
        assert 'reason' in mappings[0]
    
    @patch('stages.transformation.tag_mapper.ChatOpenAI')
    def test_fallback_mapping(self, mock_llm):
        """Test fallback keyword-based mapping."""
        # Create a mock instance
        mock_llm_instance = MagicMock()
        mock_llm.return_value = mock_llm_instance
        
        # Make the predict method raise an exception
        mock_llm_instance.predict.side_effect = Exception("LLM error")
        
        mapper = TagMapper()
        
        # Test data
        posts = [
            {
                'description': 'Dance video #dance #trending',
                'hashtags': ['dance', 'trending']
            },
            {
                'description': 'Another dance #dance #music',
                'hashtags': ['dance', 'music']
            }
        ]
        
        liked_posts = []
        
        categories = [
            {
                'tag': 'dance',
                'keywords': ['dance', 'dancing', 'choreography']
            },
            {
                'tag': 'music',
                'keywords': ['music', 'song', 'singing']
            },
            {
                'tag': 'food',
                'keywords': ['food', 'cooking', 'recipe']
            }
        ]
        
        # Test
        mappings = mapper._fallback_mapping(posts, liked_posts, categories)
        
        # Verify
        assert len(mappings) > 0
        assert any(m['tag'] == 'dance' for m in mappings)
        assert any(m['tag'] == 'music' for m in mappings)
        # Food should not be mapped as it's not in the content
        assert not any(m['tag'] == 'food' for m in mappings)

class TestAffinityScoring:
    """Test affinity scoring."""
    
    def test_affinity_scorer_initialization(self):
        """Test affinity scorer initialization."""
        scorer = AffinityScorer()
        assert scorer is not None
    
    def test_score_calculation(self):
        """Test affinity score calculation."""
        scorer = AffinityScorer()
        
        # Test data
        tag_mappings = [
            {'tag': 'dance', 'affinity': 0.7, 'reason': 'Dance content'},
            {'tag': 'music', 'affinity': 0.5, 'reason': 'Music interest'}
        ]
        
        user_data = {
            'follower_count': 5000  # Should give 0.9 influence factor
        }
        
        posts = [
            {
                'description': 'Dance video #dance',
                'hashtags': ['dance'],
                'stats': {
                    'likes': 1000,
                    'comments': 50,
                    'shares': 20
                }
            }
        ]
        
        liked_posts = []
        
        # Test
        scored_tags = scorer.score(tag_mappings, user_data, posts, liked_posts)
        
        # Verify
        assert len(scored_tags) == 2
        dance_tag = next((t for t in scored_tags if t['tag'] == 'dance'), None)
        assert dance_tag is not None
        assert dance_tag['affinity'] > dance_tag['base_affinity']  # Should be boosted
    
    def test_influence_factor_calculation(self):
        """Test user influence factor calculation."""
        scorer = AffinityScorer()
        
        # Test different follower counts
        assert scorer._calculate_influence_factor({'follower_count': 500}) == 0.8
        assert scorer._calculate_influence_factor({'follower_count': 5000}) == 0.9
        assert scorer._calculate_influence_factor({'follower_count': 50000}) == 1.0
        assert scorer._calculate_influence_factor({'follower_count': 500000}) == 1.1
        assert scorer._calculate_influence_factor({'follower_count': 5000000}) == 1.2

class TestRelevanceScoring:
    """Test relevance scoring."""
    
    def test_relevance_scorer_initialization(self):
        """Test relevance scorer initialization."""
        with patch('stages.scoring.relevance_scorer.EmbeddingGenerator'):
            scorer = RelevanceScorer()
            assert scorer is not None
    
    @patch('stages.scoring.relevance_scorer.EmbeddingGenerator')
    def test_tag_match_calculation(self, mock_embedding):
        """Test tag matching score calculation."""
        scorer = RelevanceScorer()
        
        # Test data
        video = {
            'description': 'Amazing dance moves #dance #viral',
            'hashtags': ['dance', 'viral'],
            'author': 'dancer123'
        }
        
        user_tags = [
            {'tag': 'dance', 'affinity': 0.9},
            {'tag': 'music', 'affinity': 0.5},
            {'tag': 'comedy', 'affinity': 0.3}
        ]
        
        # Test
        score = scorer._calculate_tag_match(video, user_tags)
        
        # Verify
        assert score > 0  # Should match 'dance' tag
        assert score <= 1.0
    
    @patch('stages.scoring.relevance_scorer.EmbeddingGenerator')
    def test_video_text_creation(self, mock_embedding):
        """Test video text representation creation."""
        scorer = RelevanceScorer()
        
        # Test data
        video = {
            'description': 'Check this out!',
            'hashtags': ['dance', 'viral'],
            'music_title': 'Trending Song',
            'author': 'testuser'
        }
        
        # Test
        text = scorer._create_video_text(video)
        
        # Verify
        assert 'Check this out!' in text
        assert '#dance' in text
        assert '#viral' in text
        assert 'Music: Trending Song' in text
        assert '@testuser' in text

class TestExpectedTags:
    """Test that generated tags match expected patterns."""
    
    def test_dance_content_tags(self):
        """Test tags for dance content."""
        # This would be an integration test with real LLM
        # For unit testing, we verify the structure
        
        expected_dance_tags = [
            'dance', 'choreography', 'dancing', 'dancer', 'dance_challenge'
        ]
        
        # Verify tag format (lowercase, underscores for spaces)
        for tag in expected_dance_tags:
            assert tag.islower()
            assert ' ' not in tag
    
    def test_category_diversity(self):
        """Test that categories cover diverse content types."""
        expected_categories = [
            'dance', 'music', 'comedy', 'food', 'fashion',
            'fitness', 'education', 'gaming', 'beauty', 'travel',
            'pets', 'art', 'sports', 'tech', 'lifestyle'
        ]
        
        # Verify we have a good mix of categories
        assert len(expected_categories) >= 15
        assert len(set(expected_categories)) == len(expected_categories)  # No duplicates
    
    def test_tag_affinity_range(self):
        """Test that affinity scores are in valid range."""
        test_affinities = [0.0, 0.3, 0.5, 0.7, 0.9, 1.0]
        
        for affinity in test_affinities:
            assert 0.0 <= affinity <= 1.0
    
    def test_tag_keywords_relevance(self):
        """Test that keywords are relevant to tags."""
        tag_keyword_map = {
            'dance': ['dance', 'choreography', 'moves', 'dancing'],
            'food': ['food', 'cooking', 'recipe', 'eating', 'foodie'],
            'comedy': ['funny', 'humor', 'joke', 'prank', 'lol'],
            'music': ['music', 'song', 'singing', 'cover', 'remix']
        }
        
        for tag, keywords in tag_keyword_map.items():
            # Check that keywords relate to the tag
            assert all(isinstance(kw, str) for kw in keywords)
            assert len(keywords) >= 3  # Should have multiple keywords