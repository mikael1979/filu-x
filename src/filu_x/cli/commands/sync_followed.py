"""Sync followed users' latest posts via IPNS and update thread manifests"""
import sys
import json
import re
from pathlib import Path
from datetime import datetime, timezone
import time
import click

from filu_x.storage.layout import FiluXStorageLayout
from filu_x.core.resolver import LinkResolver, ResolutionError, SecurityError
from filu_x.core.ipfs_client import IPFSClient
from filu_x.cli.commands.thread import ThreadManifest  # UUSI

def is_deterministic_id(cid: str) -> bool:
    """Check if string is a 32-char hex deterministic ID"""
    return len(cid) == 32 and re.match(r'^[0-9a-fA-F]{32}$', cid) is not None

def is_ipfs_cid(cid: str) -> bool:
    """Check if string is an IPFS CID (starts with bafk or Qm)"""
    return cid.startswith("bafk") or cid.startswith("Qm")

@click.command()
@click.pass_context
@click.option("--limit", "-l", default=10, help="Max posts per followed user")
@click.option("--verbose", "-v", is_flag=True, help="Show detailed sync progress")
@click.option("--allow-unverified", is_flag=True, help="Accept manifests without signature verification")
@click.option("--wait", "-w", default=0, help="Wait N seconds after sync (for IPNS propagation)")
@click.option("--threads", is_flag=True, help="Also fetch thread manifests for posts")
def sync_followed(ctx, limit: int, verbose: bool, allow_unverified: bool, wait: int, threads: bool):
    """
    Sync latest posts from followed users via IPNS.
    
    Fetches profiles once, then uses manifest IPNS to always get the latest manifest.
    Also fetches thread manifests for posts if --threads flag is used.
    """
    data_dir = ctx.obj.get("data_dir")
    layout = FiluXStorageLayout(base_path=data_dir)
    
    if not layout.profile_path().exists():
        click.echo(click.style("❌ User not initialized. Run: filu-x init <username>", fg="red"))
        sys.exit(1)
    
    follow_list_path = layout.follow_list_path()
    if not follow_list_path.exists():
        click.echo(click.style("📭 No followed users. Follow someone first.", fg="yellow"))
        sys.exit(0)
    
    follow_list = layout.load_json(follow_list_path)
    follows = follow_list.get("follows", [])
    
    if not follows:
        click.echo(click.style("📭 No followed users", fg="yellow"))
        sys.exit(0)
    
    ipfs = IPFSClient(mode="auto")
    resolver = LinkResolver(ipfs_client=ipfs)
    if verbose:
        resolver.set_verbose(True)
    
    total_new = 0
    total_threads = 0
    errors = []
    verified_ok = 0
    ipns_resolved = 0
    
    click.echo(click.style(f"🔄 Syncing {len(follows)} followed users via IPNS...", fg="cyan", bold=True))
    
    for follow in follows:
        user = follow.get("user", "unknown")
        expected_pubkey = follow.get("pubkey")
        
        if verbose:
            click.echo(f"\n👤 Syncing {user}...")
        
        try:
            # ========== DETERMINE PROFILE IDENTIFIER ==========
            profile_ipns = follow.get("profile_ipns")
            profile_cid = follow.get("profile_cid")
            profile_identifier = None
            identifier_type = None
            
            if profile_cid:
                profile_identifier = profile_cid
                identifier_type = "Profile CID"
                if verbose:
                    click.echo(f"   🔍 Using Profile CID: {profile_identifier[:16]}...")
            elif profile_ipns:
                profile_identifier = f"ipns://{profile_ipns}"
                identifier_type = "Profile IPNS"
                if verbose:
                    click.echo(f"   🔍 Using Profile IPNS: {profile_ipns[:16]}...")
            elif follow.get("profile_link"):
                parsed = resolver.parse_link(follow["profile_link"])
                profile_identifier = parsed["identifier"]
                identifier_type = f"Parsed {parsed['protocol']}"
            else:
                raise ResolutionError(f"No valid profile identifier for {user}")
            
            # ========== FETCH FRESH PROFILE ==========
            if verbose:
                click.echo(f"   📥 Fetching fresh profile using {identifier_type}...")
            
            profile_data = resolver.resolve_content(profile_identifier, skip_cache=True)
            
            # Verify pubkey
            profile_pubkey = profile_data.get("pubkey")
            if expected_pubkey and profile_pubkey != expected_pubkey:
                click.echo(click.style(f"   ⚠️  Pubkey mismatch!", fg="yellow"))
                if not click.confirm("Continue?"):
                    continue
            
            # ========== GET MANIFEST VIA IPNS ==========
            manifest_ipns = profile_data.get("manifest_ipns")
            if not manifest_ipns:
                click.echo(click.style(f"   ❌ No manifest_ipns in profile", fg="red"))
                continue
            
            if verbose:
                click.echo(f"   🔍 Resolving Manifest IPNS: {manifest_ipns[:16]}...")
            
            # Resolve IPNS to get the latest manifest CID
            manifest_data = None
            try:
                manifest_data = resolver.resolve_content(
                    f"ipns://{manifest_ipns}",
                    skip_cache=True,
                    expected_pubkey=profile_pubkey if not allow_unverified else None
                )
                ipns_resolved += 1
                if verbose:
                    click.echo(f"   ✅ Manifest fetched via IPNS")
                    
            except (ResolutionError, SecurityError) as e:
                if wait > 0:
                    if verbose:
                        click.echo(f"   ⚠️  IPNS resolution failed: {e}")
                        click.echo(f"   ⏳ Waiting {wait} seconds for IPNS propagation...")
                    time.sleep(wait)
                    
                    try:
                        manifest_data = resolver.resolve_content(
                            f"ipns://{manifest_ipns}",
                            skip_cache=True,
                            expected_pubkey=profile_pubkey if not allow_unverified else None
                        )
                        ipns_resolved += 1
                        if verbose:
                            click.echo(f"   ✅ Manifest fetched via IPNS after waiting")
                    except Exception as e2:
                        click.echo(click.style(f"   ❌ Still failed after waiting: {e2}", fg="red"))
                        continue
                else:
                    click.echo(click.style(f"   ❌ Failed to resolve manifest IPNS: {e}", fg="red"))
                    continue
            
            if not manifest_data:
                continue
                
            verified_ok += 1
            current_author = profile_data.get("author", user)
            manifest_cid = manifest_data.get("_resolved_cid", "unknown")
            
            if verbose:
                entries = manifest_data.get("entries", [])
                click.echo(f"   📊 Manifest version: {manifest_data.get('manifest_version', '0.0.0.0')}, posts in manifest: {len(entries)}")
                if len(entries) == 0 and verbose:
                    click.echo(f"   ⚠️  WARNING: Manifest has 0 entries!")
            
            # ========== CACHE MANIFEST ==========
            cached_dir = layout.cached_user_dir(current_author, protocol="ipfs")
            cached_dir.mkdir(parents=True, exist_ok=True)
            
            manifest_path = cached_dir / "Filu-X.json"
            manifest_path.write_text(json.dumps(manifest_data, indent=2, ensure_ascii=False))
            
            profile_path = cached_dir / "profile.json"
            profile_path.write_text(json.dumps(profile_data, indent=2, ensure_ascii=False))
            
            ipns_path = cached_dir / "manifest_ipns.txt"
            ipns_path.write_text(manifest_ipns)
            
            if profile_ipns:
                profile_ipns_path = cached_dir / "profile_ipns.txt"
                profile_ipns_path.write_text(profile_ipns)
            
            last_sync_path = cached_dir / "last_sync.txt"
            last_sync_path.write_text(datetime.now(timezone.utc).isoformat())
            
            # ========== PROCESS POSTS ==========
            posts = [e for e in manifest_data.get("entries", []) 
                    if e.get("type") in ["post", "repost", "vote", "reaction", "rating"]]
            
            posts.reverse()  # Newest first
            
            posts_dir = cached_dir / "posts"
            posts_dir.mkdir(parents=True, exist_ok=True)
            
            # Get list of already cached posts
            cached_posts = set()
            thread_ids_seen = set()  # Track threads we've processed
            if posts_dir.exists():
                for f in posts_dir.glob("*.json"):
                    cached_posts.add(f.stem)
                    # Also try to read thread_id from cached post
                    try:
                        with open(f, 'r') as pf:
                            post_data = json.load(pf)
                            if post_data.get("thread_id"):
                                thread_ids_seen.add(post_data["thread_id"])
                    except:
                        pass
            
            if verbose:
                click.echo(f"   📦 Already cached: {len(cached_posts)} posts, {len(thread_ids_seen)} threads")
            
            new_count = 0
            total_posts = len(posts)
            thread_posts_to_fetch = {}  # thread_id -> list of post data
            
            for idx, post_entry in enumerate(posts[:limit]):
                post_cid = post_entry.get("cid")
                if not post_cid:
                    continue
                
                # Detect format
                ipfs_cid = is_ipfs_cid(post_cid)
                det_id = is_deterministic_id(post_cid)
                
                if verbose:
                    if idx < 3 or idx == total_posts - 1:
                        if ipfs_cid:
                            click.echo(f"   🔍 [{idx+1}/{total_posts}] IPFS CID: {post_cid[:16]}...")
                        elif det_id:
                            click.echo(f"   🔍 [{idx+1}/{total_posts}] Deterministic ID: {post_cid[:16]}...")
                        else:
                            click.echo(f"   ⚠️  [{idx+1}/{total_posts}] Unknown format: {post_cid[:16]}...")
                    elif idx == 3:
                        click.echo(f"   ... and {total_posts - 4} more posts")
                
                if not (ipfs_cid or det_id):
                    continue
                
                if post_cid in cached_posts:
                    if verbose and (idx < 3 or idx == total_posts - 1):
                        click.echo(f"   ℹ️  Already cached: {post_cid[:16]}...")
                    continue
                
                # For deterministic IDs, we need to check if they're in IPFS
                if det_id:
                    if verbose:
                        click.echo(f"   ⚠️  Note: {post_cid[:16]}... is a local ID - ask {current_author} to run 'filu-x sync'")
                    
                    # Try to resolve as IPFS CID (might work if synced)
                    try:
                        post_content = resolver.resolve_content(post_cid, skip_cache=False)
                        post_path = posts_dir / f"{post_cid}.json"
                        post_path.write_text(json.dumps(post_content, indent=2, ensure_ascii=False))
                        new_count += 1
                        total_new += 1
                        cached_posts.add(post_cid)
                        
                        # Store for thread manifest processing
                        if threads and post_content.get("thread_id"):
                            thread_id = post_content["thread_id"]
                            if thread_id not in thread_posts_to_fetch:
                                thread_posts_to_fetch[thread_id] = []
                            thread_posts_to_fetch[thread_id].append(post_content)
                        
                        if verbose:
                            preview = post_content.get("content", "")[:40]
                            if preview:
                                preview += "..."
                            click.echo(f"   ✅ Cached: {preview}")
                    except Exception:
                        # Expected - deterministic IDs need sync first
                        continue
                
                elif ipfs_cid:
                    try:
                        post_content = resolver.resolve_content(post_cid, skip_cache=False)
                        post_path = posts_dir / f"{post_cid}.json"
                        post_path.write_text(json.dumps(post_content, indent=2, ensure_ascii=False))
                        new_count += 1
                        total_new += 1
                        cached_posts.add(post_cid)
                        
                        # Store for thread manifest processing
                        if threads and post_content.get("thread_id"):
                            thread_id = post_content["thread_id"]
                            if thread_id not in thread_posts_to_fetch:
                                thread_posts_to_fetch[thread_id] = []
                            thread_posts_to_fetch[thread_id].append(post_content)
                        
                        if verbose:
                            preview = post_content.get("content", "")[:40]
                            if preview:
                                preview += "..."
                            click.echo(f"   ✅ Cached: {preview}")
                            
                    except Exception as e:
                        if verbose:
                            click.echo(f"   ⚠️  Failed to fetch: {e}")
            
            # ========== PROCESS THREAD MANIFESTS ==========
            if threads and thread_posts_to_fetch:
                if verbose:
                    click.echo(f"   📋 Processing {len(thread_posts_to_fetch)} thread manifests...")
                
                for thread_id, thread_posts in thread_posts_to_fetch.items():
                    try:
                        # Get or create thread manifest
                        thread_manifest = ThreadManifest(layout, thread_id)
                        
                        # Add all posts to thread manifest
                        for post_content in thread_posts:
                            thread_manifest.add_post(post_content)
                        
                        if verbose:
                            click.echo(f"      ✅ Thread {thread_id[:16]}... now has {thread_manifest.data['post_count']} posts")
                        
                        total_threads += 1
                        
                    except Exception as e:
                        if verbose:
                            click.echo(f"      ⚠️  Could not update thread manifest {thread_id[:16]}...: {e}")
            
            # Update follow list
            follow["last_sync"] = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
            follow["last_manifest_version"] = manifest_data.get("manifest_version", "0.0.0.0")
            follow["last_manifest_cid"] = manifest_cid
            
            if verbose:
                if new_count == 0:
                    if len(posts) > 0:
                        click.echo(f"   ℹ️  No new posts (already have {len(cached_posts)}/{len(posts)})")
                    else:
                        click.echo(f"   ℹ️  No posts in manifest")
                else:
                    click.echo(f"   ✅ Synced {new_count} new posts (total {len(cached_posts)}/{len(posts)})")
        
        except Exception as e:
            errors.append((user, str(e)))
            if verbose:
                click.echo(f"   ❌ {e}")
    
    # Update follow list
    follow_list["follows"] = follows
    follow_list["updated_at"] = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    
    try:
        with open(layout.private_key_path(), "rb") as f:
            privkey_bytes = f.read()
        from filu_x.core.crypto import sign_json
        follow_list["signature"] = sign_json(follow_list, privkey_bytes)
        layout.save_json(follow_list_path, follow_list, private=False)
    except Exception as e:
        if verbose:
            click.echo(click.style(f"⚠️  Could not update follow list: {e}", fg="yellow"))
    
    # Summary
    click.echo()
    click.echo(click.style(f"📊 Sync completed", fg="green", bold=True))
    click.echo(f"   New posts cached: {total_new}")
    click.echo(f"   Followed users: {len(follows)}")
    click.echo(f"   Manifests verified: {verified_ok}")
    if threads:
        click.echo(f"   Threads updated: {total_threads}")
    if ipns_resolved > 0:
        click.echo(f"   IPNS resolutions: {ipns_resolved}")
    
    if errors:
        click.echo(click.style(f"\n⚠️  Errors ({len(errors)}):", fg="yellow"))
        for user, err in errors[:3]:
            click.echo(f"   • {user}: {err}")
    
    click.echo()
    click.echo(click.style("💡 View your unified feed:", fg="blue"))
    click.echo("   filu-x feed")
    
    if threads:
        click.echo(click.style("💡 View your threads:", fg="blue"))
        click.echo("   filu-x thread list")
    
    if wait > 0:
        click.echo()
        click.echo(click.style(f"⏳ Note: Used --wait {wait} seconds for IPNS propagation", fg="cyan"))
