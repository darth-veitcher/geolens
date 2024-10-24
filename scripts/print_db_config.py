from geolens.config import get_settings

settings = get_settings()
print(f"Database URL: {settings.DATABASE_URL}")
print(f"Pool Size: {settings.DATABASE_POOL_SIZE}")