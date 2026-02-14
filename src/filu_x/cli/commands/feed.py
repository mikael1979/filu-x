"""Feed command – show posts from you and followed users"""
import sys
import click
from pathlib import Path
from datetime import datetime

from filu_x.storage.layout import FiluXStorageLayout

@click.command()
@click.option("--limit", "-l", default=20, help="Maximum number of posts to show")
@click.option("--raw", is_flag=True, help="Show raw JSON instead of formatted view")
def feed(limit: int, raw: bool):
    """
    Show your feed – posts from you and followed users.
    
    Alpha version (0.0.1) shows only YOUR posts.
    Beta version (0.1.x) will include followed users' posts via Nostr/IPFS sync.
    
    Example:
      filu-x feed --limit 10
      filu-x feed --raw
    """
    layout = FiluXStorageLayout()
    
    # 1. Tarkista että käyttäjä on alustettu
    if not layout.profile_path().exists():
        click.echo(click.style(
            "❌ User not initialized. Run first:\n"
            "   filu-x init <username> --no-password",
            fg="red"
        ))
        sys.exit(1)
    
    # 2. Lataa profiili
    profile = layout.load_json(layout.profile_path())
    username = profile.get("author", "unknown")
    
    # 3. Kerää postaukset (alpha: vain omat)
    posts = []
    
    # Omien postauksien keruu
    if layout.posts_dir.exists():
        for post_path in sorted(layout.posts_dir.glob("*.json"), reverse=True):
            try:
                post = layout.load_json(post_path)
                posts.append({
                    "author": username,
                    "content": post.get("content", ""),
                    "created_at": post.get("created_at", ""),
                    "cid": post.get("id", post_path.stem),
                    "raw": post
                })
            except Exception as e:
                click.echo(click.style(
                    f"⚠️  Skipping invalid post {post_path.name}: {e}",
                    fg="yellow"
                ))
    
    # 4. Näytä feed
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
        click.echo("   • Sync for updates:        filu-x sync")
        sys.exit(0)
    
    # Rajaa määrä
    posts = posts[:limit]
    
    click.echo(click.style(
        f"📬 Feed ({len(posts)} posts)",
        fg="cyan",
        bold=True
    ))
    click.echo()
    
    # Näytä postaukset
    for i, post in enumerate(posts, 1):
        if raw:
            # Raakamuoto
            import json
            click.echo(json.dumps(post["raw"], indent=2, ensure_ascii=False))
            if i < len(posts):
                click.echo("---")
        else:
            # Ihmisluettava muoto
            author = post["author"]
            content = post["content"].strip()
            created = post["created_at"]
            
            # Formatoi aika
            try:
                dt = datetime.fromisoformat(created.replace("Z", "+00:00"))
                time_str = dt.strftime("%Y-%m-%d %H:%M:%S")
            except:
                time_str = created[:19] if len(created) > 19 else created
            
            # Näytä postaus
            click.echo(f"[{time_str}] {author}")
            click.echo(f"  {content}")
            click.echo(f"  fx://{post['cid']}")
            if i < len(posts):
                click.echo()
    
    # Footer
    total_posts = len(list(layout.posts_dir.glob("*.json"))) if layout.posts_dir.exists() else 0
    click.echo()
    click.echo(click.style(
        f"✨ Showing {len(posts)}/{total_posts} of your posts (alpha version)",
        fg="blue"
    ))
    click.echo()
    click.echo("💡 Alpha limitation: Feed shows only YOUR posts.")
    click.echo("   Beta (0.1.x) will add followed users' posts via Nostr sync.")
