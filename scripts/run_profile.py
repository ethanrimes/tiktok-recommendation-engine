#!/usr/bin/env python
"""Standalone script to profile a user."""

import sys
import argparse
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from pipelines.profiling_pipeline import ProfilingPipeline
from database.client import SupabaseClient
from utils.io import save_json, load_json
from rich.console import Console
from rich.table import Table

console = Console()

def main():
    parser = argparse.ArgumentParser(description="Generate user profile with category tags")
    parser.add_argument("--username", "-u", type=str, required=True, help="TikTok username")
    parser.add_argument("--taxonomy", "-t", type=str, help="Path to taxonomy JSON file")
    parser.add_argument("--output", "-o", type=str, help="Output JSON file")
    
    args = parser.parse_args()
    
    # Load taxonomy
    categories = []
    if args.taxonomy:
        taxonomy_path = Path(args.taxonomy)
        if taxonomy_path.exists():
            categories = load_json(taxonomy_path)
            console.print(f"[green]Loaded {len(categories)} categories from {taxonomy_path}[/green]")
    
    # If no taxonomy provided, try to load from database
    if not categories:
        console.print("[yellow]No taxonomy file provided, checking database...[/yellow]")
        db_client = SupabaseClient()
        categories = db_client.get_categories()
        
        if not categories:
            # Try default location
            default_path = Path("data/output/taxonomy.json")
            if default_path.exists():
                categories = load_json(default_path)
                console.print(f"[green]Loaded categories from {default_path}[/green]")
            else:
                console.print("[red]Error: No categories found. Please generate taxonomy first.[/red]")
                sys.exit(1)
    
    console.print(f"\n[bold blue]Profiling user @{args.username}...[/bold blue]")
    
    # Run pipeline
    pipeline = ProfilingPipeline()
    profile = pipeline.run(
        username=args.username,
        categories=categories
    )
    
    if not profile:
        console.print(f"[red]Failed to profile user @{args.username}[/red]")
        sys.exit(1)
    
    # Save if output specified
    if args.output:
        output_path = Path(args.output)
        save_json(profile, output_path)
        console.print(f"[green]✓ Saved to {output_path}[/green]")
    
    # Display results
    console.print(f"\n[bold]User Profile: @{args.username}[/bold]")
    console.print(f"Followers: {profile.get('follower_count', 0):,}")
    console.print(f"Following: {profile.get('following_count', 0):,}")
    console.print(f"Videos: {profile.get('video_count', 0):,}")
    
    if profile.get('bio'):
        console.print(f"Bio: {profile['bio'][:100]}...")
    
    # Display tags
    tags = profile.get('tags', [])
    if tags:
        table = Table(title=f"Top {len(tags)} Interest Categories")
        table.add_column("#", style="cyan", width=3)
        table.add_column("Tag", style="yellow")
        table.add_column("Affinity", style="green")
        table.add_column("Reason", style="white")
        
        for i, tag_info in enumerate(tags[:15], 1):  # Show top 15
            reason = tag_info.get('reason', '')
            if len(reason) > 50:
                reason = reason[:47] + "..."
            
            table.add_row(
                str(i),
                tag_info['tag'],
                f"{tag_info['affinity']:.2f}",
                reason
            )
        
        console.print(table)
    else:
        console.print("[yellow]No tags generated[/yellow]")

if __name__ == "__main__":
    main()