"""Follow command – add users to your follow list by fx:// or ipns:// link with collision detection"""
import sys
import json
from datetime import datetime, timezone
import click

from filu_x.storage.layout import FiluXStorageLayout
from filu_x.core.resolver import LinkResolver, ResolutionError, SecurityError
from filu_x.core.ipfs_client import IPFSClient
from filu_x.core.crypto import sign_json
from filu_x.core.id_generator import detect_display_name_collision, normalize_display_name

@click.command()
@click.pass_context
@click.argument("target")
@click.option("--alias", "-a", help="Custom display name for this user")
@click.option("--force", is_flag=True, help="Skip signature verification (use with caution!)")
@click.option("--verbose", "-v", is_flag=True, help="Show detailed debug information")
def follow(ctx, target: str, alias: str = None, force: bool = False, verbose: bool = False):
    """
    Follow a user by fx:// profile link or ipns:// profile link.
    
    Detects display name collisions (same @name, different pubkey) and warns user.
    Identity is cryptographic (pubkey), not social (display name).
    
    For best results, share the IPNS link (ipns://...) as it never changes.
    
    Examples:
      filu-x follow fx://bafkreifcxj4fm3s...
      filu-x follow ipns://k51qzi5uqu55d72d...
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
    
    # 3. Check target is fx:// or ipns:// link
    if not (target.startswith("fx://") or target.startswith("ipns://")):
        click.echo(click.style(
            f"❌ Invalid target format. Expected fx:// or ipns:// link, got:\n"
            f"   {target}",
            fg="red"
        ))
        click.echo("\n💡 Tip: Get profile link with 'filu-x link --profile'")
        sys.exit(1)
    
    # 4. Initialize resolver and resolve profile
    ipfs = IPFSClient(mode="auto")
    resolver = LinkResolver(ipfs_client=ipfs)
    if verbose:
        resolver.set_verbose(True)
    
    try:
        # Parse link using parse_link method
        parsed = resolver.parse_link(target)
        protocol = parsed["protocol"]
        identifier = parsed["identifier"]
        
        if verbose:
            click.echo(click.style(f"   🔍 Protocol: {protocol}", fg="blue"))
            click.echo(click.style(f"   🔍 Identifier: {identifier[:16]}...", fg="blue"))
        
        # Determine the resource string to pass to resolve_content
        if protocol == "fx":
            resource = identifier  # just the CID
        else:  # ipns
            resource = target      # full ipns:// URI
        
        if not force:
            click.echo(click.style(f"🔍 Verifying profile signature...", fg="cyan"))
            
            # Resolve content using the correct resource string
            profile_data = resolver.resolve_content(resource, skip_cache=False)
            
            # Verify this is a profile (has required fields)
            if "author" not in profile_data or "pubkey" not in profile_data:
                click.echo(click.style(
                    "⚠️  Warning: Target may not be a profile (missing 'author' or 'pubkey' fields)",
                    fg="yellow"
                ))
                if not click.confirm("Continue anyway?"):
                    sys.exit(1)
            
            author = profile_data.get("author", identifier[:12])
            pubkey = profile_data.get("pubkey", "")
            pubkey_preview = pubkey[:12] + "..." if pubkey else "unknown"
            
            # ========== CRITICAL: Get IPNS names from profile ==========
            profile_ipns = profile_data.get("profile_ipns", "")
            manifest_ipns = profile_data.get("manifest_ipns", "")
            
            # Debug output to verify we got the IPNS names
            if verbose or True:  # Always show this for now
                if profile_ipns:
                    click.echo(click.style(f"   ✅ Found Profile IPNS: {profile_ipns[:16]}...", fg="green"))
                else:
                    click.echo(click.style(f"   ⚠️  No Profile IPNS found in profile", fg="yellow"))
                    
                if manifest_ipns:
                    click.echo(click.style(f"   ✅ Found Manifest IPNS: {manifest_ipns[:16]}...", fg="green"))
            # ===========================================================
            
            # ✅ COLLISION DETECTION
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
            author = alias or identifier[:12]
            pubkey = "unknown"
            profile_ipns = ""
            manifest_ipns = ""
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
            "version": "0.0.6",
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
    
    # ========== Save follow entry with ALL identifiers ==========
    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    
    follow_entry = {
        "user": alias or author,
        "profile_link": target,
        "profile_cid": identifier if protocol == "fx" else "",
        "profile_ipns": profile_ipns,
        "pubkey": pubkey,
        "manifest_ipns": manifest_ipns,
        "discovered_via": "manual",
        "discovered_at": now,
        "last_sync": now,
        "trust_score": 1.0
    }
    
    # Debug: show what we're saving
    if verbose or True:
        click.echo(click.style("\n📝 Saving follow entry:", fg="cyan"))
        click.echo(f"   • User: {follow_entry['user']}")
        click.echo(f"   • Profile IPNS: {follow_entry['profile_ipns'][:16] if follow_entry['profile_ipns'] else 'None'}")
        click.echo(f"   • Manifest IPNS: {follow_entry['manifest_ipns'][:16] if follow_entry['manifest_ipns'] else 'None'}")
    
    follows.append(follow_entry)
    follow_list["follows"] = follows
    follow_list["updated_at"] = now
    
    # Sign new list
    follow_list["signature"] = sign_json(follow_list, privkey_bytes)
    
    # Save
    layout.save_json(follow_list_path, follow_list, private=False)
    
    # ========== OPTIONAL: Cache profile immediately ==========
    # KORJATTU: Käytä layout-metodia
    if profile_data:
        try:
            cached_dir = layout.cached_user_dir(author, protocol="ipfs")
            cached_dir.mkdir(parents=True, exist_ok=True)
            
            profile_path = cached_dir / "profile.json"
            profile_path.write_text(json.dumps(profile_data, indent=2, ensure_ascii=False))
            
            if manifest_ipns:
                ipns_path = cached_dir / "manifest_ipns.txt"
                ipns_path.write_text(manifest_ipns)
            
            if profile_ipns:
                profile_ipns_path = cached_dir / "profile_ipns.txt"
                profile_ipns_path.write_text(profile_ipns)
                
            click.echo(click.style(f"   📦 Profile cached immediately", fg="green"))
        except Exception as e:
            if verbose:
                click.echo(click.style(f"   ⚠️  Could not cache profile: {e}", fg="yellow"))
    # =========================================================
    
    # 6. Show result
    display_name = alias or author
    
    # Show pubkey suffix if collision possible
    collision_suffix = ""
    if collision:
        collision_suffix = f" ({pubkey[:6]})"
    
    click.echo()
    click.echo(click.style(
        f"✅ Now following {display_name}{collision_suffix}",
        fg="green",
        bold=True
    ))
    click.echo(f"   Profile: {target}")
    if pubkey:
        click.echo(f"   Pubkey: {pubkey[:12]}...")
    
    if profile_ipns:
        click.echo(f"   📌 Profile IPNS: {profile_ipns}")
    if manifest_ipns:
        click.echo(f"   📌 Manifest IPNS: {manifest_ipns[:16]}...")
    
    click.echo(f"   Posts: will appear in feed after sync")
    
    # Suggest next steps
    click.echo()
    click.echo(click.style("💡 Next steps:", fg="blue"))
    click.echo("   • See your feed:        filu-x feed")
    click.echo("   • Sync for new posts:   filu-x sync")
    click.echo("   • Sync followed users:  filu-x sync-followed")
    click.echo("   • List follows:         filu-x ls --follows")
    
    if profile_ipns:
        click.echo()
        click.echo(click.style(
            "✅ This user has a Profile IPNS. For automatic updates,",
            fg="green"
        ))
        click.echo("   the IPNS link is saved in your follow list.")
        click.echo(f"   ipns://{profile_ipns}")
