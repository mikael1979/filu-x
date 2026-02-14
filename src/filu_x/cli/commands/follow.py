# src/filu_x/cli/commands/follow.py
"""Follow command – add users to your follow list by fx:// link"""
import sys
import json
from datetime import datetime, timezone
import click

from filu_x.storage.layout import FiluXStorageLayout
from filu_x.core.resolver import LinkResolver, ResolutionError, SecurityError
from filu_x.core.ipfs_client import IPFSClient
from filu_x.core.crypto import sign_json

@click.command()
@click.argument("target")
@click.option("--alias", "-a", help="Custom display name for this user")
@click.option("--force", is_flag=True, help="Skip signature verification (use with caution!)")
def follow(target: str, alias: str = None, force: bool = False):
    """
    Follow a user by fx:// profile link.
    
    The target must be a profile link (fx://bafkrei...) – not a post link.
    Filu-X will verify the cryptographic signature before adding to your follow list.
    
    Examples:
      filu-x follow fx://bafkreiabc123...
      filu-x follow fx://bafkreiabc123... --alias Alice
    """
    layout = FiluXStorageLayout()
    
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
    
    # 3. Check target is fx:// link
    if not target.startswith("fx://"):
        click.echo(click.style(
            f"❌ Invalid target format. Expected fx:// link, got:\n"
            f"   {target}",
            fg="red"
        ))
        click.echo("\n💡 Tip: Get profile link with 'filu-x link --profile'")
        sys.exit(1)
    
    # 4. Initialize resolver and resolve profile
    ipfs = IPFSClient(mode="auto")
    resolver = LinkResolver(ipfs_client=ipfs)
    
    try:
        # Parse link
        parsed = resolver.parse_fx_link(target)
        cid = parsed["cid"]
        
        # Resolve content
        if not force:
            click.echo(click.style(f"🔍 Verifying profile signature...", fg="cyan"))
            profile_data = resolver.resolve_content(cid, skip_cache=False)
            
            # Verify this is a profile (not a post)
            if "author" not in profile_data or "feed_cid" not in profile_
                click.echo(click.style(
                    "⚠️  Warning: Target may not be a profile (missing 'author' or 'feed_cid' fields)",
                    fg="yellow"
                ))
                if not click.confirm("Continue anyway?"):
                    sys.exit(1)
            
            author = profile_data.get("author", cid[:12])
            pubkey_preview = profile_data.get("pubkey", "")[:12] + "..."
            
            click.echo(click.style(
                f"✅ Verified profile: {author} (pubkey: {pubkey_preview})",
                fg="green"
            ))
        else:
            # Force mode: skip resolution
            profile_data = None
            author = alias or cid[:12]
            pubkey_preview = "unknown"
            click.echo(click.style(
                "⚠️  Skipping verification (--force mode)",
                fg="yellow"
            ))
    
    except ResolutionError as e:
        click.echo(click.style(f"❌ Failed to resolve profile: {e}", fg="red"))
        if not force:
            click.echo("   Try again with --force to skip verification")
        sys.exit(1)
    
    except SecurityError as e:
        click.echo(click.style(f"🔒 SECURITY BLOCKED: {e}", fg="red", bold=True))
        click.echo("   This profile failed cryptographic verification")
        sys.exit(1)
    
    except Exception as e:
        click.echo(click.style(f"❌ Unexpected error: {e}", fg="red"))
        sys.exit(1)
    
    # 5. Update follow list
    follow_list_path = layout.follow_list_path()
    
    if follow_list_path.exists():
        follow_list = layout.load_json(follow_list_path)
        follows = follow_list.get("follows", [])
    else:
        follows = []
        follow_list = {
            "version": "0.0.1",
            "author": profile["author"],
            "pubkey": profile["pubkey"],
            "follows": follows,
            "updated_at": "",
            "signature": ""
        }
    
    # Check if already following
    if any(f["profile_cid"] == cid for f in follows):
        click.echo(click.style(
            f"⚠️  You already follow this user",
            fg="yellow"
        ))
        sys.exit(0)
    
    # Add new follow
    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    follows.append({
        "user": alias or author,
        "profile_link": f"fx://{cid}",
        "profile_cid": cid,
        "pubkey": profile_data.get("pubkey", "unknown") if profile_data else "unknown",
        "discovered_via": "manual",
        "discovered_at": now,
        "last_sync": now,
        "trust_score": 1.0
    })
    
    follow_list["follows"] = follows
    follow_list["updated_at"] = now
    
    # Sign new list
    follow_list["signature"] = sign_json(follow_list, privkey_bytes)
    
    # Save
    layout.save_json(follow_list_path, follow_list, private=False)
    
    # 6. Show result
    display_name = alias or author
    click.echo()
    click.echo(click.style(
        f"✅ Now following {display_name}",
        fg="green",
        bold=True
    ))
    click.echo(f"   Profile: fx://{cid}")
    click.echo(f"   Posts: will appear in feed after sync")
    
    # Suggest next steps
    click.echo()
    click.echo(click.style(
        "💡 Next steps:",
        fg="blue"
    ))
    click.echo("   • See your feed:        filu-x feed")
    click.echo("   • Sync for new posts:   filu-x sync")
    click.echo("   • List follows:         cat ~/.local/share/filu-x/data/public/follow_list.json")
