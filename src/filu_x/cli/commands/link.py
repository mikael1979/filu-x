# src/filu_x/cli/commands/link.py
"""Link command – generate shareable fx:// links"""
import sys
import click

from filu_x.storage.layout import FiluXStorageLayout
from filu_x.core.ipfs_client import IPFSClient

@click.command()
@click.argument("target", default="latest")
@click.option("--profile", is_flag=True, help="Generate link to profile")
@click.option("--qr", is_flag=True, help="Generate QR code (requires qrcode)")
@click.option("--force-mock", is_flag=True, help="Force mock IPFS mode")
def link(target: str, profile: bool, qr: bool, force_mock: bool):
    """
    Generate shareable fx:// link to your content.
    
    TARGET can be:
      - "latest" (default): Your most recent post
      - "profile": Your profile
      - <post_id>: Specific post ID
    
    Examples:
      filu-x link                # Latest post
      filu-x link --profile      # Profile link
      filu-x link 20260201_hello # Specific post
    """
    layout = FiluXStorageLayout()
    
    if not layout.profile_path().exists():
        click.echo(click.style(
            "❌ User not initialized. Run: filu-x init <username>",
            fg="red"
        ))
        sys.exit(1)
    
    # Initialize IPFS client to check mode
    mode = "mock" if force_mock else "auto"
    ipfs = IPFSClient(mode=mode)
    
    try:
        if profile or target == "profile":
            # Get profile CID
            cid = ipfs.add_file(layout.profile_path())
            target_type = "profile"
        
        elif target == "latest":
            # Get latest post CID from manifest
            manifest = layout.load_json(layout.manifest_path())
            posts = [e for e in manifest.get("entries", []) if e.get("type") == "post"]
            
            if not posts:
                click.echo(click.style(
                    "⚠️  No posts found. Create a post first: filu-x post 'Hello'",
                    fg="yellow"
                ))
                sys.exit(1)
            
            # Use CID from manifest (or generate if missing)
            cid = posts[-1].get("cid")
            if not cid or not cid.startswith("Qm") and not cid.startswith("bafk"):
                post_path = layout.posts_dir / posts[-1]["path"].split("/")[-1]
                cid = ipfs.add_file(post_path)
            
            target_type = "latest post"
        
        else:
            # Specific post by ID
            post_path = layout.post_path(target)
            if not post_path.exists():
                post_path = layout.posts_dir / f"{target}.json"
            
            if not post_path.exists():
                available = [p.stem for p in layout.posts_dir.glob('*.json')]
                click.echo(click.style(
                    f"❌ Post not found: {target}\n"
                    f"   Available posts:\n"
                    + "\n".join([f"     • {p}" for p in available]),
                    fg="red"
                ))
                sys.exit(1)
            
            # Generate CID from file
            cid = ipfs.add_file(post_path)
            target_type = f"post '{target}'"
        
        # Build link
        link_url = f"fx://{cid}"
        
        # Display link
        mode_str = "real IPFS" if ipfs.use_real else "mock IPFS"
        click.echo(click.style(
            f"🔗 Shareable link to your {target_type} ({mode_str}):",
            fg="green",
            bold=True
        ))
        click.echo()
        click.echo(f"  {link_url}")
        click.echo()
        
        # QR code option
        if qr:
            try:
                import qrcode
                import io
                qr_code = qrcode.QRCode(version=1, box_size=4, border=2)
                qr_code.add_data(link_url)
                qr_code.make(fit=True)
                qr_io = io.StringIO()
                qr_code.print_ascii(out=qr_io)
                qr_io.seek(0)
                click.echo(qr_io.read())
                click.echo()
                click.echo("  Scan with any QR reader to open this link")
            except ImportError:
                click.echo(click.style(
                    "⚠️  QR code requires 'qrcode' package. Install with:\n"
                    "   pip install qrcode[pil]",
                    fg="yellow"
                ))
        
        # Usage hint
        click.echo(click.style(
            "💡 Share this link on Twitter, Mastodon, or anywhere!",
            fg="blue"
        ))
        click.echo()
        click.echo("   Example tweet:")
        click.echo(f'   "Just posted on Filu-X: {link_url}"')
    
    except Exception as e:
        click.echo(click.style(f"❌ {e}", fg="red"))
        sys.exit(1)
