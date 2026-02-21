"""Filu-X CLI entry point"""
import os
from pathlib import Path
import click

from .commands.init import init
from .commands.post import post
from .commands.sync import sync
from .commands.link import link
from .commands.resolve import resolve
from .commands.follow import follow
from .commands.feed import feed
from .commands.sync_followed import sync_followed
from .commands.ls import ls
from .commands.rm import rm
from .commands.repost import repost
from .commands.thread import thread
from .commands.fetch import fetch

@click.group()
@click.version_option(version="0.0.4", prog_name="filu-x")
@click.option(
    "--data-dir",
    type=click.Path(file_okay=False),
    help="Custom data directory (default: ~/.local/share/filu-x). "
         "Also set via FILU_X_DATA_DIR environment variable."
)
@click.pass_context
def cli(ctx, data_dir: str):
    """
    Filu-X: File-based decentralized social media
    
    All data is stored as plain JSON files. No servers required.
    """
    ctx.ensure_object(dict)
    
    if data_dir:
        ctx.obj["data_dir"] = Path(data_dir).resolve()
    elif "FILU_X_DATA_DIR" in os.environ:
        ctx.obj["data_dir"] = Path(os.environ["FILU_X_DATA_DIR"]).resolve()
    else:
        ctx.obj["data_dir"] = None

cli.add_command(init)
cli.add_command(post)
cli.add_command(sync)
cli.add_command(link)
cli.add_command(resolve)
cli.add_command(follow)
cli.add_command(feed)
cli.add_command(sync_followed)
cli.add_command(ls)
cli.add_command(rm)
cli.add_command(repost)
cli.add_command(thread)
cli.add_command(fetch)

if __name__ == "__main__":
    cli()
