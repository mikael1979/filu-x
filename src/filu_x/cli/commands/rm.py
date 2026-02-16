"""Remove command – delete posts or cached content (alpha-safe)"""
import sys
from pathlib import Path
import click

from filu_x.storage.layout import FiluXStorageLayout

@click.command()
@click.pass_context
@click.argument("target", required=False)
@click.option("--cache", is_flag=True, help="Clear cached content from followed users")
@click.option("--force", "-f", is_flag=True, help="Skip confirmation prompts")
@click.option("--dry-run", "-n", is_flag=True, help="Show what would be deleted")
def rm(ctx, target: str, cache: bool, force: bool, dry_run: bool):
    """
    Remove posts or cached content.
    
    Examples:
      filu-x rm 11654937          # Delete post starting with 11654937
      filu-x rm --cache           # Clear cache from followed users
      filu-x rm 11654937 --dry-run  # Preview deletion
    
    ⚠️  Manifest update: Run 'filu-x sync' after deletion to update your profile.
    💡  Full profile deletion: Use standard Unix tools (rm -rf) or cleanup script.
    """
    # Validate arguments
    if not target and not cache:
        click.echo(click.style(
            "❌ Usage: filu-x rm <post_id> OR filu-x rm --cache",
            fg="red"
        ))
        click.echo()
        click.echo("Examples:")
        click.echo("  filu-x rm 11654937")
        click.echo("  filu-x rm --cache")
        sys.exit(1)
    
    if target and cache:
        click.echo(click.style(
            "❌ Cannot combine post ID with --cache",
            fg="red"
        ))
        sys.exit(1)
    
    data_dir = ctx.obj.get("data_dir")
    layout = FiluXStorageLayout(base_path=data_dir)
    
    # Verify user is initialized
    if not layout.profile_path().exists():
        click.echo(click.style(
            "❌ User not initialized. Run: filu-x init <username>",
            fg="red"
        ))
        sys.exit(1)
    
    # Handle targets
    if cache:
        _remove_cache(layout, force, dry_run)
    else:
        _remove_post(layout, target, force, dry_run)


def _remove_post(layout: FiluXStorageLayout, post_id_prefix: str, force: bool, dry_run: bool):
    """Remove a specific post by ID prefix (first 8+ chars)."""
    # Find matching post
    matches = []
    if layout.posts_dir.exists():
        matches = [
            p for p in layout.posts_dir.glob("*.json")
            if p.stem.startswith(post_id_prefix)
        ]
    
    if not matches:
        click.echo(click.style(
            f"❌ No posts match ID prefix: {post_id_prefix}",
            fg="red"
        ))
        # List available posts (first 16 chars)
        available = [p.stem[:16] for p in layout.posts_dir.glob("*.json")]
        if available:
            click.echo("   Available posts (first 16 chars):")
            for a in sorted(available)[:5]:
                click.echo(f"     • {a}")
            if len(available) > 5:
                click.echo(f"     ... and {len(available) - 5} more")
        sys.exit(1)
    
    if len(matches) > 1:
        click.echo(click.style(
            f"❌ Multiple posts match '{post_id_prefix}':",
            fg="red"
        ))
        for m in matches:
            click.echo(f"   • {m.stem[:16]}...")
        sys.exit(1)
    
    post_path = matches[0]
    post_id = post_path.stem
    
    # Load post data for preview
    try:
        post_data = layout.load_json(post_path)
        content_preview = post_data.get("content", "")[:50]
        author = post_data.get("author", "unknown")
    except Exception:
        content_preview = "[unreadable]"
        author = "unknown"
    
    # Show deletion preview
    click.echo(click.style(
        f"🗑️  Delete post: {post_id[:16]}...",
        fg="yellow",
        bold=True
    ))
    click.echo(f"   Author: {author}")
    click.echo(f"   Content: {content_preview}...")
    click.echo(f"   File: {post_path.relative_to(layout.base_path)}")
    click.echo()
    click.echo(click.style(
        "💡 Manifest update: Run 'filu-x sync' after deletion to update your profile",
        fg="blue"
    ))
    
    if dry_run:
        click.echo(click.style("📄 Dry run – nothing deleted.", fg="blue"))
        return
    
    # Confirm deletion
    if not force:
        if not click.confirm("   Confirm deletion?"):
            click.echo("Cancelled.")
            sys.exit(0)
    
    # Delete file
    try:
        post_path.unlink()
        click.echo(click.style(f"✅ Post deleted: {post_id[:16]}...", fg="green"))
        click.echo()
        click.echo("💡 Remember to run 'filu-x sync' to update your manifest.")
    except Exception as e:
        click.echo(click.style(f"❌ Error deleting post: {e}", fg="red"))
        sys.exit(1)


def _remove_cache(layout: FiluXStorageLayout, force: bool, dry_run: bool):
    """Clear cached content from followed users."""
    cache_base = layout.base_path / "data" / "cached" / "follows"
    
    if not cache_base.exists():
        click.echo(click.style("📭 No cached content to clear.", fg="yellow"))
        return
    
    # Count cache usage
    cached_users = [d for d in cache_base.glob("*") if d.is_dir()]
    total_posts = sum(
        len(list(u.rglob("*.json"))) 
        for u in cached_users
    )
    
    click.echo(click.style(
        f"🗑️  Clear cached content",
        fg="yellow",
        bold=True
    ))
    click.echo(f"   Users cached: {len(cached_users)}")
    click.echo(f"   Posts cached: {total_posts}")
    
    if dry_run:
        click.echo(click.style("📄 Dry run – nothing deleted.", fg="blue"))
        return
    
    if not force:
        if not click.confirm("   Clear all cached content?"):
            click.echo("Cancelled.")
            sys.exit(0)
    
    try:
        import shutil
        shutil.rmtree(cache_base)
        cache_base.mkdir(parents=True, exist_ok=True)
        click.echo(click.style("✅ Cache cleared.", fg="green"))
    except Exception as e:
        click.echo(click.style(f"❌ Error clearing cache: {e}", fg="red"))
        sys.exit(1)
