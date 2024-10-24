"""
Command line interface for GeoLens.
"""
import asyncio
import click
from geolens.database.engine import create_async_engine
from geolens.database.init import init_database, load_sample_data
from geolens.config import get_settings
from sqlalchemy.ext.asyncio import AsyncSession

@click.group()
def cli():
    """GeoLens CLI commands."""
    pass

@cli.command()
@click.option('--with-sample-data', is_flag=True, help='Load sample data after initialization')
def init_db(with_sample_data: bool):
    """Initialize the database schema and optionally load sample data."""
    settings = get_settings()
    
    async def run():
        engine = create_async_engine(settings.DATABASE_URL)
        try:
            await init_database(engine)
            if with_sample_data:
                async with AsyncSession(engine) as session:
                    await load_sample_data(session)
            click.echo("Database initialized successfully!")
        finally:
            await engine.dispose()

    asyncio.run(run())

if __name__ == '__main__':
    cli()