# src/filu_x/cli/commands/sync.py
"""Sync command – sync files to IPFS (real or mock)"""
import sys
import json
from pathlib import Path
import click

from filu_x.storage.layout import FiluXStorageLayout
from filu_x.core.ipfs_client import IPFSClient

@click.command()
@click.option("--dry-run", is_flag=True, help="Show what would be synced, don't make changes")
@click.option("--verbose", "-v", is_flag=True, help="Show detailed output")
@click.option("--force-mock", is_flag=True, help="Force mock IPFS mode")
def sync(dry_run: bool, verbose: bool, force_mock: bool):
    """
    Sync local files to IPFS (real or mock).
    
    Automatically uses real IPFS daemon if available at http://127.0.0.1:5001.
    Falls back to mock mode if daemon is not running.
    """
    layout = FiluXStorageLayout()
    
    if not layout.profile_path().exists():
        click.echo(click.style(
            "❌ User not initialized. Run: filu-x init <username>",
            fg="red"
        ))
        sys.exit(1)
    
    # Initialize IPFS client
    mode = "mock" if force_mock else "auto"
    try:
        ipfs = IPFSClient(mode=mode)
    except Exception as e:
        click.echo(click.style(f"❌ IPFS error: {e}", fg="red"))
        sys.exit(1)
    
    mode_str = "real IPFS" if ipfs.use_real else "mock IPFS"
    click.echo(click.style(
        f"🔄 Syncing files to {mode_str}...",
        fg="cyan",
        bold=True
    ))
    
    synced = []
    errors = []
    
    def add_file(name: str, path: Path):
        try:
            if path.exists():
                cid = "DRYRUN_CID" if dry_run else ipfs.add_file(path)
                synced.append((name, cid))
                if verbose:
                    status = "✅" if not dry_run else "📄"
                    click.echo(f"   {status} {name} → {cid}")
        except Exception as e:
            errors.append((name, str(e)))
    
    # Sync core files
    add_file("profile.json", layout.profile_path())
    add_file("Filu-X.json", layout.manifest_path())
    add_file("follow_list.json", layout.follow_list_path())
    
    # Sync posts
    post_count = 0
    if layout.posts_dir.exists():
        for post_path in sorted(layout.posts_dir.glob("*.json")):
            try:
                cid = "DRYRUN_CID" if dry_run else ipfs.add_file(post_path)
                synced.append((post_path.name, cid))
                post_count += 1
                if verbose:
                    status = "✅" if not dry_run else "📄"
                    click.echo(f"   {status} {post_path.name} → {cid}")
            except Exception as e:
                errors.append((post_path.name, str(e)))
    
    # Update manifest with real CIDs (if real IPFS)
    if not dry_run and ipfs.use_real:
        try:
            manifest = layout.load_json(layout.manifest_path())
            for i, entry in enumerate(manifest.get("entries", [])):
                if entry["type"] == "post":
                    post_path = layout.posts_dir / entry["path"].split("/")[-1]
                    if post_path.exists():
                        cid = ipfs.add_file(post_path)
                        manifest["entries"][i]["cid"] = cid
            # Re-sign manifest
            from filu_x.core.crypto import sign_json
            with open(layout.private_key_path(), "rb") as f:
                privkey = f.read()
            manifest["signature"] = sign_json(manifest, privkey)
            layout.save_json(layout.manifest_path(), manifest, private=False)
        except Exception as e:
            click.echo(click.style(f"⚠️  Failed to update manifest CIDs: {e}", fg="yellow"))
    
    # Summary
    click.echo()
    status = "DRY RUN" if dry_run else "COMPLETED"
    click.echo(click.style(
        f"📊 Sync {status} ({mode_str})",
        fg="green",
        bold=True
    ))
    click.echo(f"   Files synced: {len(synced)}")
    click.echo(f"   Posts: {post_count}")
    
    # Show profile link
    if synced and not dry_run:
        profile_cid = next((cid for name, cid in synced if name == "profile.json"), None)
        if profile_cid:
            gateway_url = ipfs.get_gateway_url(profile_cid)
            click.echo()
            click.echo(click.style("🔗 Your profile link:", fg="blue", bold=True))
            click.echo(f"   fx://{profile_cid}")
            click.echo(f"   {gateway_url}")
            click.echo()
            click.echo(click.style("💡 Share this link anywhere!", fg="blue"))
    
    # Show errors if any
    if errors:
        click.echo()
        click.echo(click.style(f"⚠️  Errors ({len(errors)}):", fg="yellow"))
        for name, err in errors[:3]:
            click.echo(f"   • {name}: {err}")
        if len(errors) > 3:
            click.echo(f"   ... and {len(errors) - 3} more")
    
    if dry_run:
        click.echo()
        click.echo(click.style("ℹ️  This was a dry run – nothing was uploaded.", fg="blue"))
        click.echo("   Remove --dry-run to actually sync to IPFS.")
