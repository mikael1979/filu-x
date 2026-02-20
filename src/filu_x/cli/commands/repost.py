"""Repost command – share someone else's post with optional comment"""
import sys
import click
from datetime import datetime, timezone

from filu_x.storage.layout import FiluXStorageLayout
from filu_x.core.resolver import LinkResolver, ResolutionError, SecurityError
from filu_x.core.ipfs_client import IPFSClient
from filu_x.core.crypto import sign_json
from filu_x.core.id_generator import generate_post_id

@click.command()
@click.pass_context
@click.argument("target")
@click.option("--comment", "-c", help="Optional comment to add to repost")
@click.option("--force", is_flag=True, help="Skip signature verification (use with caution!)")
def repost(ctx, target: str, comment: str = None, force: bool = False):
    """
    Repost someone else's content with optional comment.
    
    Creates a new post of type "repost" that references the original.
    The repost will appear in your feed with a 🔁 icon.
    
    Examples:
      filu-x repost fx://bafkreifdjx22gltzus6iddt7yjhbrg2enj5djfvbbrn263jtbbbmftoys4
      filu-x repost fx://bafkrei... --comment "Check this out!"
      filu-x repost bafkreifdjx22gltzus6iddt7yjhbrg2enj5djfvbbrn263jtbbbmftoys4
    """
    data_dir = ctx.obj.get("data_dir")
    layout = FiluXStorageLayout(base_path=data_dir)
    
    # 1. Verify user is initialized
    if not layout.profile_path().exists():
        click.echo(click.style(
            "❌ User not initialized. Run first:\n"
            "   filu-x init <username>",
            fg="red"
        ))
        sys.exit(1)
    
    # 2. Load profile and private key
    try:
        profile = layout.load_json(layout.profile_path())
        with open(layout.private_key_path(), "rb") as f:
            privkey_bytes = f.read()
    except FileNotFoundError as e:
        click.echo(click.style(f"❌ Error loading keys: {e}", fg="red"))
        sys.exit(1)
    
    # 3. Parse target (supports fx:// links or direct CIDs)
    if target.startswith("fx://"):
        cid = target[5:]  # Remove fx:// prefix
    else:
        cid = target  # Assume it's a raw CID
    
    # Validate CID length (basic check)
    if len(cid) < 10:
        click.echo(click.style(
            f"❌ Invalid CID: too short ({len(cid)} chars). Expected at least 10 chars.",
            fg="red"
        ))
        click.echo()
        click.echo("💡 Use a complete CID (46+ chars for IPFS CIDs)")
        sys.exit(1)
    
    # 4. Initialize resolver and fetch original post
    ipfs = IPFSClient(mode="auto")
    resolver = LinkResolver(ipfs_client=ipfs)
    
    try:
        if not force:
            click.echo(click.style(f"🔍 Fetching original post...", fg="cyan"))
            
            # Resolve and verify original content
            original = resolver.resolve_content(cid, skip_cache=False)
            
            # Verify this is a post (has required fields)
            if "author" not in original:
                click.echo(click.style(
                    "⚠️  Warning: Target may not be a post (missing 'author' field)",
                    fg="yellow"
                ))
                if not click.confirm("Repost anyway?"):
                    sys.exit(1)
            
            # Extract original metadata
            original_author = original.get("author", "unknown")
            original_content = original.get("content", "")[:60]
            original_pubkey = original.get("pubkey", "unknown")
            original_type = original.get("type", "post")
            
            click.echo(click.style(
                f"✅ Original post by {original_author}:",
                fg="green"
            ))
            if original_content:
                click.echo(f"   \"{original_content}...\"")
            else:
                click.echo(f"   [{original_type}]")
            click.echo()
            
        else:
            # Force mode: skip resolution
            original = None
            original_author = "unknown"
            original_pubkey = "unknown"
            original_type = "post"
            click.echo(click.style(
                "⚠️  Skipping verification (--force mode)",
                fg="yellow"
            ))
    
    except ResolutionError as e:
        click.echo(click.style(f"❌ Failed to resolve original post: {e}", fg="red"))
        if not force:
            click.echo("   Try again with --force to skip verification")
        sys.exit(1)
    
    except SecurityError as e:
        click.echo(click.style(f"🔒 SECURITY BLOCKED: {e}", fg="red", bold=True))
        click.echo("   The original post failed cryptographic verification")
        sys.exit(1)
    
    # 5. Create repost
    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    
    # Generate deterministic ID for the repost itself
    repost_id = generate_post_id(
        pubkey=profile["pubkey"],
        timestamp=now,
        content=comment or ""  # Empty comment still affects hash
    )
    
    # Build repost data
    repost_data = {
        "version": "0.0.5",
        "id": repost_id,
        "author": profile["author"],
        "pubkey": profile["pubkey"],
        "type": "repost",
        "content": comment or "",
        "content_type": "text/plain",
        "original_post_cid": cid,
        "original_author": original_author,
        "original_pubkey": original_pubkey,
        "original_type": original_type,
        "thread_id": None,  # Reposts don't participate in threads by default
        "created_at": now,
        "updated_at": now,
        "signature": ""
    }
    
    # Sign the repost
    repost_data["signature"] = sign_json(repost_data, privkey_bytes)
    
    # 6. Save repost locally
    post_path = layout.post_path(repost_id)
    layout.save_json(post_path, repost_data, private=False)
    
    # 7. Update manifest
    manifest_path = layout.manifest_path()
    if manifest_path.exists():
        manifest = layout.load_json(manifest_path)
    else:
        manifest = {
            "version": "0.0.5",
            "author": profile["author"],
            "root_cid": None,
            "entries": [],
            "signature": ""
        }
    
    # Add to manifest
    manifest["entries"].append({
        "path": f"posts/{repost_id}.json",
        "cid": repost_id,
        "type": "repost",
        "created_at": now,
        "priority": len(manifest.get("entries", [])) + 1
    })
    
    manifest["signature"] = sign_json(manifest, privkey_bytes)
    layout.save_json(manifest_path, manifest, private=False)
    
    # 8. Update profile's feed_cid (point to latest manifest)
    profile["feed_cid"] = repost_id  # In alpha, just point to latest
    profile["updated_at"] = now
    profile["signature"] = sign_json(profile, privkey_bytes)
    layout.save_json(layout.profile_path(), profile, private=False)
    
    # 9. Show success message
    click.echo(click.style(
        f"✅ Repost created: {repost_id[:16]}...",
        fg="green",
        bold=True
    ))
    
    if comment:
        preview = comment[:50] + "..." if len(comment) > 50 else comment
        click.echo(f"   Comment: {preview}")
    
    click.echo(f"   Original: {cid[:16]}... by {original_author}")
    click.echo(f"   File: {post_path}")
    
    # Suggest next steps
    click.echo()
    click.echo(click.style("💡 Next steps:", fg="blue"))
    click.echo("   • See your feed:        filu-x feed")
    click.echo("   • Sync to IPFS:         filu-x sync")
    click.echo("   • Share the link:       filu-x link " + repost_id[:16] + "...")
