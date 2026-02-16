# src/filu_x/cli/commands/recent.py
import sys
import click
from filu_x.storage.layout import FiluXStorageLayout

@click.command()
@click.pass_context
@click.option("--count", "-n", default=5, help="Number of recent links to show")
def recent(ctx, count: int):
    """Show recently used fx:// links for quick reuse."""
    data_dir = ctx.obj.get("data_dir")
    layout = FiluXStorageLayout(base_path=data_dir)
    
    if not layout.private_config_path().exists():
        click.echo(click.style(
            "❌ No private config found. Initialize first: filu-x init <user>",
            fg="red"
        ))
        sys.exit(1)
    
    try:
        config = layout.load_json(layout.private_config_path())
        recent_links = config.get("recent_links", [])
        
        if not recent_links:
            click.echo(click.style("📭 No recent links saved.", fg="yellow"))
            return
        
        click.echo(click.style("🔗 Recent links:", fg="cyan", bold=True))
        for i, link in enumerate(recent_links[:count], 1):
            click.echo(f"   [{i}] {link}")
        
        # Näytä default profile link jos asetettu
        default = config.get("default_profile_link")
        if default:
            click.echo()
            click.echo(click.style("👤 Default profile:", fg="blue"))
            click.echo(f"   {default}")
    
    except Exception as e:
        click.echo(click.style(f"❌ Error loading recent links: {e}", fg="red"))
        sys.exit(1)
