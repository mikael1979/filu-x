import click
from .commands.init import init

@click.group()
@click.version_option(version="0.0.1", prog_name="filu-x")
def cli():
    """Filu-X: File-based decentralized social media"""
    pass

cli.add_command(init)

if __name__ == "__main__":
    cli()
