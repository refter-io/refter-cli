import click

from refter.utils.deploy import deploy as _deploy
from refter.utils.validation import validate as _validate


@click.group()
def cli():
    pass


@cli.command()
@click.option(
    "-m",
    "--manifest",
    default="target/manifest.json",
    type=click.Path(exists=True),
)
def validate(manifest: str):
    _validate(manifest)


@cli.command()
@click.option(
    "-m",
    "--manifest",
    default="target/manifest.json",
    type=click.Path(exists=True),
)
@click.option("-t", "--token", required=True)
@click.option("-b", "--branch")
@click.option("-c", "--commit")
def deploy(manifest: str, token: str, branch: str, commit: str):
    _validate(manifest)
    _deploy(manifest, token, branch, commit)
