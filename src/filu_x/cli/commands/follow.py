"""Follow command – add users to your follow list by fx:// link with collision detection"""
import sys
import json
from datetime import datetime, timezone
import click

from filu_x.storage.layout import FiluXStorageLayout
from filu_x.core.resolver import LinkResolver, ResolutionError, SecurityError
from filu_x.core.ipfs_client import IPFSClient
from filu_x.core.crypto import sign_json
from filu_x.core.id_generator import detect_display_name_collision, normalize_display_name  # NEW IMPORT

@click.command()
@click.pass_context
@click.argument("target")
@click.option("--alias", "-a", help="Custom display name for this user")
@click.option("--force", is_flag=True, help="Skip signature verification (use with caution!)")
def follow(ctx, target: str, alias: str = None, force: bool = False):
    """
    Follow a user by fx:// profile link.
    
    Detects display name collisions (same @name, different pubkey) and warns user.
    Identity is cryptographic (pubkey), not social (display name).
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
            if "author" not in profile_data or "feed_cid" not in profile_data:
                click.echo(click.style(
                    "⚠️  Warning: Target may not be a profile (missing 'author' or 'feed_cid' fields)",
                    fg="yellow"
                ))
                if not click.confirm("Continue anyway?"):
                    sys.exit(1)
            
            author = profile_data.get("author", cid[:12])
            pubkey = profile_data.get("pubkey", "")
            pubkey_preview = pubkey[:12] + "..."
            
            # ✅ COLLISION DETECTION: Check if display name already followed with different pubkey
            follow_list_path = layout.follow_list_path()
            existing_follows = []
            if follow_list_path.exists():
                follow_list = layout.load_json(follow_list_path)
                existing_follows = follow_list.get("follows", [])
            
            collision = detect_display_name_collision(
                display_name=author,
                pubkey=pubkey,
                existing_follows=existing_follows
            )
            
            if collision:
                click.echo(click.style(
                    f"⚠️  DISPLAY NAME COLLISION DETECTED",
                    fg="yellow",
                    bold=True
                ))
                click.echo(f"   You already follow '{collision['existing_user']}' with pubkey:")
                click.echo(f"     {collision['existing_pubkey_suffix']}")
                click.echo(f"   This profile '{author}' has DIFFERENT pubkey:")
                click.echo(f"     {collision['new_pubkey_suffix']}")
                click.echo()
                click.echo("💡 This is NOT an error – display names can collide in decentralized systems.")
                click.echo("   Identity is defined by pubkey, not display name.")
                if not click.confirm("Follow this user anyway?"):
                    sys.exit(1)
            
            click.echo(click.style(
                f"✅ Verified profile: {author} (pubkey: {pubkey_preview})",
                fg="green"
            ))
        else:
            # Force mode: skip resolution
            profile_data = None
            author = alias or cid[:12]
            pubkey = "unknown"
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
    
    # Check if already following (by pubkey, not display name!)
    if any(f.get("pubkey") == pubkey for f in follows):
        click.echo(click.style(
            f"⚠️  You already follow this user (same pubkey)",
            fg="yellow"
        ))
        sys.exit(0)
    
    # Add new follow
    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    follows.append({
        "user": alias or author,
        "profile_link": f"fx://{cid}",
        "profile_cid": cid,
        "pubkey": pubkey,
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
    
    # ✅ Show pubkey suffix if collision possible
    collision_suffix = ""
    if collision:
        collision_suffix = f" ({pubkey[:6]})"
    
    click.echo()
    click.echo(click.style(
        f"✅ Now following {display_name}{collision_suffix}",
        fg="green",
        bold=True
    ))
    click.echo(f"   Profile: fx://{cid}")
    click.echo(f"   Pubkey: {pubkey[:12]}...")
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
