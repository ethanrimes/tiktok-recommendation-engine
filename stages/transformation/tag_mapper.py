"""Tag mapping using LangChain."""

from typing import List, Dict, Any

from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field

from config import settings

class TagMapping(BaseModel):
    """Structured output for a single tag mapping."""
    tag: str = Field(description="Category tag name")
    affinity: float = Field(description="Affinity score from 0.0 to 1.0", ge=0.0, le=1.0)
    reason: str = Field(description="Reason for this affinity score")

class TagMappingsOutput(BaseModel):
    """Structured output for all tag mappings."""
    mappings: List[TagMapping] = Field(description="List of tag mappings")

class TagMapper:
    """Map user data to category tags using LLM."""
    
    def __init__(self):
        self.llm = ChatOpenAI(
            model=settings.llm_model,
            temperature=settings.llm_temperature,
            openai_api_key=settings.openai_api_key
        )
        self.parser = PydanticOutputParser(pydantic_object=TagMappingsOutput)
        
        # Load prompt template
        prompt_path = settings.prompts_dir / "tag_mapping.txt"
        with open(prompt_path, 'r') as f:
            prompt_template = f.read()
        
        # Add format instructions
        self.prompt = PromptTemplate(
            template=prompt_template + "\n\n{format_instructions}",
            input_variables=[
                "username", "bio", "follower_count", "following_count",
                "posted_content", "liked_content", "categories"
            ],
            partial_variables={"format_instructions": self.parser.get_format_instructions()}
        )
    
    def map_tags(
        self,
        user_data: Dict[str, Any],
        posts: List[Dict[str, Any]],
        reposts: List[Dict[str, Any]],  # NEW parameter
        liked_posts: List[Dict[str, Any]],
        categories: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Map user to category tags with enhanced data."""
        try:
            posted_content = self._summarize_posts(posts[:10])
            reposted_content = self._summarize_posts(reposts[:10])  # NEW
            liked_content = self._summarize_posts(liked_posts[:10])
            categories_text = self._summarize_categories(categories)
            
            # Include region context in prompt
            region_context = f"User is from {user_data.get('region', 'Unknown')} region, speaks {user_data.get('language', 'Unknown')}"
            
            formatted_prompt = self.prompt.format(
                username=user_data.get('username', ''),
                bio=user_data.get('bio', 'No bio'),
                follower_count=user_data.get('follower_count', 0),
                following_count=user_data.get('following_count', 0),
                posted_content=posted_content,
                reposted_content=reposted_content,  # NEW
                liked_content=liked_content,
                categories=categories_text,
                region_context=region_context  # NEW
            )
            
            # Generate response
            response = self.llm.invoke(formatted_prompt).content
            
            # Parse response
            result = self.parser.parse(response)
            
            # Convert to dictionaries
            mappings = []
            for mapping in result.mappings:
                mappings.append({
                    'tag': mapping.tag,
                    'affinity': mapping.affinity,
                    'reason': mapping.reason
                })
            
            return mappings
            
        except Exception as e:
            print(f"Error mapping tags: {e}")
            # Return simple keyword-based mapping as fallback
            return self._fallback_mapping(posts, liked_posts, categories)
    
    def _summarize_posts(self, posts: List[Dict[str, Any]]) -> str:
        """Summarize posts for prompt."""
        if not posts:
            return "No posts available"
        
        summaries = []
        for i, post in enumerate(posts, 1):
            desc = post.get('description', '')[:100]
            hashtags = ' '.join([f"#{tag}" for tag in post.get('hashtags', [])])
            music = post.get('music_title', 'Unknown')
            
            summary = f"{i}. {desc} | Music: {music} | Tags: {hashtags}"
            summaries.append(summary)
        
        return "\n".join(summaries)
    
    def _summarize_categories(self, categories: List[Dict[str, Any]]) -> str:
        """Summarize categories for prompt."""
        summaries = []
        for cat in categories:
            summary = f"- {cat['tag']}: {cat['description']}"
            summaries.append(summary)
        
        return "\n".join(summaries)
    
    def _fallback_mapping(
        self,
        posts: List[Dict[str, Any]],
        liked_posts: List[Dict[str, Any]],
        categories: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Simple keyword-based mapping as fallback."""
        mappings = []
        
        # Collect all text content
        all_text = []
        for post in posts + liked_posts:
            all_text.append(post.get('description', ''))
            all_text.extend(post.get('hashtags', []))
        
        all_text = ' '.join(all_text).lower()
        
        # Score each category based on keyword matches
        for cat in categories:
            score = 0
            matches = 0
            
            for keyword in cat.get('keywords', []):
                if keyword.lower() in all_text:
                    matches += 1
            
            if matches > 0:
                score = min(1.0, matches / len(cat.get('keywords', [1])))
                mappings.append({
                    'tag': cat['tag'],
                    'affinity': score,
                    'reason': f"Found {matches} keyword matches"
                })
        
        # Sort by affinity
        mappings.sort(key=lambda x: x['affinity'], reverse=True)
        
        return mappings[:10]  # Return top 10