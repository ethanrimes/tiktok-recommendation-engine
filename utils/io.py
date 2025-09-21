"""File I/O utilities."""

import json
from pathlib import Path
from typing import Any, Dict, List

def save_json(data: Any, file_path: Path):
    """
    Save data as JSON file.
    
    Args:
        data: Data to save
        file_path: Path to save file
    """
    try:
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Error saving JSON: {e}")
        raise

def load_json(file_path: Path) -> Any:
    """
    Load data from JSON file.
    
    Args:
        file_path: Path to JSON file
        
    Returns:
        Loaded data
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading JSON: {e}")
        raise

def save_text(text: str, file_path: Path):
    """
    Save text to file.
    
    Args:
        text: Text to save
        file_path: Path to save file
    """
    try:
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(text)
    except Exception as e:
        print(f"Error saving text: {e}")
        raise

def load_text(file_path: Path) -> str:
    """
    Load text from file.
    
    Args:
        file_path: Path to text file
        
    Returns:
        Loaded text
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        print(f"Error loading text: {e}")
        raise

def list_files(directory: Path, pattern: str = "*") -> List[Path]:
    """
    List files in directory matching pattern.
    
    Args:
        directory: Directory path
        pattern: File pattern (e.g., "*.txt")
        
    Returns:
        List of file paths
    """
    if not directory.exists():
        return []
    
    return list(directory.glob(pattern))