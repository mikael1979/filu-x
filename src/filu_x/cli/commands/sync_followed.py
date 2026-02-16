"""Sync followed users' latest posts into local cache"""
import sys
import json
from pathlib import Path
import click

from filu_x.storage.layout import FiluXStorageLayout
from filu_x.core.resolver import LinkResolver, ResolutionError
from filu_x.core.ipfs_client import IPFSClient

@click.command()
@click.pass_context
@click.option("--limit", "-l", default=10, help="Max posts per followed user")
@click.option("--verbose", "-v", is_flag=True, help="Show detailed sync progress")
def sync_followed(ctx, limit: int, verbose: bool):
    """
    Sync latest posts from followed users into local cache.
    
    Fetches profile manifests from IPFS, resolves new posts,
    and stores them in ~/.local/share/filu-x/data/cached/follows/
    
    Example:
      filu-x sync-followed --limit 5
    """
    data_dir = ctx.obj.get("data_dir")
    layout = FiluXStorageLayout(base_path=data_dir)
    
    # Verify user is initialized
    if not layout.profile_path().exists():
        click.echo(click.style(
            "❌ User not initialized. Run: filu-x init <username>",
            fg="red"
        ))
        sys.exit(1)
    
    # Load follow list
    follow_list_path = layout.follow_list_path()
    if not follow_list_path.exists():
        click.echo(click.style(
            "📭 No followed users. Follow someone first:\n"
            "   filu-x follow fx://bafkrei...",
            fg="yellow"
        ))
        sys.exit(0)
    
    follow_list = layout.load_json(follow_list_path)
    follows = follow_list.get("follows", [])
    
    if not follows:
        click.echo(click.style("📭 No followed users", fg="yellow"))
        sys.exit(0)
    
    # Initialize resolver
    ipfs = IPFSClient(mode="auto")
    resolver = LinkResolver(ipfs_client=ipfs)
    
    # Sync each followed user
    total_new = 0
    errors = []
    
    click.echo(click.style(
        f"🔄 Syncing {len(follows)} followed users...",
        fg="cyan",
        bold=True
    ))
    
    for follow in follows:
        user = follow.get("user", follow.get("profile_cid", "unknown"))
        profile_link = follow.get("profile_link", "")
        cid = follow.get("profile_cid", "")
        
        if verbose:
            click.echo(f"\n👤 Syncing {user}...")
        
        try:
            # Resolve profile if CID missing or invalid
            if not cid.startswith("bafk") and not cid.startswith("Qm"):
                parsed = resolver.parse_fx_link(profile_link)
                cid = parsed["cid"]
            
            profile_data = resolver.resolve_content(cid, skip_cache=False)
            
            # Get manifest CID from profile
            manifest_cid = profile_data.get("feed_cid")
            if not manifest_cid:
                if verbose:
                    click.echo(f"   ⚠️  No manifest CID in profile")
                continue
            
            # Resolve manifest
            manifest = resolver.resolve_content(manifest_cid, skip_cache=False)
            posts = [e for e in manifest.get("entries", []) if e.get("type") == "post"]
            
            # Reverse to get newest first
            posts.reverse()
            
            # Save to cached directory
            cached_dir = layout.base_path / "data" / "cached" / "follows" / user.replace("@", "").replace(" ", "_")
            cached_dir.mkdir(parents=True, exist_ok=True)
            
            # Save profile and manifest
            (cached_dir / "profile.json").write_text(json.dumps(profile_data, indent=2, ensure_ascii=False))
            (cached_dir / "Filu-X.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False))
            
            # Save posts (max limit)
            new_count = 0
            for post_entry in posts[:limit]:
                post_cid = post_entry.get("cid")
                if not post_cid:
                    continue
                
                # ✅ SKIP non-CID values (post IDs like "20260214_...")
                # Real CIDs always start with "bafk" (CIDv1) or "Qm" (CIDv0)
                if not (post_cid.startswith("bafk") or post_cid.startswith("Qm")):
                    if verbose:
                        preview = post_cid[:30] + "..." if len(post_cid) > 30 else post_cid
                        click.echo(f"   ⚠️  Skipping non-CID entry: {preview}")
                    continue
                
                # Skip if already cached
                post_path = cached_dir / "posts" / f"{post_cid}.json"
                post_path.parent.mkdir(parents=True, exist_ok=True)
                
                if post_path.exists():
                    continue
                
                # Resolve and save post
                try:
                    post_content = resolver.resolve_content(post_cid, skip_cache=False)
                    post_path.write_text(json.dumps(post_content, indent=2, ensure_ascii=False))
                    new_count += 1
                    total_new += 1
                    
                    if verbose:
                        content_preview = post_content.get("content", "")[:40]
                        preview = content_preview + "..." if len(content_preview) > 40 else content_preview
                        click.echo(f"   ✅ Cached: {preview}")
                except ResolutionError as e:
                    if verbose:
                        click.echo(f"   ⚠️  Failed to resolve {post_cid[:12]}: {e}")
                    continue
                except Exception as e:
                    if verbose:
                        click.echo(f"   ⚠️  Error caching {post_cid[:12]}: {e}")
                    continue
            
            if verbose and new_count == 0:
                click.echo(f"   ℹ️  No new posts")
        
        except ResolutionError as e:
            errors.append((user, f"Resolution failed: {e}"))
            if verbose:
                click.echo(f"   ❌ {e}")
        except Exception as e:
            errors.append((user, str(e)))
            if verbose:
                click.echo(f"   ❌ {e}")
    
    # Show summary
    click.echo()
    click.echo(click.style(
        f"📊 Sync completed",
        fg="green",
        bold=True
    ))
    click.echo(f"   New posts cached: {total_new}")
    click.echo(f"   Followed users: {len(follows)}")
    
    if errors:
        click.echo(click.style(f"\n⚠️  Errors ({len(errors)}):", fg="yellow"))
        for user, err in errors[:3]:
            click.echo(f"   • {user}: {err}")
        if len(errors) > 3:
            click.echo(f"   ... and {len(errors) - 3} more")
    
    click.echo()
    click.echo(click.style("💡 View your unified feed:", fg="blue"))
    click.echo("   filu-x feed")
