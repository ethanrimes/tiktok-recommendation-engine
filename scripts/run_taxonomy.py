#!/usr/bin/env python
"""Standalone script to generate taxonomy."""

import sys
import argparse
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from pipelines.taxonomy_pipeline import TaxonomyPipeline
from utils.io import save_json
from rich.console import Console
from rich.table import Table

console = Console()

def main():
    parser = argparse.ArgumentParser(description="Generate content taxonomy from text")
    parser.add_argument("--input", "-i", type=str, required=True, help="Input text file")
    parser.add_argument("--output", "-o", type=str, help="Output JSON file")
    parser.add_argument("--num-categories", "-n", type=int, default=20, help="Number of categories")
    
    args = parser.parse_args()
    
    input_path = Path(args.input)
    if not input_path.exists():
        console.print(f"[red]Error: Input file not found: {input_path}[/red]")
        sys.exit(1)
    
    console.print(f"[bold blue]Generating taxonomy from {input_path}...[/bold blue]")
    
    # Run pipeline
    pipeline = TaxonomyPipeline()
    categories = pipeline.run(
        input_path=input_path,
        num_categories=args.num_categories
    )
    
    if not categories:
        console.print("[red]Failed to generate categories[/red]")
        sys.exit(1)
    
    # Save if output specified
    if args.output:
        output_path = Path(args.output)
        save_json(categories, output_path)
        console.print(f"[green]✓ Saved to {output_path}[/green]")
    
    # Display results
    table = Table(title=f"Generated {len(categories)} Categories")
    table.add_column("#", style="cyan", width=3)
    table.add_column("Tag", style="yellow")
    table.add_column("Description", style="white")
    table.add_column("Keywords", style="dim")
    
    for i, cat in enumerate(categories, 1):
        keywords = ', '.join(cat.get('keywords', [])[:3])
        if len(cat.get('keywords', [])) > 3:
            keywords += '...'
        
        table.add_row(
            str(i),
            cat['tag'],
            cat['description'][:50] + "...",
            keywords
        )
    
    console.print(table)

if __name__ == "__main__":
    main()