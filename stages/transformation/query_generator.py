"""Query generation using LangChain."""

from typing import List, Dict, Any

from langchain.chat_models import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field

from config import settings

class SearchQuery(BaseModel):
    """Structured output for a search query."""
    query: str = Field(description="Search query string")
    source_tags: List[str] = Field(description="Primary tags this query targets")
    content_type: str = Field(description="Expected content type")

class SearchQueriesOutput(BaseModel):
    """Structured output for all search queries."""
    queries: List[SearchQuery] = Field(description="List of search queries")

class QueryGenerator:
    """Generate search queries using LLM."""
    
    def __init__(self):
        self.llm = ChatOpenAI(
            model=settings.llm_model,
            temperature=settings.llm_temperature,
            openai_api_key=settings.openai_api_key
        )
        self.parser = PydanticOutputParser(pydantic_object=SearchQueriesOutput)
        
        # Load prompt template
        prompt_path = settings.prompts_dir / "query_generation.txt"
        with open(prompt_path, 'r') as f:
            prompt_template = f.read()
        
        # Add format instructions
        self.prompt = PromptTemplate(
            template=prompt_template + "\n\n{format_instructions}",
            input_variables=["user_tags", "num_queries"],
            partial_variables={"format_instructions": self.parser.get_format_instructions()}
        )
    
    def generate(self, user_tags: List[Dict[str, Any]], num_queries: int = 10) -> List[Dict[str, Any]]:
        """
        Generate search queries from user tags.
        
        Args:
            user_tags: List of user tags with affinity scores
            num_queries: Number of queries to generate
            
        Returns:
            List of search query dictionaries
        """
        try:
            # Prepare user tags summary
            tags_text = self._format_user_tags(user_tags)
            
            # Format prompt
            formatted_prompt = self.prompt.format(
                user_tags=tags_text,
                num_queries=num_queries
            )
            
            # Generate response
            response = self.llm.predict(formatted_prompt)
            
            # Parse response
            result = self.parser.parse(response)
            
            # Convert to dictionaries
            queries = []
            for q in result.queries:
                queries.append({
                    'query': q.query,
                    'source_tags': q.source_tags,
                    'content_type': q.content_type
                })
            
            return queries[:num_queries]  # Ensure we return exact number requested
            
        except Exception as e:
            print(f"Error generating queries: {e}")
            # Return simple queries based on tags as fallback
            return self._fallback_queries(user_tags, num_queries)
    
    def _format_user_tags(self, user_tags: List[Dict[str, Any]]) -> str:
        """Format user tags for prompt."""
        if not user_tags:
            return "No tags available"
        
        formatted = []
        for tag in user_tags[:10]:  # Use top 10 tags
            formatted.append(f"- {tag['tag']} (affinity: {tag['affinity']:.2f})")
        
        return "\n".join(formatted)
    
    def _fallback_queries(self, user_tags: List[Dict[str, Any]], num_queries: int) -> List[Dict[str, Any]]:
        """Generate simple queries as fallback."""
        queries = []
        
        for i, tag in enumerate(user_tags):
            if i >= num_queries:
                break
            
            # Simple queries based on tag name
            tag_name = tag['tag']
            
            # Generate variations
            variations = [
                f"#{tag_name}",
                f"{tag_name} viral",
                f"best {tag_name}",
                f"{tag_name} 2024",
                f"trending {tag_name}"
            ]
            
            for j, query in enumerate(variations):
                if len(queries) >= num_queries:
                    break
                
                queries.append({
                    'query': query,
                    'source_tags': [tag_name],
                    'content_type': 'general'
                })
        
        return queries[:num_queries]