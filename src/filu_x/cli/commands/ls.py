"""List local Filu-X files and status"""
import sys
from pathlib import Path
import click
from datetime import datetime

from filu_x.storage.layout import FiluXStorageLayout

@click.command()
@click.pass_context
@click.option("--posts", is_flag=True, help="Show only posts")
@click.option("--follows", is_flag=True, help="Show only followed users")
@click.option("--raw", is_flag=True, help="Show raw file paths")
@click.option("--threads", is_flag=True, help="Show thread information")
def ls(ctx, posts: bool, follows: bool, raw: bool, threads: bool):
    """
    List local Filu-X files and status.
    
    Shows your posts, profile, follow list, and cached content without
    requiring IPFS daemon or network connection.
    
    Examples:
      filu-x ls                # Show all local content
      filu-x ls --posts        # Show only your posts
      filu-x ls --follows      # Show followed users
      filu-x ls --threads      # Show thread information
    """
    data_dir = ctx.obj.get("data_dir")
    layout = FiluXStorageLayout(base_path=data_dir)
    
    # Verify user is initialized
    if not layout.profile_path().exists():
        click.echo(click.style(
            "❌ User not initialized. Run: filu-x init <username>",
            fg="red"
        ))
        sys.exit(1)
    
    # Load profile for context
    profile = layout.load_json(layout.profile_path())
    username = profile.get("author", "unknown")
    
    click.echo(click.style(f"📁 Local Filu-X data for {username}", fg="cyan", bold=True))
    click.echo(f"   Data directory: {layout.base_path}")
    click.echo()
    
    # Show posts
    if not follows or posts:
        _show_posts(layout, raw, threads)
    
    # Show follows
    if not posts or follows:
        _show_follows(layout)
    
    # Show cached content
    if not posts and not follows:
        _show_cached(layout)
    
    # Show disk usage
    _show_disk_usage(layout)


def _show_posts(layout: FiluXStorageLayout, raw: bool, show_threads: bool):
    """Display user's posts with optional thread information"""
    if not layout.posts_dir.exists():
        click.echo(click.style("📭 No posts yet", fg="yellow"))
        click.echo()
        return
    
    post_files = sorted(layout.posts_dir.glob("*.json"), reverse=True)
    if not post_files:
        click.echo(click.style("📭 No posts yet", fg="yellow"))
        click.echo()
        return
    
    click.echo(click.style("📝 Your posts:", fg="green", bold=True))
    
    for i, post_path in enumerate(post_files[:10], 1):  # Limit to 10
        if raw:
            click.echo(f"   {post_path}")
            continue
        
        try:
            post = layout.load_json(post_path)
            
            # Extract basic info
            post_type = post.get("type", "post")
            created = post.get("created_at", "")[:16].replace("T", " ")
            thread_id = post.get("thread_id", "")
            reply_count = post.get("reply_count", 0)
            
            # Format content based on type
            if post_type == "repost":
                original = post.get("original_author", "unknown")
                comment = post.get("comment", "")
                preview = f"🔁 {original}: {comment}"[:50]
            elif post_type == "vote":
                value = post.get("value", 0)
                action = "👍" if value == 1 else "👎"
                content = post.get("content", "")[:30]
                preview = f"{action} {content}"[:50]
            elif post_type == "reaction":
                emoji = post.get("value", "❤️")
                content = post.get("content", "")[:30]
                preview = f"❤️ {emoji} {content}"[:50]
            elif post_type == "rating":
                stars = "⭐" * post.get("value", 0)
                content = post.get("content", "")[:30]
                preview = f"{stars} {content}"[:50]
            else:  # regular post
                content = post.get("content", "")[:50]
                preview = content
            
            # Build display line
            line = f"   [{i}] {created} | {preview}"
            
            # Add thread indicators if requested
            if show_threads and thread_id:
                if reply_count > 0:
                    line += f" (thread: {reply_count} replies)"
                else:
                    line += f" (in thread: {thread_id[:8]}...)"
            
            click.echo(line)
            
        except Exception as e:
            click.echo(f"   [{i}] {post_path.name} (unreadable: {e})")
    
    if len(post_files) > 10:
        click.echo(f"   ... and {len(post_files) - 10} more")
    click.echo()


def _show_follows(layout: FiluXStorageLayout):
    """Display followed users"""
    follow_list_path = layout.follow_list_path()
    if not follow_list_path.exists():
        click.echo(click.style("📭 Not following anyone yet", fg="yellow"))
        click.echo()
        return
    
    follow_list = layout.load_json(follow_list_path)
    follows_list = follow_list.get("follows", [])
    
    if not follows_list:
        click.echo(click.style("📭 Not following anyone yet", fg="yellow"))
        click.echo()
        return
    
    click.echo(click.style("👥 Followed users:", fg="blue", bold=True))
    for i, follow in enumerate(follows_list, 1):
        user = follow.get("user", "unknown")
        cid = follow.get("profile_cid", "")[:12]
        pubkey = follow.get("pubkey", "")[:8]
        
        # Check if we have cached content
        cached_dir = layout.cached_user_path(user)
        has_cache = cached_dir.exists() and any(cached_dir.glob("posts/*.json"))
        cache_indicator = " 📦" if has_cache else ""
        
        click.echo(f"   [{i}] {user} ({pubkey}) CID: {cid}...{cache_indicator}")
    click.echo()


def _show_cached(layout: FiluXStorageLayout):
    """Display cached content from followed users"""
    cached_base = layout.cached_follows_path()
    if not cached_base.exists():
        return
    
    cached_users = [d for d in cached_base.glob("*") if d.is_dir()]
    if not cached_users:
        return
    
    click.echo(click.style("📦 Cached content:", fg="magenta", bold=True))
    total_posts = 0
    
    for user_dir in sorted(cached_users):
        posts_dir = user_dir / "posts"
        if posts_dir.exists():
            post_count = len(list(posts_dir.glob("*.json")))
            total_posts += post_count
            
            # Count threads
            thread_count = 0
            thread_ids = set()
            for post_path in posts_dir.glob("*.json"):
                try:
                    post = layout.load_json(post_path)
                    thread_id = post.get("thread_id")
                    if thread_id:
                        thread_ids.add(thread_id)
                except:
                    pass
            thread_count = len(thread_ids)
            
            if thread_count > 0:
                click.echo(f"   • {user_dir.name}: {post_count} posts, {thread_count} threads")
            else:
                click.echo(f"   • {user_dir.name}: {post_count} posts")
    
    click.echo(f"   Total cached posts: {total_posts}")
    click.echo()


def _show_disk_usage(layout: FiluXStorageLayout):
    """Calculate and display disk usage"""
    total_size = sum(
        f.stat().st_size 
        for f in layout.base_path.rglob("*") 
        if f.is_file()
    ) / 1024 / 1024  # Convert to MB
    
    click.echo(click.style(f"💾 Disk usage: {total_size:.2f} MB", fg="cyan"))
