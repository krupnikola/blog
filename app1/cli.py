# a file that stores custom created flask-babel CLI commands for managing translations file
# it will be enough to import it to microblog.py to get the custom CLI commands registered in runtime

from app1 import app
import os
import click


@app.cli.group()
def translate():
    """Translation and localization commands."""
    pass


@translate.command()
def update():
    """Update all languages."""
    # command os.system('') executes the command in a subshell
    if os.system('pybabel extract -F babel.cfg -k _l -o messages.pot .'):
        raise RuntimeError('extract command failed')
    if os.system('pybabel update -i messages.pot -d app1/translations'):
        raise RuntimeError('update command failed')
    os.remove('messages.pot')


@translate.command()
def compile():
    """Compile all languages."""
    if os.system('pybabel compile -d app1/translations'):
        raise RuntimeError('compile command failed')



@translate.command()
@click.argument('lang')
def init(lang):
    """Initialize a new language."""
    if os.system('pybabel extract -F babel.cfg -k _l -o messages.pot .'):
        raise RuntimeError('extract command failed')
    if os.system(
            'pybabel init -i messages.pot -d app1/translations -l ' + lang):
        raise RuntimeError('init command failed')
    os.remove('messages.pot')