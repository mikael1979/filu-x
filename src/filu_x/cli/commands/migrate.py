# src/filu_x/cli/commands/migrate.py
import json
import click
from pathlib import Path
from filu_x.storage.layout import FiluXStorageLayout

def migrate_post_to_v008(old_post: dict) -> dict:
    """Migrate old format post to new protocol-grouped format"""
    # Base structure
    new_post = {
        "version": "0.0.8",
        "id": old_post.get("id"),
        "local_id": old_post.get("local_id", ""),
        "author": old_post.get("author"),
        "pubkey": old_post.get("pubkey"),
        "content": old_post.get("content"),
        "protocols": {
            "ipfs": {
                "cid": old_post.get("cid"),
                "gateway": "https://ipfs.io/ipfs/",
                "ipns": {
                    "name": old_post.get("ipns") or old_post.get("thread_ipns"),
                    "gateway": "https://ipfs.io/ipns/",
                    "sequence": 0,
                    "previous": None
                }
            },
            "http": {
                "primary": old_post.get("http_url"),
                "mirrors": [],
                "last_checked": None
            },
            "nostr": {
                "event_id": None,
                "relay": None,
                "kind": 1,
                "tags": []
            },
            "freenet": {
                "uri": None,
                "key": None,
                "edition": 0
            },
            "hypercore": {
                "key": None,
                "seq": 0
            },
            "activitypub": {
                "uri": None,
                "type": "Note",
                "inbox": None
            }
        },
        "attachments": [],
        "prev_post_cid": old_post.get("prev_post_cid"),
        "tags": old_post.get("tags", []),
        "thread_title": old_post.get("thread_title"),
        "thread_description": old_post.get("thread_description"),
        "thread_id": old_post.get("thread_id"),
        "reply_to": old_post.get("reply_to"),
        "participants": old_post.get("participants", []),
        "reply_count": old_post.get("reply_count", 0),
        "created_at": old_post.get("created_at"),
        "updated_at": old_post.get("updated_at"),
        "signature": old_post.get("signature")
    }
    
    # Clean up None values
    for key in list(new_post.keys()):
        if new_post[key] is None:
            del new_post[key]
    
    return new_post

@click.command()
@click.pass_context
@click.option("--dry-run", is_flag=True, help="Show what would be migrated without making changes")
def migrate(ctx, dry_run: bool):
    """Migrate posts to latest format (currently 0.0.8)"""
    data_dir = ctx.obj.get("data_dir")
    layout = FiluXStorageLayout(base_path=data_dir)
    
    posts_dir = layout.public_ipfs_dir / "posts"
    if not posts_dir.exists():
        click.echo("📭 No posts found to migrate")
        return
    
    migrated = 0
    for post_path in posts_dir.glob("*.json"):
        with open(post_path) as f:
            old_post = json.load(f)
        
        # Check version
        if old_post.get("version") == "0.0.8":
            continue
        
        new_post = migrate_post_to_v008(old_post)
        
        if dry_run:
            click.echo(f"📄 Would migrate: {post_path.name}")
            migrated += 1
        else:
            # Backup old version
            backup_path = post_path.with_suffix(".json.bak")
            post_path.rename(backup_path)
            
            # Save new version
            with open(post_path, "w") as f:
                json.dump(new_post, f, indent=2)
            
            click.echo(f"✅ Migrated: {post_path.name}")
            migrated += 1
    
    click.echo(f"\n📊 Migrated {migrated} posts to format 0.0.8")
