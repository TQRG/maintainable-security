"""Logging utils."""
import click

def info(text):
    """Log text at info level."""
    click.secho(str(text), fg='blue')

def success(text):
    """Log text at success level."""
    click.secho(str(text), fg='green')

def warning(text):
    """Log text at warning level."""
    click.secho(str(text), fg='yellow')

def error(text):
    """Log text at warning level."""
    click.secho(str(text), fg='red')
