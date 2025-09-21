"""Category generation using LangChain."""

from typing import List, Dict, Any
from pathlib import Path

from langchain.chat_models import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field

from config import settings

class CategoryOutput(BaseModel):
    """Structured output for a single category."""
    tag: str = Field(description="Category tag name (lowercase, with underscores)")
    description: str = Field(description="Detailed description of the category")
    keywords: List[str] = Field(description="Associated keywords")

class CategoriesOutput(BaseModel):
    """Structured output for all categories."""
    categories: List[CategoryOutput] = Field(description="List of generated categories")

class CategoryGenerator:
    """Generate content categories using LLM."""
    
    def __init__(self):
        self.llm = ChatOpenAI(
            model=settings.llm_model,
            temperature=settings.llm_temperature,
            openai_api_key=settings.openai_api_key
        )
        self.parser = PydanticOutputParser(pydantic_object=CategoriesOutput)
        
        # Load prompt template
        prompt_path = settings.prompts_dir / "category_generation.txt"
        with open(prompt_path, 'r') as f:
            prompt_template = f.read()
        
        # Add format instructions
        self.prompt = PromptTemplate(
            template=prompt_template + "\n\n{format_instructions}",
            input_variables=["input_text", "num_categories"],
            partial_variables={"format_instructions": self.parser.get_format_instructions()}
        )
    
    def generate(self, text: str, num_categories: int = 20) -> List[Dict[str, Any]]:
        """
        Generate categories from text.
        
        Args:
            text: Input text to analyze
            num_categories: Number of categories to generate
            
        Returns:
            List of category dictionaries
        """
        try:
            # Truncate text if too long
            max_text_length = 5000
            if len(text) > max_text_length:
                text = text[:max_text_length]
            
            # Format prompt
            formatted_prompt = self.prompt.format(
                input_text=text,
                num_categories=num_categories
            )
            
            # Generate response
            response = self.llm.predict(formatted_prompt)
            
            # Parse response
            result = self.parser.parse(response)
            
            # Convert to dictionaries
            categories = []
            for cat in result.categories:
                categories.append({
                    'tag': cat.tag.lower().replace(' ', '_'),
                    'description': cat.description,
                    'keywords': cat.keywords
                })
            
            return categories[:num_categories]  # Ensure we return exact number requested
            
        except Exception as e:
            print(f"Error generating categories: {e}")
            # Return some default categories as fallback
            return self._get_default_categories(num_categories)
    
    def _get_default_categories(self, num_categories: int) -> List[Dict[str, Any]]:
        """Get default categories as fallback."""
        defaults = [
            {
                'tag': 'dance',
                'description': 'Dance videos including choreography, dance challenges, and freestyle',
                'keywords': ['dance', 'choreography', 'moves', 'dancing', 'dancer']
            },
            {
                'tag': 'comedy',
                'description': 'Funny videos, skits, pranks, and humorous content',
                'keywords': ['funny', 'comedy', 'humor', 'joke', 'prank', 'skit']
            },
            {
                'tag': 'music',
                'description': 'Music performances, covers, original songs, and music-related content',
                'keywords': ['music', 'song', 'singing', 'cover', 'performance']
            },
            {
                'tag': 'fashion',
                'description': 'Fashion, outfits, style tips, and clothing hauls',
                'keywords': ['fashion', 'outfit', 'style', 'clothes', 'ootd']
            },
            {
                'tag': 'food',
                'description': 'Cooking, recipes, food reviews, and eating content',
                'keywords': ['food', 'cooking', 'recipe', 'eating', 'foodie']
            }
        ]
        
        return defaults[:num_categories]