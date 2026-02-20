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
    """
    author = post["author"]
    normalized = post["author_normalized"]
    pubkey_suffix = post["pubkey_suffix"]
    content = post.get("content", "").strip()
    created = post["created_at"]
    post_type = post.get("type", "post")
    thread_id = post.get("thread_id")
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
    if icon:
        lines.append(f"[{time_str}] {author_display} {icon}")
    else:
        lines.append(f"[{time_str}] {author_display}")
    
    # Content (if any)
    if content:
        lines.append(f"  {content}")
    
    # Thread indicator
    if thread_id:
        if reply_count > 0:
            lines.append(f"  💬 Thread ({reply_count} replies)")
        else:
            lines.append(f"  💬 In thread: {thread_id[:12]}...")
    
    # Link
    lines.append(f"  fx://{post['cid']}")
    
    return "\n".join(lines)


def collect_posts(layout, limit: int) -> list:
    """
    Collect own posts + cached followed posts chronologically.
    Now includes reaction types and thread info.
    """
    posts = []
    
    # Collect own posts
    if layout.posts_dir.exists():
        for post_path in sorted(layout.posts_dir.glob("*.json"), reverse=True):
            try:
                post = layout.load_json(post_path)
                
                # Base post info
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
                    "reply_count": post.get("reply_count", 0)
                }
                
                # Add type-specific fields
                if "value" in post:
                    post_entry["value"] = post["value"]
                if "reply_to" in post:
                    post_entry["reply_to"] = post["reply_to"]
                
                posts.append(post_entry)
                
            except Exception as e:
                continue
    
    # Sort newest first
    posts.sort(key=lambda x: x["created_at"], reverse=True)
    return posts[:limit]


@click.command()
@click.pass_context
@click.option("--limit", "-l", default=20, help="Maximum number of posts to show")
@click.option("--raw", is_flag=True, help="Show raw JSON instead of formatted view")
@click.option("--threads", is_flag=True, help="Show thread structure")
def feed(ctx, limit: int, raw: bool, threads: bool):
    """
    Show your feed – posts from you and followed users.
    
    Alpha 0.0.5: Includes reactions, reposts, and thread awareness.
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
    total_own = len(list(layout.posts_dir.glob("*.json"))) if layout.posts_dir.exists() else 0
    
    click.echo()
    click.echo(click.style(
        f"✨ Showing {len(posts)}/{total_own} posts (alpha 0.0.5)",
        fg="blue"
    ))
    click.echo()
    click.echo("💡 Tips:")
    click.echo("   • Sync followed users: filu-x sync-followed")
    click.echo("   • Sync your posts:     filu-x sync")
    click.echo("   • View threads:        filu-x thread show <cid>")
    click.echo("   • Follow threads:      filu-x thread follow <cid>")
