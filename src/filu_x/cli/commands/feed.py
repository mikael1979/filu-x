"""Feed command – show posts from you and followed users"""
import sys
import click
from pathlib import Path
from datetime import datetime
import json

from filu_x.storage.layout import FiluXStorageLayout

def collect_posts(layout, limit: int) -> list:
    """
    Collect own posts + cached followed posts chronologically.
    
    Returns list of post dicts with keys:
      - author: display name
      - content: post text
      - created_at: ISO8601 timestamp
      - cid: content ID
      - source: "own" or "followed"
    """
    posts = []
    
    # Collect own posts
    if layout.posts_dir.exists():
        for post_path in sorted(layout.posts_dir.glob("*.json"), reverse=True):
            try:
                post = layout.load_json(post_path)
                posts.append({
                    "author": post.get("author", "unknown"),
                    "content": post.get("content", ""),
                    "created_at": post.get("created_at", ""),
                    "cid": post.get("id", post_path.stem),
                    "source": "own"
                })
            except Exception:
                continue
    
    # Collect cached followed posts
    cached_base = layout.base_path / "data" / "cached" / "follows"
    if cached_base.exists():
        for user_dir in cached_base.glob("*"):
            if not user_dir.is_dir():
                continue
            
            posts_dir = user_dir / "posts"
            if not posts_dir.exists():
                continue
            
            for post_path in posts_dir.glob("*.json"):
                try:
                    post = json.loads(post_path.read_text(encoding="utf-8"))
                    posts.append({
                        "author": post.get("author", user_dir.name),
                        "content": post.get("content", ""),
                        "created_at": post.get("created_at", ""),
                        "cid": post_path.stem,  # Filename = CID
                        "source": "followed"
                    })
                except Exception:
                    continue
    
    # Sort newest first
    posts.sort(key=lambda x: x["created_at"], reverse=True)
    return posts[:limit]

@click.command()
@click.option("--limit", "-l", default=20, help="Maximum number of posts to show")
@click.option("--raw", is_flag=True, help="Show raw JSON instead of formatted view")
def feed(limit: int, raw: bool):
    """
    Show your feed – posts from you and followed users.
    
    Alpha 0.0.2: Includes cached posts from followed users.
    Run 'filu-x sync-followed' first to fetch followed users' posts.
    
    Example:
      filu-x feed --limit 10
      filu-x sync-followed && filu-x feed
    """
    layout = FiluXStorageLayout()
    
    # Verify user is initialized
    if not layout.profile_path().exists():
        click.echo(click.style(
            "❌ User not initialized. Run first:\n"
            "   filu-x init <username>",
            fg="red"
        ))
        sys.exit(1)
    
    # Load profile for display name
    profile = layout.load_json(layout.profile_path())
    username = profile.get("author", "unknown")
    
    # Collect posts (own + cached followed)
    posts = collect_posts(layout, limit)
    
    # Show empty feed message
    if not posts:
        click.echo(click.style(
            "📭 Your feed is empty",
            fg="yellow",
            bold=True
        ))
        click.echo()
        click.echo("💡 Suggestions:")
        click.echo("   • Create your first post:  filu-x post 'Hello world!'")
        click.echo("   • Follow someone:          filu-x follow fx://bafkrei...")
        click.echo("   • Sync followed users:     filu-x sync-followed")
        click.echo("   • Sync your own posts:     filu-x sync")
        sys.exit(0)
    
    # Show feed header
    click.echo(click.style(
        f"📬 Feed ({len(posts)} posts)",
        fg="cyan",
        bold=True
    ))
    click.echo()
    
    # Show posts
    for i, post in enumerate(posts, 1):
        if raw:
            # Raw JSON output
            click.echo(json.dumps(post, indent=2, ensure_ascii=False))
            if i < len(posts):
                click.echo("---")
        else:
            # Human-readable format
            author = post["author"]
            content = post["content"].strip()
            created = post["created_at"]
            source = post["source"]
            
            # Format timestamp
            try:
                dt = datetime.fromisoformat(created.replace("Z", "+00:00"))
                time_str = dt.strftime("%Y-%m-%d %H:%M:%S")
            except:
                time_str = created[:19] if len(created) > 19 else created
            
            # Show post with source indicator
            if source == "followed":
                click.echo(f"[{time_str}] {author} 🔁")
            else:
                click.echo(f"[{time_str}] {author}")
            
            click.echo(f"  {content}")
            click.echo(f"  fx://{post['cid']}")
            if i < len(posts):
                click.echo()
    
    # Show footer
    total_own = len(list(layout.posts_dir.glob("*.json"))) if layout.posts_dir.exists() else 0
    cached_base = layout.base_path / "data" / "cached" / "follows"
    total_cached = sum(1 for p in cached_base.rglob("*.json")) if cached_base.exists() else 0
    
    click.echo()
    click.echo(click.style(
        f"✨ Showing {len(posts)}/{total_own + total_cached} posts (alpha 0.0.2)",
        fg="blue"
    ))
    click.echo()
    click.echo("💡 Tips:")
    click.echo("   • Sync followed users: filu-x sync-followed")
    click.echo("   • Sync your posts:     filu-x sync")
    click.echo("   • Follow new users:    filu-x follow fx://bafkrei...")
