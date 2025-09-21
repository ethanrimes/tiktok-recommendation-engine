"""Text extraction stage."""

from pathlib import Path
from typing import Optional

class TextExtractor:
    """Extract text from files."""
    
    def extract_from_file(self, file_path: Path) -> Optional[str]:
        """
        Extract text from a file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Extracted text or None if failed
        """
        try:
            if not file_path.exists():
                raise FileNotFoundError(f"File not found: {file_path}")
            
            # Read text file
            with open(file_path, 'r', encoding='utf-8') as f:
                text = f.read()
            
            return text.strip()
            
        except Exception as e:
            print(f"Error extracting text: {e}")
            return None
    
    def extract_from_multiple_files(self, file_paths: list[Path]) -> str:
        """
        Extract and combine text from multiple files.
        
        Args:
            file_paths: List of file paths
            
        Returns:
            Combined text
        """
        combined_text = []
        
        for file_path in file_paths:
            text = self.extract_from_file(file_path)
            if text:
                combined_text.append(text)
        
        return "\n\n".join(combined_text)