#!/usr/bin/env python
"""Standalone script to get recommendations."""

import sys
import argparse
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from pipelines.recommendation_pipeline import RecommendationPipeline
from pipelines.profiling_pipeline import ProfilingPipeline
from database.client import SupabaseClient
from utils.io import save_json, load_json
from rich.console import Console
from rich.table import Table

console = Console()

def main():
    parser = argparse.ArgumentParser(description="Generate video recommendations for a user")
    parser.add_argument("--username", "-u", type=str, required=True, help="TikTok username")
    parser.add_argument("--profile", "-p", type=str, help="Path to user profile JSON")
    parser.add_argument("--tags", "-t", type=str, help="Comma-separated tags (if no profile)")
    parser.add_argument("--count", "-c", type=int, default=20, help="Number of recommendations")
    parser.add_argument("--output", "-o", type=str, help="Output JSON file")
    
    args = parser.parse_args()
    
    # Get or create user profile
    profile = None
    
    if args.profile:
        # Load existing profile
        profile_path = Path(args.profile)
        if profile_path.exists():
            profile = load_json(profile_path)
            console.print(f"[green]Loaded profile from {profile_path}[/green]")
    
    if not profile and args.tags:
        # Create simple profile from tags
        tags = args.tags.split(',')
        profile = {
            'username': args.username,
            'tags': [
                {'tag': tag.strip(), 'affinity': 0.8, 'reason': 'Manual input'}
                for tag in tags
            ]
        }
        console.print(f"[green]Created profile with tags: {', '.join(tags)}[/green]")
    
    if not profile:
        # Try to load from database
        console.print("[yellow]No profile provided, checking database...[/yellow]")
        db_client = SupabaseClient()
        profile = db_client.get_user_profile(args.username)
        
        if not profile:
            # Generate profile
            console.print("[yellow]Profile not found, generating new profile...[/yellow]")
            
            # Load categories
            categories = db_client.get_categories()
            if not categories:
                default_path = Path("data/output/taxonomy.json")
                if default_path.exists():
                    categories = load_json(default_path)
                else:
                    console.print("[red]Error: No categories found. Please generate taxonomy first.[/red]")
                    sys.exit(1)
            
            # Generate profile
            pipeline = ProfilingPipeline()
            profile = pipeline.run(
                username=args.username,
                categories=categories
            )
            
            if not profile:
                console.print(f"[red]Failed to generate profile for @{args.username}[/red]")
                sys.exit(1)
    
    console.print(f"\n[bold blue]Generating {args.count} recommendations for @{args.username}...[/bold blue]")
    
    # Display user's top tags
    if profile.get('tags'):
        top_tags = ', '.join([t['tag'] for t in profile['tags'][:5]])
        console.print(f"User interests: {top_tags}")
    
    # Run recommendation pipeline
    pipeline = RecommendationPipeline()
    recommendations = pipeline.run(
        user_profile=profile,
        count=args.count
    )
    
    if not recommendations:
        console.print("[red]Failed to generate recommendations[/red]")
        sys.exit(1)
    
    # Save if output specified
    if args.output:
        output_path = Path(args.output)
        save_json(recommendations, output_path)
        console.print(f"[green]✓ Saved {len(recommendations)} recommendations to {output_path}[/green]")
    
    # Display results
    table = Table(title=f"Top {min(15, len(recommendations))} Recommendations")
    table.add_column("#", style="cyan", width=3)
    table.add_column("Video", style="white", width=40)
    table.add_column("Author", style="yellow")
    table.add_column("Score", style="green")
    table.add_column("Tags", style="blue")
    
    for i, rec in enumerate(recommendations[:15], 1):
        desc = rec['description']
        if len(desc) > 37:
            desc = desc[:34] + "..."
        
        matched_tags = ', '.join(rec.get('matched_tags', [])[:2])
        
        table.add_row(
            str(i),
            desc,
            f"@{rec['author']}",
            f"{rec['score']:.2f}",
            matched_tags
        )
    
    console.print(table)
    
    # Show top 5 links
    console.print(f"\n[bold]Top 5 Video Links:[/bold]")
    for i, rec in enumerate(recommendations[:5], 1):
        console.print(f"{i}. {rec['url']}")
    
    # Show score breakdown for top video
    if recommendations:
        top = recommendations[0]
        scores = top.get('scores', {})
        console.print(f"\n[bold]Top Video Score Breakdown:[/bold]")
        console.print(f"  Virality: {scores.get('virality', 0):.2f}")
        console.print(f"  Relevance: {scores.get('relevance', 0):.2f}")
        console.print(f"  Engagement: {scores.get('engagement', 0):.2f}")
        console.print(f"  [bold]Total: {top['score']:.2f}[/bold]")

if __name__ == "__main__":
    main()