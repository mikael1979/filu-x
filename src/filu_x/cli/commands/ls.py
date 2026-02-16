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
def ls(ctx, posts: bool, follows: bool, raw: bool):
    """
    List local Filu-X files and status.
    
    Shows your posts, profile, follow list, and cached content without
    requiring IPFS daemon or network connection.
    
    Examples:
      filu-x ls                # Show all local content
      filu-x ls --posts        # Show only your posts
      filu-x ls --follows      # Show followed users
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
        if layout.posts_dir.exists():
            post_files = sorted(layout.posts_dir.glob("*.json"), reverse=True)
            if post_files:
                click.echo(click.style("📝 Your posts:", fg="green", bold=True))
                for i, post_path in enumerate(post_files[:10], 1):  # Limit to 10
                    if raw:
                        click.echo(f"   {post_path}")
                    else:
                        try:
                            post = layout.load_json(post_path)
                            content = post.get("content", "")[:50]
                            created = post.get("created_at", "")[:16].replace("T", " ")
                            click.echo(f"   [{i}] {created} | {content}")
                        except Exception:
                            click.echo(f"   [{i}] {post_path.name} (unreadable)")
                if len(post_files) > 10:
                    click.echo(f"   ... and {len(post_files) - 10} more")
                click.echo()
            else:
                click.echo(click.style("📭 No posts yet", fg="yellow"))
                click.echo()
    
    # Lisää TÄMÄ posts-kokoelman jälkeen (noin rivi 45):

        # Collect reposts
        if layout.posts_dir.exists():
            for post_path in sorted(layout.posts_dir.glob("*.json"), reverse=True):
                try:
                    post = layout.load_json(post_path)
                    if post.get("type") == "repost":
                        posts.append({
                            "author": post.get("author", "unknown"),
                            "author_normalized": normalize_display_name(post.get("author", "unknown")),
                            "pubkey_suffix": post.get("pubkey", "")[:6],
                            "content": post.get("comment", ""),
                            "created_at": post.get("created_at", ""),
                            "cid": post.get("id", post_path.stem),
                            "source": "own",
                            "type": "repost",
                            "original_author": post.get("original_author", "unknown"),
                            "original_post_cid": post.get("original_post_cid", "")[:12]
                        })
                except Exception:
                    continue
    
    # Show follows
    if not posts or follows:
        follow_list_path = layout.follow_list_path()
        if follow_list_path.exists():
            follow_list = layout.load_json(follow_list_path)
            follows_list = follow_list.get("follows", [])
            if follows_list:
                click.echo(click.style("👥 Followed users:", fg="blue", bold=True))
                for i, follow in enumerate(follows_list, 1):
                    user = follow.get("user", "unknown")
                    cid = follow.get("profile_cid", "")[:12]
                    click.echo(f"   [{i}] {user} (CID: {cid}...)")
                click.echo()
            else:
                click.echo(click.style("📭 Not following anyone yet", fg="yellow"))
                click.echo()
    
    # Show cached content
    cached_base = layout.base_path / "data" / "cached" / "follows"
    if cached_base.exists() and not posts and not follows:
        cached_users = [d for d in cached_base.glob("*") if d.is_dir()]
        if cached_users:
            click.echo(click.style("📦 Cached content:", fg="magenta", bold=True))
            total_posts = 0
            for user_dir in cached_users:
                posts_dir = user_dir / "posts"
                if posts_dir.exists():
                    post_count = len(list(posts_dir.glob("*.json")))
                    total_posts += post_count
                    click.echo(f"   • {user_dir.name}: {post_count} posts")
            click.echo(f"   Total cached posts: {total_posts}")
            click.echo()
    
    # Show disk usage
    total_size = sum(
        f.stat().st_size 
        for f in layout.base_path.rglob("*") 
        if f.is_file()
    ) / 1024 / 1024
    
    click.echo(click.style(f"💾 Disk usage: {total_size:.2f} MB", fg="cyan"))
