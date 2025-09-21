"""Pipeline for generating content taxonomy."""

from pathlib import Path
from typing import List, Dict, Any

from pipelines.base import BasePipeline
from stages.extraction.text_extractor import TextExtractor
from stages.transformation.text_processor import TextProcessor
from stages.transformation.category_generator import CategoryGenerator
from utils.embeddings import EmbeddingGenerator
from config import settings

class TaxonomyPipeline(BasePipeline):
    """Pipeline to generate content categories from text."""
    
    def __init__(self):
        super().__init__(name="taxonomy")
        self.text_extractor = TextExtractor()
        self.text_processor = TextProcessor()
        self.category_generator = CategoryGenerator()
        self.embedding_generator = EmbeddingGenerator()
    
    def run(self, input_path: Path, num_categories: int = 20) -> List[Dict[str, Any]]:
        """
        Run the taxonomy generation pipeline.
        
        Args:
            input_path: Path to input text file
            num_categories: Number of categories to generate
            
        Returns:
            List of category dictionaries
        """
        self.start()
        
        try:
            # Step 1: Extract text from file
            self.log("Extracting text from file...")
            raw_text = self.text_extractor.extract_from_file(input_path)
            
            if not raw_text:
                self.log("No text extracted from file", "error")
                return []
            
            self.log(f"Extracted {len(raw_text)} characters of text")
            
            # Step 2: Process and clean text
            self.log("Processing text...")
            processed_text = self.text_processor.process(raw_text)
            
            # Step 3: Generate categories using LLM
            self.log(f"Generating {num_categories} categories...")
            categories = self.category_generator.generate(
                text=processed_text,
                num_categories=num_categories
            )
            
            if not categories:
                self.log("No categories generated", "error")
                return []
            
            self.log(f"Generated {len(categories)} categories")
            
            # Step 4: Generate embeddings for categories
            self.log("Generating embeddings for categories...")
            for category in categories:
                # Create text representation for embedding
                text_repr = f"{category['tag']}: {category['description']}"
                if category.get('keywords'):
                    text_repr += f" Keywords: {', '.join(category['keywords'])}"
                
                embedding = self.embedding_generator.generate(text_repr)
                category['embedding'] = embedding
            
            # Step 5: Save to database
            self.log("Saving categories to database...")
            for category in categories:
                self.db_client.save_category(category)
            
            # Save complete result
            self.save_result(categories, f"taxonomy_{num_categories}")
            
            self.end()
            return categories
            
        except Exception as e:
            self.log(f"Pipeline failed: {e}", "error")
            self.end()
            return []