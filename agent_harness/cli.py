"""Console script for agent_harness."""
import sys
import click


@click.command()
def main(args=None):
    """Console script for agent_harness."""
    click.echo("Replace this message by putting your code into "
               "agent_harness.cli.main")
    click.echo("See click documentation at https://click.palletsprojects.com/")
    return 0


if __name__ == "__main__":
    sys.exit(main())  # pragma: no cover
