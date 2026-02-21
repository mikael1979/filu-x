"""Resolve and display Filu-X content from fx:// or ipns:// links"""
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
@click.option("--no-cache", is_flag=True, help="Skip cache and fetch fresh from IPFS")
@click.option("--verbose", "-v", is_flag=True, help="Show detailed verification info")
def resolve(ctx, link: str, raw: bool, no_cache: bool, verbose: bool):
    """
    Resolve and display Filu-X content from fx:// or ipns:// link.
    
    Verifies cryptographic signature before showing content.
    
    Examples:
      filu-x resolve fx://bafkrei...
      filu-x resolve ipns://k51qzi5uqu5...
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
        # Käytetään uutta parse_link-metodia
        parsed = resolver.parse_link(link)
        protocol = parsed["protocol"]
        identifier = parsed["identifier"]
        
        if verbose:
            click.echo(f"   Protocol: {protocol}")
            click.echo(f"   Identifier: {identifier[:16]}...")
            if parsed["author_hint"]:
                click.echo(f"   Author hint: {parsed['author_hint']}")
            if parsed["type_hint"] != "unknown":
                click.echo(f"   Type hint: {parsed['type_hint']}")
            click.echo()
        
        # Resolve content (with signature verification)
        click.echo(click.style(f"📥 Fetching content from {'real IPFS' if ipfs.use_real else 'mock IPFS'}...", fg="blue"))
        content = resolver.resolve_content(identifier, skip_cache=no_cache)
        
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
            if content_type == "profile":
                click.echo(f"   Display name: {content.get('display_name', 'unknown')}")
                click.echo(f"   Profile IPNS: {content.get('profile_ipns', 'N/A')}")
                click.echo(f"   Manifest IPNS: {content.get('manifest_ipns', 'N/A')}")
                click.echo(f"   Bio: {content.get('bio', '')}")
            elif content_type == "manifest":
                entries = content.get("entries", [])
                click.echo(f"   Posts: {len(entries)}")
                for i, entry in enumerate(entries[:5]):
                    click.echo(f"     {i+1}. {entry.get('cid', '')[:16]}... ({entry.get('type', 'unknown')})")
                if len(entries) > 5:
                    click.echo(f"     ... and {len(entries) - 5} more")
            else:
                # Post or other content
                click.echo(f"   {content.get('content', '[No content]')}")
                if content.get("value"):
                    click.echo(f"   Value: {content['value']}")
            
            click.echo()
        
        # Show gateway URL
        gateway_url = ipfs.get_gateway_url(identifier)
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
