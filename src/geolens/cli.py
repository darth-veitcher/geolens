"""
Command line interface for GeoLens.
"""
import asyncio
import click
from geolens.database.engine import create_async_engine
from geolens.database.init import init_database, load_sample_data
from geolens.config import get_settings
from sqlalchemy.ext.asyncio import AsyncSession
from alembic.config import Config
from alembic import command

@click.group()
def cli():
    """GeoLens CLI commands."""
    pass

@cli.command()
@click.option('--with-sample-data', is_flag=True, help='Load sample data after initialization')
def init_db(with_sample_data: bool):
    """Initialize the database schema and optionally load sample data."""
    alembic_cfg = Config("alembic.ini")
    command.upgrade(alembic_cfg, "head")
    click.echo("Database initialized successfully!")
    async def run():
        try:
            if with_sample_data:
                settings = get_settings()
                engine = create_async_engine(settings.DATABASE_URL)
                await init_database(engine)
                async with AsyncSession(engine) as session:
                    await load_sample_data(session)
                    click.echo("Sample data loaded!")
        finally:
            await engine.dispose()

    asyncio.run(run())

@cli.command()
@click.argument('revision', required=False)
def db_upgrade(revision: str = 'head'):
    """Upgrade database to a later version."""
    alembic_cfg = Config("alembic.ini")
    command.upgrade(alembic_cfg, revision)
    click.echo(f"Database upgraded successfully to {revision}!")

@cli.command()
@click.argument('revision', required=True)
def db_downgrade(revision: str):
    """Downgrade database to a previous version."""
    alembic_cfg = Config("alembic.ini")
    command.downgrade(alembic_cfg, revision)
    click.echo(f"Database downgraded successfully to {revision}!")

@cli.command()
@click.argument('message')
def db_revision(message: str):
    """Create a new database revision."""
    alembic_cfg = Config("alembic.ini")
    command.revision(alembic_cfg, message=message, autogenerate=True)
    click.echo("Created new database revision!")

if __name__ == '__main__':
    cli()