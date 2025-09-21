"""Main CLI entry point for TikTok Recommendation Engine."""

import click
import json
from pathlib import Path
from rich.console import Console
from rich.table import Table

from config import settings
from pipelines.taxonomy_pipeline import TaxonomyPipeline
from pipelines.profiling_pipeline import ProfilingPipeline
from pipelines.recommendation_pipeline import RecommendationPipeline
from utils.io import save_json, load_json

console = Console()

@click.group()
def cli():
    """TikTok Recommendation Engine CLI."""
    pass

@cli.command()
@click.option('--input', '-i', type=click.Path(exists=True), required=True, help='Input text file')
@click.option('--output', '-o', type=click.Path(), default='data/output/taxonomy.json', help='Output file')
@click.option('--num-categories', '-n', type=int, default=20, help='Number of categories to generate')
def taxonomy(input, output, num_categories):
    """Generate content taxonomy from text files."""
    console.print(f"[bold blue]Generating taxonomy from {input}...[/bold blue]")
    
    pipeline = TaxonomyPipeline()
    categories = pipeline.run(
        input_path=Path(input),
        num_categories=num_categories
    )
    
    save_json(categories, Path(output))
    
    # Display results
    table = Table(title="Generated Categories")
    table.add_column("Tag", style="cyan")
    table.add_column("Description", style="white")
    
    for cat in categories[:10]:  # Show first 10
        table.add_row(cat['tag'], cat['description'][:50] + "...")
    
    console.print(table)
    console.print(f"[green]✓ Saved {len(categories)} categories to {output}[/green]")

@cli.command()
@click.option('--username', '-u', required=True, help='TikTok username')
@click.option('--taxonomy', '-t', type=click.Path(exists=True), required=True, help='Taxonomy file')
@click.option('--output', '-o', type=click.Path(), help='Output file')
def profile(username, taxonomy, output):
    """Generate user profile with category tags."""
    console.print(f"[bold blue]Profiling user @{username}...[/bold blue]")
    
    # Load taxonomy
    categories = load_json(Path(taxonomy))
    
    pipeline = ProfilingPipeline()
    user_profile = pipeline.run(
        username=username,
        categories=categories
    )
    
    if output:
        save_json(user_profile, Path(output))
    
    # Display results
    table = Table(title=f"Profile for @{username}")
    table.add_column("Tag", style="cyan")
    table.add_column("Affinity", style="yellow")
    
    for tag_info in user_profile['tags'][:10]:  # Show top 10
        table.add_row(tag_info['tag'], f"{tag_info['affinity']:.2f}")
    
    console.print(table)
    if output:
        console.print(f"[green]✓ Saved profile to {output}[/green]")

@cli.command()
@click.option('--username', '-u', required=True, help='TikTok username')
@click.option('--profile', '-p', type=click.Path(exists=True), help='User profile file')
@click.option('--count', '-c', type=int, default=20, help='Number of recommendations')
@click.option('--output', '-o', type=click.Path(), help='Output file')
def recommend(username, profile, count, output):
    """Generate video recommendations for a user."""
    console.print(f"[bold blue]Generating recommendations for @{username}...[/bold blue]")
    
    # Load or generate profile
    if profile:
        user_profile = load_json(Path(profile))
    else:
        # Need to run profiling first
        console.print("[yellow]No profile provided, generating one...[/yellow]")
        taxonomy_path = Path("data/output/taxonomy.json")
        if not taxonomy_path.exists():
            console.print("[red]Error: No taxonomy found. Run 'taxonomy' command first.[/red]")
            return
        
        categories = load_json(taxonomy_path)
        profiling = ProfilingPipeline()
        user_profile = profiling.run(username=username, categories=categories)
    
    pipeline = RecommendationPipeline()
    recommendations = pipeline.run(
        user_profile=user_profile,
        count=count
    )
    
    if output:
        save_json(recommendations, Path(output))
    
    # Display results
    table = Table(title=f"Recommendations for @{username}")
    table.add_column("#", style="cyan")
    table.add_column("Video", style="white")
    table.add_column("Author", style="yellow")
    table.add_column("Score", style="green")
    
    for i, rec in enumerate(recommendations[:10], 1):  # Show top 10
        desc = rec['description'][:40] + "..." if len(rec['description']) > 40 else rec['description']
        table.add_row(
            str(i),
            desc,
            f"@{rec['author']}",
            f"{rec['score']:.2f}"
        )
    
    console.print(table)
    console.print(f"\n[bold]Video Links:[/bold]")
    for i, rec in enumerate(recommendations[:5], 1):
        console.print(f"{i}. {rec['url']}")
    
    if output:
        console.print(f"\n[green]✓ Saved {len(recommendations)} recommendations to {output}[/green]")

@cli.command()
@click.option('--username', '-u', required=True, help='TikTok username')
@click.option('--taxonomy', '-t', type=click.Path(exists=True), help='Taxonomy file')
@click.option('--count', '-c', type=int, default=20, help='Number of recommendations')
def pipeline(username, taxonomy, count):
    """Run the full recommendation pipeline."""
    console.print(f"[bold blue]Running full pipeline for @{username}...[/bold blue]")
    
    # Step 1: Load or generate taxonomy
    if taxonomy:
        categories = load_json(Path(taxonomy))
    else:
        console.print("[yellow]No taxonomy provided, using default...[/yellow]")
        taxonomy_path = Path("data/output/taxonomy.json")
        if taxonomy_path.exists():
            categories = load_json(taxonomy_path)
        else:
            console.print("[red]Error: No taxonomy found. Run 'taxonomy' command first.[/red]")
            return
    
    # Step 2: Profile user
    console.print("\n[bold]Step 1: Profiling user...[/bold]")
    profiling = ProfilingPipeline()
    user_profile = profiling.run(username=username, categories=categories)
    
    # Step 3: Generate recommendations
    console.print("\n[bold]Step 2: Generating recommendations...[/bold]")
    recommendation = RecommendationPipeline()
    recommendations = recommendation.run(user_profile=user_profile, count=count)
    
    # Display final results
    console.print("\n[bold green]Pipeline Complete![/bold green]")
    
    table = Table(title="Top Recommendations")
    table.add_column("#", style="cyan")
    table.add_column("Video", style="white")
    table.add_column("Author", style="yellow")
    table.add_column("Score", style="green")
    
    for i, rec in enumerate(recommendations[:10], 1):
        desc = rec['description'][:40] + "..." if len(rec['description']) > 40 else rec['description']
        table.add_row(
            str(i),
            desc,
            f"@{rec['author']}",
            f"{rec['score']:.2f}"
        )
    
    console.print(table)

if __name__ == '__main__':
    cli()