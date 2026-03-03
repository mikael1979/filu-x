"""Local command – manage local copies of posts with friendly names and manifest versions"""
import sys
import json
import shutil
from pathlib import Path
import click
from datetime import datetime

from filu_x.storage.layout import FiluXStorageLayout
from filu_x.core.id_generator import parse_local_id

@click.group(name="local")
def local():
    """Manage local copies of posts with friendly names and manifest versions"""
    pass

@local.command()
@click.pass_context
@click.argument("local_id")
def show(ctx, local_id: str):
    """
    Show a local post by its local ID.
    
    Examples:
      filu-x local show my-discussion.0_0_0_1_a1b2c3
      filu-x local show post42.0_0_0_1_d4e5f6
    """
    data_dir = ctx.obj.get("data_dir")
    layout = FiluXStorageLayout(base_path=data_dir)
    
    local_posts_dir = layout.base_path / "local" / "posts"
    local_path = local_posts_dir / local_id
    
    if not local_path.exists():
        click.echo(click.style(f"❌ Local post not found: {local_id}", fg="red"))
        
        # Try to find from mapping
        mapping_file = layout.base_path / "local" / "mapping.json"
        if mapping_file.exists():
            with open(mapping_file, 'r') as f:
                mapping = json.load(f)
            
            if local_id in mapping:
                click.echo(f"   Found in mapping but file missing: {mapping[local_id]['path']}")
        return
    
    # Display the post content
    with open(local_path, 'r') as f:
        content = json.load(f)
    
    # Parse local ID to show components
    parsed = parse_local_id(local_id)
    if parsed:
        click.echo(click.style(f"📋 Local ID: {local_id}", fg="cyan", bold=True))
        click.echo(f"   Name: {parsed['name']}")
        click.echo(f"   Manifest version: {parsed['manifest_version']}")
        click.echo(f"   Post fingerprint: {parsed['post_fingerprint']}")
        click.echo()
    
    # Show content preview
    if content.get("post_type") == "thread":
        click.echo(click.style(f"📌 Thread: {content.get('thread_title', 'Untitled')}", fg="green"))
        if content.get("thread_description"):
            click.echo(f"   {content['thread_description']}")
    else:
        click.echo(click.style(f"📝 Post", fg="green"))
    
    click.echo(f"   Author: {content.get('author', 'unknown')}")
    click.echo(f"   Created: {content.get('created_at', 'unknown')[:16]}")
    click.echo(f"\n   Content: {content.get('content', '[No content]')}")
    
    # Show full JSON with --raw option
    if ctx.obj.get("raw"):
        click.echo("\n" + json.dumps(content, indent=2, ensure_ascii=False))

@local.command()
@click.pass_context
def list(ctx):
    """List all local posts with their local IDs"""
    data_dir = ctx.obj.get("data_dir")
    layout = FiluXStorageLayout(base_path=data_dir)
    
    mapping_file = layout.base_path / "local" / "mapping.json"
    local_posts_dir = layout.base_path / "local" / "posts"
    
    if not mapping_file.exists() or not local_posts_dir.exists():
        click.echo(click.style("📭 No local posts found", fg="yellow"))
        return
    
    with open(mapping_file, 'r') as f:
        mapping = json.load(f)
    
    if not mapping:
        click.echo(click.style("📭 No local posts found", fg="yellow"))
        return
    
    click.echo(click.style("📋 Local posts:", fg="cyan", bold=True))
    
    # Sort by creation date (newest first)
    sorted_items = sorted(mapping.items(), 
                          key=lambda x: x[1].get('created_at', ''), 
                          reverse=True)
    
    for local_id, info in sorted_items:
        post_type = info.get('post_type', 'simple')
        title = info.get('title')
        created = info.get('created_at', '')[:16].replace('T', ' ')
        manifest_version = info.get('manifest_version', 'unknown')
        
        if post_type == 'thread' and title:
            display = f"📌 {title}"
        else:
            display = f"📝 Post"
        
        click.echo(f"   • {local_id}")
        click.echo(f"     {display} ({created})")
        click.echo(f"     Manifest: {manifest_version}")

