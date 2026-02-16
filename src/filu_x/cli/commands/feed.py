"""Feed command – show posts from you and followed users with collision-aware rendering"""
import sys
import click
from pathlib import Path
from datetime import datetime
import json

from filu_x.storage.layout import FiluXStorageLayout
from filu_x.core.id_generator import normalize_display_name  # NEW IMPORT

def collect_posts(layout, limit: int) -> list:
    """
    Collect own posts + cached followed posts chronologically.
    
    Returns list of post dicts with keys:
      - author: display name
      - author_normalized: normalized display name (for collision detection)
      - pubkey_suffix: first 6 chars of pubkey (for disambiguation)
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
                    "author_normalized": normalize_display_name(post.get("author", "unknown")),
                    "pubkey_suffix": post.get("pubkey", "")[:6],
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
                        "author_normalized": normalize_display_name(post.get("author", user_dir.name)),
                        "pubkey_suffix": post.get("pubkey", "")[:6],
                        "content": post.get("content", ""),
                        "created_at": post.get("created_at", ""),
                        "cid": post_path.stem,
                        "source": "followed"
                    })
                except Exception:
                    continue
    
    # Sort newest first
    posts.sort(key=lambda x: x["created_at"], reverse=True)
    return posts[:limit]


def render_author(post: dict, all_posts: list) -> str:
    """
    Render author name with pubkey suffix if display name collision detected.
    
    Collision = same normalized display name but different pubkey suffix in feed.
    """
    author = post["author"]
    normalized = post["author_normalized"]
    pubkey_suffix = post["pubkey_suffix"]
    
    # Check if any other post in feed has same normalized name but different pubkey
    has_collision = any(
        p["author_normalized"] == normalized and p["pubkey_suffix"] != pubkey_suffix
        for p in all_posts
    )
    
    if has_collision:
        return f"{author} ({pubkey_suffix})"
    else:
        return author


@click.command()
@click.pass_context
@click.option("--limit", "-l", default=20, help="Maximum number of posts to show")
@click.option("--raw", is_flag=True, help="Show raw JSON instead of formatted view")
def feed(ctx, limit: int, raw: bool):
    """
    Show your feed – posts from you and followed users.
    
    Alpha 0.0.3: Includes cached posts from followed users.
    Collision-aware: Shows pubkey suffix when display names collide.
    """
    data_dir = ctx.obj.get("data_dir")
    layout = FiluXStorageLayout(base_path=data_dir)
    
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
            # Human-readable format with collision-aware author rendering
            author_display = render_author(post, posts)
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
                click.echo(f"[{time_str}] {author_display} 🔁")
            else:
                click.echo(f"[{time_str}] {author_display}")
            
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
        f"✨ Showing {len(posts)}/{total_own + total_cached} posts (alpha 0.0.3)",
        fg="blue"
    ))
    click.echo()
    click.echo("💡 Tips:")
    click.echo("   • Sync followed users: filu-x sync-followed")
    click.echo("   • Sync your posts:     filu-x sync")
    click.echo("   • Follow new users:    filu-x follow fx://bafkrei...")
    
    # ✅ Show collision explanation if detected
    normalized_names = {}
    for post in posts:
        norm = post["author_normalized"]
        suffix = post["pubkey_suffix"]
        normalized_names.setdefault(norm, set()).add(suffix)
    
    collisions = {name: suffixes for name, suffixes in normalized_names.items() if len(suffixes) > 1}
    
    if collisions:
        click.echo()
        click.echo(click.style(
            "⚠️  Display name collisions in feed:",
            fg="yellow",
            bold=True
        ))
        for name, suffixes in collisions.items():
            click.echo(f"   • '{name}' used by pubkeys: {', '.join(sorted(suffixes))}")
        click.echo()
        click.echo("💡 Identity is cryptographic (pubkey), not social (display name).")
