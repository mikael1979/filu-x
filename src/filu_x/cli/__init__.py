import click
from .commands.init import init
from .commands.post import post
from .commands.sync import sync
from .commands.link import link
from .commands.resolve import resolve
from .commands.follow import follow
from .commands.feed import feed
from .commands.sync_followed import sync_followed  # NEW IMPORT

@click.group()
@click.version_option(version="0.0.2", prog_name="filu-x")  # UPDATED VERSION
@click.option("--lang", type=click.Choice(["en"]), default="en",
              help="Language for CLI output (English only in alpha)")
def cli(lang: str):
    """Filu-X: File-based decentralized social media"""
    pass

cli.add_command(init)
cli.add_command(post)
cli.add_command(sync)
cli.add_command(link)
cli.add_command(resolve)
cli.add_command(follow)
cli.add_command(feed)
cli.add_command(sync_followed)  # NEW COMMAND

if __name__ == "__main__":
    cli()
