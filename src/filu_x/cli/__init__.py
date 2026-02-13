import click
from .commands.init import init
from .commands.post import post
from .commands.sync import sync
from .commands.link import link
from .commands.resolve import resolve  # Uusi import

@click.group()
@click.version_option(version="0.0.1", prog_name="filu-x")
def cli():
    """Filu-X: File-based decentralized social media"""
    pass

cli.add_command(init)
cli.add_command(post)
cli.add_command(sync)
cli.add_command(link)
cli.add_command(resolve)  # Lisää resolve-komento

if __name__ == "__main__":
    cli()
