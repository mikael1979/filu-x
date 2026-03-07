"""Feed command – show posts from you and followed users with thread support"""
import sys
import click
from pathlib import Path
from datetime import datetime
import json

from filu_x.storage.layout import FiluXStorageLayout
from filu_x.core.id_generator import normalize_display_name

def render_post_item(post: dict, all_posts: list) -> str:
    """
    Render a single post with proper type indicators and thread info.
    
    Args:
        post: Post data dictionary
        all_posts: List of all posts (for collision detection)
    
    Returns:
        Formatted post string
    """
    author = post["author"]
    normalized = post["author_normalized"]
    pubkey_suffix = post["pubkey_suffix"]
    content = post.get("content", "").strip()
    created = post["created_at"]
    post_type = post.get("type", "post")
    thread_id = post.get("thread_id")
    participants = post.get("participants", [])
    reply_count = post.get("reply_count", 0)
    
    # Format timestamp
    try:
        dt = datetime.fromisoformat(created.replace("Z", "+00:00"))
        time_str = dt.strftime("%Y-%m-%d %H:%M:%S")
    except:
        time_str = created[:19] if len(created) > 19 else created
    
    # Check for display name collision
    has_collision = any(
        p["author_normalized"] == normalized and p["pubkey_suffix"] != pubkey_suffix
        for p in all_posts
    )
    
    if has_collision:
        author_display = f"{author} ({pubkey_suffix})"
    else:
        author_display = author
    
    # Choose icon based on type
    if post_type == "repost":
        icon = "🔁"
    elif post_type == "vote":
        value = post.get("value", 0)
        icon = "👍" if value == 1 else "👎"
    elif post_type == "reaction":
        icon = post.get("value", "❤️")
    elif post_type == "rating":
        stars = "⭐" * post.get("value", 0)
        icon = stars
    else:
        icon = "📝"
    
    # Build the post lines
    lines = []
    
    # Header with icon
    lines.append(f"[{time_str}] {author_display} {icon}")
    
    # Content (if any)
    if content:
        lines.append(f"  {content}")
    
    # Thread indicator - only show if thread_id exists and is not null/None
    if thread_id and thread_id.lower() != "null" and str(thread_id).strip():
        participant_count = len(participants) if participants else 1
        if reply_count > 0:
            lines.append(f"  💬 Thread ({participant_count} participants, {reply_count} replies)")
        else:
            lines.append(f"  💬 In thread: {thread_id[:12]}... ({participant_count} participants)")
        lines.append(f"  → filu-x thread show {thread_id[:12]}...")
    
    # Link
    lines.append(f"  fx://{post['cid']}")
    
    return "\n".join(lines)


def collect_posts(layout, limit: int) -> list:
    """
    Collect own posts + cached followed posts chronologically.
    
    Args:
        layout: Storage layout instance
        limit: Maximum number of posts to return
    
    Returns:
        List of post entries sorted by date (newest first)
    """
    posts = []
    
    # Collect own posts from IPFS protocol
    if layout.public_ipfs_dir.exists():
        posts_dir = layout.public_ipfs_dir / "posts"
        
        if posts_dir.exists():
            post_files = sorted(posts_dir.glob("*.json"), reverse=True)
            
            for post_path in post_files:
                try:
                    post = layout.load_json(post_path)
                    
                    post_entry = {
                        "author": post.get("author", "unknown"),
                        "author_normalized": normalize_display_name(post.get("author", "unknown")),
                        "pubkey_suffix": post.get("pubkey", "")[:6],
                        "content": post.get("content", ""),
                        "created_at": post.get("created_at", ""),
                        "cid": post.get("id", post_path.stem),
                        "source": "own",
                        "type": post.get("type", "post"),
                        "thread_id": post.get("thread_id"),
                        "participants": post.get("participants", []),
                        "reply_count": post.get("reply_count", 0)
                    }
                    
                    # Add type-specific fields
                    if "value" in post:
                        post_entry["value"] = post["value"]
                    if "reply_to" in post:
                        post_entry["reply_to"] = post["reply_to"]
                    
                    posts.append(post_entry)
                    
                except Exception as e:
                    # Silently skip corrupted posts
                    continue
    
    # Collect cached followed posts from IPFS cache
    cached_follows_dir = layout.base_path / "data" / "cached" / "ipfs" / "follows"
    
    if cached_follows_dir.exists():
        user_dirs = [d for d in cached_follows_dir.glob("*") if d.is_dir()]
        
        for user_dir in user_dirs:
            posts_dir = user_dir / "posts"
            
            if not posts_dir.exists():
                continue
            
            post_files = list(posts_dir.glob("*.json"))
            
            for post_path in post_files:
                try:
                    post = json.loads(post_path.read_text(encoding="utf-8"))
                    
                    post_entry = {
                        "author": post.get("author", user_dir.name),
                        "author_normalized": normalize_display_name(post.get("author", user_dir.name)),
                        "pubkey_suffix": post.get("pubkey", "")[:6],
                        "content": post.get("content", ""),
                        "created_at": post.get("created_at", ""),
                        "cid": post_path.stem,
                        "source": "followed",
                        "type": post.get("type", "post"),
                        "thread_id": post.get("thread_id"),
                        "participants": post.get("participants", []),
                        "reply_count": post.get("reply_count", 0)
                    }
                    
                    if "value" in post:
                        post_entry["value"] = post["value"]
                    if "reply_to" in post:
                        post_entry["reply_to"] = post["reply_to"]
                    
                    posts.append(post_entry)
                    
                except Exception as e:
                    # Silently skip corrupted posts
                    continue
    
    # Sort newest first
    posts.sort(key=lambda x: x["created_at"], reverse=True)
    
    return posts[:limit]


@click.command()
@click.pass_context
@click.option("--limit", "-l", default=20, help="Maximum number of posts to show")
@click.option("--raw", is_flag=True, help="Show raw JSON instead of formatted view")
@click.option("--threads", is_flag=True, help="Show thread structure (experimental)")
def feed(ctx, limit: int, raw: bool, threads: bool):
    """
    Show your feed – posts from you and followed users.
    
    Includes reactions, reposts, and thread awareness.
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
    
    # Collect posts
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
            click.echo(json.dumps(post, indent=2, ensure_ascii=False))
            if i < len(posts):
                click.echo("---")
        else:
            rendered = render_post_item(post, posts)
            click.echo(rendered)
            if i < len(posts):
                click.echo()
    
    # Show footer
    total_own = 0
    if layout.public_ipfs_dir.exists():
        posts_dir = layout.public_ipfs_dir / "posts"
        if posts_dir.exists():
            total_own = len(list(posts_dir.glob("*.json")))
    
    cached_follows_dir = layout.cached_follows_dir(protocol="ipfs")
    total_cached = 0
    if cached_follows_dir.exists():
        total_cached = sum(1 for p in cached_follows_dir.rglob("*.json") if p.parent.name == "posts")
    
    click.echo()
    click.echo(click.style(
        f"✨ Showing {len(posts)}/{total_own + total_cached} posts",
        fg="blue"
    ))
    click.echo()
    click.echo("💡 Tips:")
    click.echo("   • Sync followed users: filu-x sync-followed")
    click.echo("   • Sync your posts:     filu-x sync")
    click.echo("   • View threads:        filu-x thread show <cid>")
    click.echo("   • Follow threads:      filu-x thread follow <cid>")
    click.echo("   • React to posts:      filu-x post '!(upvote): Great!' --reply-to <cid>")
    
    # Show collision explanation if detected
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
