"""Sync command – sync files to IPFS and update manifest with IPFS CIDs, then publish to IPNS"""
import sys
import json
from pathlib import Path
from datetime import datetime, timezone
import click

from filu_x.storage.layout import FiluXStorageLayout
from filu_x.core.ipfs_client import IPFSClient
from filu_x.core.crypto import sign_json
from filu_x.core.ipns import IPNSManager

def increment_version(version_str):
    """Increment version number (major.minor.patch.build)"""
    try:
        parts = version_str.split('.')
        if len(parts) != 4:
            return "0.0.0.1"
        major, minor, patch, build = map(int, parts)
        build += 1
        if build > 9999:
            build = 0
            patch += 1
            if patch > 9999:
                patch = 0
                minor += 1
                if minor > 9999:
                    minor = 0
                    major += 1
        return f"{major}.{minor}.{patch}.{build}"
    except:
        return "0.0.0.1"

@click.command()
@click.pass_context
@click.option("--dry-run", is_flag=True, help="Show what would be synced, don't make changes")
@click.option("--verbose", "-v", is_flag=True, help="Show detailed output")
@click.option("--force-mock", is_flag=True, help="Force mock IPFS mode")
def sync(ctx, dry_run: bool, verbose: bool, force_mock: bool):
    """
    Sync local files to IPFS and update manifest with IPFS CIDs.
    
    Process:
    1. Add all posts to IPFS → get IPFS CIDs
    2. Update manifest with these IPFS CIDs
    3. Add updated manifest to IPFS
    4. Publish new manifest CID to IPNS
    5. Update profile (optional, for backward compatibility)
    """
    data_dir = ctx.obj.get("data_dir")
    layout = FiluXStorageLayout(base_path=data_dir)
    
    if not layout.profile_path().exists():
        click.echo(click.style("❌ User not initialized. Run: filu-x init <username>", fg="red"))
        sys.exit(1)
    
    mode = "mock" if force_mock else "auto"
    try:
        ipfs = IPFSClient(mode=mode)
        ipns = IPNSManager(use_mock=True)
    except Exception as e:
        click.echo(click.style(f"❌ IPFS error: {e}", fg="red"))
        sys.exit(1)
    
    mode_str = "real IPFS" if ipfs.use_real else "mock IPFS"
    click.echo(click.style(f"🔄 Syncing files to {mode_str}...", fg="cyan", bold=True))
    
    synced = []
    errors = []
    post_cids = {}  # Map filename -> IPFS CID
    
    def add_file(name: str, path: Path, is_post: bool = False):
        """Add file to IPFS and track its CID"""
        try:
            if path.exists():
                cid = "DRYRUN_CID" if dry_run else ipfs.add_file(path)
                synced.append((name, cid))
                if verbose:
                    status = "✅" if not dry_run else "📄"
                    click.echo(f"   {status} {name} → {cid[:16]}...")
                return cid
        except Exception as e:
            errors.append((name, str(e)))
        return None
    
    # ========== STEP 1: Add all posts to IPFS ==========
    posts_dir = layout.public_ipfs_dir / "posts"
    if posts_dir.exists():
        for post_path in sorted(posts_dir.glob("*.json")):
            cid = add_file(post_path.name, post_path)
            if cid:
                post_cids[post_path.name] = cid
                if verbose:
                    click.echo(f"   📦 Post {post_path.name} → IPFS CID: {cid[:16]}...")
    
    # ========== STEP 2: Update manifest with IPFS CIDs ==========
    manifest_path = layout.manifest_path(protocol="ipfs")
    manifest_updated = False
    
    if manifest_path.exists() and not dry_run:
        try:
            # Load current manifest
            manifest = layout.load_json(manifest_path)
            old_version = manifest.get("manifest_version", "0.0.0.0")
            
            if verbose:
                entries_before = len(manifest.get("entries", []))
                click.echo(f"   📊 Manifest before update: {entries_before} entries, version {old_version}")
            
            # Update each post entry with its IPFS CID
            for entry in manifest.get("entries", []):
                post_filename = entry.get("path", "").split("/")[-1]
                if post_filename in post_cids:
                    old_cid = entry.get("cid")
                    new_cid = post_cids[post_filename]
                    if old_cid != new_cid:
                        entry["cid"] = new_cid
                        manifest_updated = True
                        if verbose:
                            click.echo(f"   🔄 Manifest entry updated: {old_cid[:16]}... → {new_cid[:16]}...")
            
            if manifest_updated:
                # Increment version
                new_version = increment_version(old_version)
                manifest["manifest_version"] = new_version
                
                # Re-sign manifest
                with open(layout.private_key_path(), "rb") as f:
                    privkey = f.read()
                manifest["signature"] = sign_json(manifest, privkey)
                
                # Save updated manifest locally
                layout.save_json(manifest_path, manifest, private=False)
                
                if verbose:
                    entries_after = len(manifest.get("entries", []))
                    click.echo(f"   📝 Manifest updated: {entries_after} entries, version {old_version} → {new_version}")
            else:
                if verbose:
                    click.echo(f"   ℹ️  No manifest updates needed")
                    
        except Exception as e:
            errors.append(("manifest_update", str(e)))
    
    # ========== STEP 3: Add updated manifest to IPFS ==========
    manifest_cid = None
    if manifest_path.exists():
        manifest_cid = add_file("Filu-X.json", manifest_path)
    
    # ========== STEP 4: Add profile and follow list to IPFS ==========
    profile_cid = add_file("profile.json", layout.profile_path(protocol="ipfs"))
    add_file("follow_list.json", layout.follow_list_path(protocol="ipfs"))
    
    # ========== STEP 5: Publish manifest to IPNS ==========
    if manifest_cid and not dry_run:
        try:
            profile = layout.load_json(layout.profile_path(protocol="ipfs"))
            manifest_ipns = profile.get("manifest_ipns")
            if manifest_ipns:
                ipns.publish(layout.manifest_path(protocol="ipfs"), manifest_ipns)
                if verbose:
                    click.echo(click.style(f"   📌 Manifest IPNS updated to {manifest_cid[:16]}...", fg="green"))
        except Exception as e:
            errors.append(("ipns_publish", str(e)))
    
    # ========== STEP 6: Update profile (optional) ==========
    if manifest_cid and not dry_run and manifest_updated:
        try:
            profile = layout.load_json(layout.profile_path(protocol="ipfs"))
            old_manifest_cid = profile.get("manifest_cid")
            
            # Update profile's manifest_cid (for backward compatibility)
            profile["manifest_cid"] = manifest_cid
            profile["updated_at"] = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
            
            with open(layout.private_key_path(), "rb") as f:
                privkey = f.read()
            profile["signature"] = sign_json(profile, privkey)
            
            # Save updated profile locally
            layout.save_json(layout.profile_path(protocol="ipfs"), profile, private=False)
            
            # Add updated profile to IPFS
            new_profile_cid = ipfs.add_file(layout.profile_path(protocol="ipfs"))
            
            if verbose:
                click.echo(click.style(f"   📢 Profile manifest_cid updated: {old_manifest_cid[:16] if old_manifest_cid else 'None'}... → {manifest_cid[:16]}...", fg="green"))
                click.echo(f"   📦 Profile re-synced: {new_profile_cid[:16]}...")
                
        except Exception as e:
            errors.append(("profile_update", str(e)))
    
    # ========== SUMMARY ==========
    click.echo()
    status = "DRY RUN" if dry_run else "COMPLETED"
    click.echo(click.style(f"📊 Sync {status} ({mode_str})", fg="green", bold=True))
    click.echo(f"   Files synced: {len(synced)}")
    click.echo(f"   Posts: {len(post_cids)}")
    if manifest_updated:
        click.echo(f"   Manifest updated: Yes (new version)")
    else:
        click.echo(f"   Manifest updated: No")
    
    if profile_cid and not dry_run:
        gateway_url = ipfs.get_gateway_url(profile_cid)
        click.echo()
        click.echo(click.style("🔗 Your profile link:", fg="blue", bold=True))
        click.echo(f"   fx://{profile_cid}")
        click.echo(f"   {gateway_url}")
    
    if errors:
        click.echo()
        click.echo(click.style(f"⚠️  Errors ({len(errors)}):", fg="yellow"))
        for name, err in errors[:3]:
            click.echo(f"   • {name}: {err}")
    
    if dry_run:
        click.echo()
        click.echo(click.style("ℹ️  This was a dry run – nothing was uploaded.", fg="blue"))
