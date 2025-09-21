"""Text processing stage."""

import re
from typing import List

class TextProcessor:
    """Process and clean text data."""
    
    def process(self, text: str, max_length: int = 10000) -> str:
        """
        Process raw text.
        
        Args:
            text: Raw text to process
            max_length: Maximum text length to keep
            
        Returns:
            Processed text
        """
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove special characters but keep hashtags
        text = re.sub(r'[^\w\s#@]', ' ', text)
        
        # Normalize hashtags
        text = re.sub(r'#+', '#', text)
        
        # Truncate if too long
        if len(text) > max_length:
            text = text[:max_length]
        
        return text.strip()
    
    def extract_hashtags(self, text: str) -> List[str]:
        """
        Extract hashtags from text.
        
        Args:
            text: Text containing hashtags
            
        Returns:
            List of hashtags (without #)
        """
        hashtags = re.findall(r'#(\w+)', text)
        return list(set(hashtags))  # Remove duplicates
    
    def extract_mentions(self, text: str) -> List[str]:
        """
        Extract user mentions from text.
        
        Args:
            text: Text containing mentions
            
        Returns:
            List of mentioned usernames (without @)
        """
        mentions = re.findall(r'@(\w+)', text)
        return list(set(mentions))