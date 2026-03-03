"""Resolve and display Filu-X content from fx://, ipns://, or http:// links"""
import sys
import click
from datetime import datetime

from filu_x.storage.layout import FiluXStorageLayout
from filu_x.core.resolver import LinkResolver, ResolutionError, SecurityError
from filu_x.core.ipfs_client import IPFSClient

@click.command()
@click.pass_context
@click.argument("link")
@click.option("--raw", is_flag=True, help="Show raw JSON instead of formatted content")
@click.option("--no-cache", is_flag=True, help="Skip cache and fetch fresh from source")
@click.option("--verbose", "-v", is_flag=True, help="Show detailed verification info")
@click.option("--allow-unverified", is_flag=True, help="Skip signature verification (for testing)")
def resolve(ctx, link: str, raw: bool, no_cache: bool, verbose: bool, allow_unverified: bool):
    """
    Resolve and display Filu-X content from fx://, ipns://, or http:// link.
    
    Verifies cryptographic signature before showing content unless --allow-unverified is used.
    
    Examples:
      filu-x resolve fx://bafkrei...
      filu-x resolve ipns://k51qzi5uqu5...
      filu-x resolve http://127.0.0.1:8888/profile.json --allow-unverified
    """
    data_dir = ctx.obj.get("data_dir")
    layout = FiluXStorageLayout(base_path=data_dir)
    
    # Initialize resolver
    ipfs = IPFSClient(mode="auto")
    resolver = LinkResolver(ipfs_client=ipfs)
    if verbose:
        resolver.set_verbose(True)
    
    # Parse link
    if verbose:
        click.echo(click.style(f"🔍 Parsing link: {link}", fg="cyan"))
    
    try:
        # Parse the link to determine protocol
        parsed = resolver.parse_link(link)
        protocol = parsed["protocol"]
        identifier = parsed["identifier"]
        
        if verbose:
            click.echo(f"   Protocol: {protocol}")
            click.echo(f"   Identifier: {identifier[:50]}...")
            if parsed["author_hint"]:
                click.echo(f"   Author hint: {parsed['author_hint']}")
            if parsed["type_hint"] != "unknown":
                click.echo(f"   Type hint: {parsed['type_hint']}")
            click.echo()
        
        # Determine the resource string to pass to resolve_content
        if protocol in ["http", "https"]:
            resource = link  # Use full URL
        else:
            resource = identifier  # For fx and ipns, use identifier
        
        # Resolve content
        content = resolver.resolve_content(
            resource,
            skip_cache=no_cache,
            expected_pubkey=None,
            do_verify=not allow_unverified  # Skip verification if allow_unverified is True
        )
        
        # Extract metadata
        author = content.get("author", "unknown")
        pubkey = content.get("pubkey", "")[:12] + "..." if content.get("pubkey") else "unknown"
        created_at = content.get("created_at", "unknown")
        content_type = content.get("_validated_type", "unknown")
        resolved_via = content.get("_resolved_via", "unknown")
        
        # Show verification status
        if allow_unverified:
            click.echo(click.style(f"⚠️  Verification skipped", fg="yellow", bold=True))
        else:
            click.echo(click.style(f"✅ Content resolved", fg="green", bold=True))
        
        click.echo(f"   Author: {author}")
        click.echo(f"   Pubkey: {pubkey}")
        click.echo(f"   Type: {content_type}")
        click.echo(f"   Via: {resolved_via}")
        if created_at != "unknown":
            try:
                dt = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
                click.echo(f"   Created: {dt.strftime('%Y-%m-%d %H:%M:%S UTC')}")
            except:
                click.echo(f"   Created: {created_at}")
        click.echo()
        
        # Render content
        if raw:
            import json
            click.echo(click.style("📄 Raw JSON:", fg="yellow"))
            click.echo(json.dumps(content, indent=2, ensure_ascii=False))
        else:
            click.echo(click.style(f"📝 Content:", fg="green", bold=True))
            
            # Format content based on type
            if content_type in ["profile", "manifest (unverified)", "unverified"] and "display_name" in content:
                # It's a profile
                click.echo(f"   Display name: {content.get('display_name', 'unknown')}")
                click.echo(f"   Profile IPNS: {content.get('profile_ipns', 'N/A')}")
                click.echo(f"   Manifest IPNS: {content.get('manifest_ipns', 'N/A')}")
                if content.get("threads_ipns"):
                    click.echo(f"   Threads: {len(content['threads_ipns'])}")
                click.echo(f"   Bio: {content.get('bio', '')}")
            elif content_type in ["manifest", "manifest (unverified)", "unverified"] and "entries" in content:
                # It's a manifest
                entries = content.get("entries", [])
                click.echo(f"   Posts: {len(entries)}")
                click.echo(f"   Version: {content.get('manifest_version', 'unknown')}")
                for i, entry in enumerate(entries[:5]):
                    cid = entry.get('cid', '')[:16]
                    etype = entry.get('type', 'unknown')
                    click.echo(f"     {i+1}. {cid}... ({etype})")
                if len(entries) > 5:
                    click.echo(f"     ... and {len(entries) - 5} more")
            elif content_type == "post" or content.get("content") is not None:
                # It's a post
                click.echo(f"   {content.get('content', '[No content]')}")
                if content.get("value"):
                    click.echo(f"   Value: {content['value']}")
                if content.get("thread_id"):
                    click.echo(f"   Thread: {content['thread_id'][:16]}...")
                if content.get("reply_to"):
                    click.echo(f"   Reply to: {content['reply_to'][:16]}...")
            else:
                # Unknown type, show all fields
                for key, value in list(content.items())[:10]:
                    if not key.startswith("_"):
                        click.echo(f"   {key}: {str(value)[:50]}")
            
            click.echo()
        
        # Show source URL for HTTP content
        if resolved_via == "http":
            click.echo(click.style("🌐 Source URL:", fg="blue"))
            click.echo(f"   {content.get('_resolved_from', link)}")
        else:
            # Show gateway URL
            gateway_url = ipfs.get_gateway_url(content.get('_resolved_cid', identifier))
            click.echo(click.style("🔗 Public gateway URL:", fg="blue"))
            click.echo(f"   {gateway_url}")
        
        # Cache info
        if not no_cache:
            click.echo(click.style(f"\n📦 Cached for offline use", fg="cyan"))
    
    except ResolutionError as e:
        click.echo(click.style(f"❌ Resolution failed: {e}", fg="red"))
        sys.exit(1)
    
    except SecurityError as e:
        click.echo(click.style(f"🔒 SECURITY BLOCKED: {e}", fg="red", bold=True))
        click.echo("This content failed cryptographic verification or contains unsafe types.")
        sys.exit(1)
    
    except ValueError as e:
        click.echo(click.style(f"❌ Invalid link: {e}", fg="red"))
        sys.exit(1)
    
    except Exception as e:
        click.echo(click.style(f"❌ Unexpected error: {e}", fg="red"))
        if verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)
    finally:
        # Clean up resolver resources
        resolver.close()
