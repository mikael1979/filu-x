"""Fetch command – retrieve and display content from IPFS by CID"""
import sys
import json
import click
from filu_x.core.ipfs_client import IPFSClient

@click.command()
@click.pass_context
@click.argument("cid")
@click.option("--raw", is_flag=True, help="Show raw bytes instead of JSON parsing")
def fetch(ctx, cid: str, raw: bool):
    """
    Fetch content from IPFS by CID and display it.
    
    Useful for debugging what's actually stored on IPFS.
    
    Examples:
      filu-x fetch bafkreibztk6you5...
      filu-x fetch QmXoypizjW3WknFiJnKLwHCnL72vedxjQkDDP1mXWo6uco --raw
    """
    # Initialize IPFS client
    ipfs = IPFSClient(mode="auto")
    
    # Clean CID (remove fx:// if present)
    if cid.startswith("fx://"):
        cid = cid[5:]
    
    click.echo(click.style(f"🔍 Fetching {cid[:16]}... from IPFS", fg="cyan"))
    
    # Fetch content
    content_bytes = ipfs.cat(cid)
    if content_bytes is None:
        click.echo(click.style(f"❌ Content not found for CID: {cid}", fg="red"))
        sys.exit(1)
    
    # Display
    if raw:
        # Show raw bytes as hexdump or just first 100 bytes as text?
        # For simplicity, show as text if printable, else hex
        try:
            text = content_bytes.decode('utf-8')
            click.echo(text)
        except UnicodeDecodeError:
            click.echo(click.style("Binary data, showing hexdump of first 256 bytes:", fg="yellow"))
            hexdump = content_bytes[:256].hex(' ')
            # split into lines of 32 bytes
            for i in range(0, len(hexdump), 96):
                click.echo(hexdump[i:i+96])
    else:
        # Try to parse as JSON
        try:
            data = json.loads(content_bytes.decode('utf-8'))
            click.echo(json.dumps(data, indent=2, ensure_ascii=False))
        except json.JSONDecodeError:
            click.echo(click.style("Content is not JSON. Use --raw to see raw data.", fg="yellow"))
            # Show first 200 chars as text
            try:
                text = content_bytes.decode('utf-8')
                preview = text[:200] + ("..." if len(text) > 200 else "")
                click.echo(preview)
            except:
                click.echo(click.style("Binary data, use --raw", fg="yellow"))