@local.command()
@click.pass_context
@click.argument("local_id")
@click.argument("new_name")
def rename(ctx, local_id: str, new_name: str):
    """
    Rename a local post (changes only the name part, keeps manifest version and hash).
    
    Examples:
      filu-x local rename my-discussion.0_0_0_1_a1b2c3 updated-discussion
    """
    data_dir = ctx.obj.get("data_dir")
    layout = FiluXStorageLayout(base_path=data_dir)
    
    # Parse the local ID
    parsed = parse_local_id(local_id)
    if not parsed:
        click.echo(click.style(f"❌ Invalid local ID format: {local_id}", fg="red"))
        return
    
    # Sanitize new name
    import re
    safe_name = new_name.strip().lower()
    safe_name = re.sub(r'[^a-z0-9]+', '-', safe_name)
    safe_name = safe_name.strip('-')
    
    if not safe_name:
        click.echo(click.style(f"❌ Invalid name after sanitization: {new_name}", fg="red"))
        return
    
    # Construct new local ID
    new_local_id = f"{safe_name}.{parsed['manifest_version'].replace('.', '_')}_{parsed['post_fingerprint']}"
    
    # Check if files exist
    local_posts_dir = layout.base_path / "local" / "posts"
    old_path = local_posts_dir / local_id
    new_path = local_posts_dir / new_local_id
    
    if not old_path.exists():
        click.echo(click.style(f"❌ Local post not found: {local_id}", fg="red"))
        return
    
    if new_path.exists():
        click.echo(click.style(f"❌ Target name already exists: {new_local_id}", fg="red"))
        return
    
    # Rename the file
    old_path.rename(new_path)
    
    # Update mapping
    mapping_file = layout.base_path / "local" / "mapping.json"
    if mapping_file.exists():
        with open(mapping_file, 'r') as f:
            mapping = json.load(f)
        
        if local_id in mapping:
            mapping[new_local_id] = mapping.pop(local_id)
            mapping[new_local_id]["path"] = str(new_path)
            
            with open(mapping_file, 'w') as f:
                json.dump(mapping, f, indent=2)
    
    click.echo(click.style(f"✅ Renamed: {local_id} → {new_local_id}", fg="green"))

@local.command()
@click.pass_context
@click.argument("local_id")
@click.option("--force", "-f", is_flag=True, help="Force deletion without confirmation")
def rm(ctx, local_id: str, force: bool):
    """
    Remove a local post (does not affect IPFS version).
    
    Examples:
      filu-x local rm my-discussion.0_0_0_1_a1b2c3
    """
    data_dir = ctx.obj.get("data_dir")
    layout = FiluXStorageLayout(base_path=data_dir)
    
    local_posts_dir = layout.base_path / "local" / "posts"
    local_path = local_posts_dir / local_id
    
    if not local_path.exists():
        click.echo(click.style(f"❌ Local post not found: {local_id}", fg="red"))
        return
    
    # Confirm deletion
    if not force:
        click.echo(click.style(f"🗑️  Delete local post: {local_id}", fg="yellow"))
        if not click.confirm("   Confirm?"):
            click.echo("Cancelled.")
            return
    
    # Delete the file
    local_path.unlink()
    
    # Update mapping
    mapping_file = layout.base_path / "local" / "mapping.json"
    if mapping_file.exists():
        with open(mapping_file, 'r') as f:
            mapping = json.load(f)
        
        if local_id in mapping:
            del mapping[local_id]
            
            with open(mapping_file, 'w') as f:
                json.dump(mapping, f, indent=2)
    
    click.echo(click.style(f"✅ Deleted: {local_id}", fg="green"))

@local.command()
@click.pass_context
@click.argument("local_id")
def info(ctx, local_id: str):
    """
    Show detailed information about a local post.
    
    Examples:
      filu-x local info my-discussion.0_0_0_1_a1b2c3
    """
    data_dir = ctx.obj.get("data_dir")
    layout = FiluXStorageLayout(base_path=data_dir)
    
    # Parse the local ID
    parsed = parse_local_id(local_id)
    if not parsed:
        click.echo(click.style(f"❌ Invalid local ID format: {local_id}", fg="red"))
        return
    
    click.echo(click.style(f"📋 Local ID Info: {local_id}", fg="cyan", bold=True))
    click.echo(f"   Name: {parsed['name']}")
    click.echo(f"   Manifest version: {parsed['manifest_version']}")
    click.echo(f"   Post fingerprint: {parsed['post_fingerprint']}")
    
    # Check mapping
    mapping_file = layout.base_path / "local" / "mapping.json"
    if mapping_file.exists():
        with open(mapping_file, 'r') as f:
            mapping = json.load(f)
        
        if local_id in mapping:
            info = mapping[local_id]
            click.echo(f"\n   Post ID: {info.get('post_id', 'unknown')[:16]}...")
            click.echo(f"   Created: {info.get('created_at', 'unknown')[:16]}")
            click.echo(f"   Type: {info.get('post_type', 'unknown')}")
            if info.get('title'):
                click.echo(f"   Title: {info['title']}")
    
    # Check if file exists
    local_posts_dir = layout.base_path / "local" / "posts"
    local_path = local_posts_dir / local_id
    
    if local_path.exists():
        size = local_path.stat().st_size
        click.echo(f"\n   File: {local_path}")
        click.echo(f"   Size: {size} bytes")
    else:
        click.echo(f"\n   ⚠️  File missing: {local_path}")
