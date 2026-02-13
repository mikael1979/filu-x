"""Resolve command – fetch and verify remote Filu-X content"""
import sys
import click
from datetime import datetime

from filu_x.core.resolver import LinkResolver, ResolutionError, SecurityError
from filu_x.core.ipfs_client import IPFSClient

@click.command()
@click.argument("link")
@click.option("--raw", is_flag=True, help="Show raw JSON instead of formatted content")
@click.option("--no-cache", is_flag=True, help="Skip cache and fetch fresh from IPFS")
@click.option("--verbose", "-v", is_flag=True, help="Show detailed verification info")
def resolve(link: str, raw: bool, no_cache: bool, verbose: bool):
    """
    Resolve and display Filu-X content from fx:// link.
    
    Verifies cryptographic signature before showing content.
    
    Examples:
      filu-x resolve fx://bafkrei...
      filu-x resolve "fx://bafkrei...?author=ed25519:8a1b&type=post"
      filu-x resolve fx://bafkrei... --raw
    """
    try:
        # Initialize resolver
        ipfs = IPFSClient(mode="auto")
        resolver = LinkResolver(ipfs_client=ipfs)
        
        # Parse link
        if verbose:
            click.echo(click.style(f"🔍 Parsing link: {link}", fg="cyan"))
        
        parsed = resolver.parse_fx_link(link)
        cid = parsed["cid"]
        
        if verbose:
            click.echo(f"   CID: {cid}")
            if parsed["author_hint"]:
                click.echo(f"   Author hint: {parsed['author_hint']}")
            if parsed["type_hint"] != "unknown":
                click.echo(f"   Type hint: {parsed['type_hint']}")
            click.echo()
        
        # Resolve content (with signature verification)
        click.echo(click.style(f"📥 Fetching content from {'real IPFS' if ipfs.use_real else 'mock IPFS'}...", fg="blue"))
        content = resolver.resolve_content(cid, skip_cache=no_cache)
        
        # Extract metadata
        author = content.get("author", "unknown")
        pubkey = content.get("pubkey", "")[:12] + "..."
        created_at = content.get("created_at", "unknown")
        content_type = content.get("_validated_type", "unknown")
        
        # Show verification success
        click.echo(click.style(f"✅ Signature verified", fg="green", bold=True))
        click.echo(f"   Author: {author}")
        click.echo(f"   Pubkey: {pubkey}")
        click.echo(f"   Type: {content_type}")
        if created_at != "unknown":
            # Format timestamp nicely
            try:
                dt = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
                click.echo(f"   Created: {dt.strftime('%Y-%m-%d %H:%M:%S UTC')}")
            except:
                click.echo(f"   Created: {created_at}")
        click.echo()
        
        # Render content
        rendered = resolver.render_content(content, raw=raw)
        
        if raw:
            click.echo(click.style("📄 Raw JSON:", fg="yellow"))
            click.echo(rendered)
        else:
            click.echo(click.style(f"📝 Content:", fg="green", bold=True))
            click.echo(rendered)
            click.echo()
        
        # Show gateway URL
        gateway_url = ipfs.get_gateway_url(cid)
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
        click.echo()
        click.echo("This content failed cryptographic verification or contains unsafe types.")
        click.echo("Do not trust this content – it may be malicious or tampered with.")
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
