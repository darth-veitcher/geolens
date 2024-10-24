"""
Sample data loader for GeoLens.
Loads architectural and historical data for major European cities.
"""
import asyncio
import os
from pathlib import Path
from dotenv import load_dotenv
import asyncpg
from sentence_transformers import SentenceTransformer
import numpy as np
from datetime import datetime

# Load environment variables
load_dotenv()

# Database connection parameters from environment
DB_USER = os.getenv('POSTGRES_USER', 'geolens')
DB_PASS = os.getenv('POSTGRES_PASSWORD')
DB_NAME = os.getenv('POSTGRES_DB', 'geolens')
DB_PORT = os.getenv('POSTGRES_PORT', '5433')
DB_HOST = 'localhost'


def convert_embedding_to_pgvector(embedding: np.ndarray) -> str:
    """Convert numpy array to pgvector format [x,y,z,...]"""
    return f"[{','.join(str(x) for x in embedding)}]"


async def load_sample_data():
    # Connect to the database through pgpool
    conn_str: str = f'postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}'
    print(f"Using: {conn_str}")
    conn = await asyncpg.connect(
        conn_str
    )
    
    # Load sentence transformer for generating embeddings
    model = SentenceTransformer('all-MiniLM-L6-v2')
    
    try:
        # Sample architectural landmarks
        landmarks = [
            {
                "name": "Notre-Dame Cathedral",
                "location": (2.3488, 48.8529),  # Paris
                "description": "Medieval Catholic cathedral exemplifying French Gothic architecture.",
                "location_type": "religious",
                "architectural_features": {
                    "style": "French Gothic",
                    "year_built": 1163,
                    "architect": "Unknown",
                    "description": "Famous for its pioneering use of the rib vault and flying buttress."
                }
            },
            {
                "name": "Sagrada Familia",
                "location": (2.1744, 41.4036),  # Barcelona
                "description": "Extraordinary modern basilica designed by Antoni Gaudí.",
                "location_type": "religious",
                "architectural_features": {
                    "style": "Art Nouveau/Gothic",
                    "year_built": 1882,
                    "architect": "Antoni Gaudí",
                    "description": "Combines Gothic and curvilinear Art Nouveau forms in a unique way."
                }
            },
            {
                "name": "St. Paul's Cathedral",
                "location": (-0.0983, 51.5138),  # London
                "description": "Anglican cathedral with significant baroque influence.",
                "location_type": "religious",
                "architectural_features": {
                    "style": "English Baroque",
                    "year_built": 1675,
                    "architect": "Christopher Wren",
                    "description": "Masterpiece of English Baroque architecture with its distinctive dome."
                }
            },
        ]

        # Historical events
        events = [
            {
                "name": "Notre-Dame Construction Begins",
                "location_name": "Notre-Dame Cathedral",
                "event_date": datetime(1163, 1, 1),
                "event_type": "construction",
                "description": "Bishop Maurice de Sully orders the construction of Notre-Dame."
            },
            {
                "name": "Notre-Dame Fire",
                "location_name": "Notre-Dame Cathedral",
                "event_date": datetime(2019, 4, 15),
                "event_type": "disaster",
                "description": "Major fire severely damages the cathedral's roof and spire."
            },
            {
                "name": "Sagrada Familia Construction Begins",
                "location_name": "Sagrada Familia",
                "event_date": datetime(1882, 3, 19),
                "event_type": "construction",
                "description": "Construction begins under architect Francisco de Paula del Villar."
            }
        ]

        # Architectural influences (relationships)
        relationships = [
            {
                "from": "Notre-Dame Cathedral",
                "to": "St. Paul's Cathedral",
                "relationship_type": "influences",
                "strength": 0.7,
                "evidence": "Gothic architectural elements adapted in the English context."
            },
            {
                "from": "Notre-Dame Cathedral",
                "to": "Sagrada Familia",
                "relationship_type": "influences",
                "strength": 0.8,
                "evidence": "Gothic structural principles reinterpreted in modern form."
            }
        ]

        # Insert locations and architectural features
        for landmark in landmarks:
            # Insert location
            location_id = await conn.fetchval("""
                INSERT INTO geolens.locations 
                (name, description, location_type, geometry)
                VALUES ($1, $2, $3, ST_SetSRID(ST_MakePoint($4, $5), 4326))
                RETURNING id
            """, 
            landmark["name"],
            landmark["description"],
            landmark["location_type"],
            landmark["location"][0],  # longitude
            landmark["location"][1]   # latitude
            )

            # Generate and insert architectural features with embedding
            features = landmark["architectural_features"]
            feature_text = f"{features['style']} {features['description']}"
            embedding = model.encode(feature_text)
            
            # Convert embedding to pgvector format
            embedding_str = convert_embedding_to_pgvector(embedding)

            await conn.execute("""
                INSERT INTO geolens.architectural_features 
                (location_id, style, year_built, architect, description, embedding)
                VALUES ($1, $2, $3, $4, $5, $6::vector)
            """,
            location_id,
            features["style"],
            features["year_built"],
            features["architect"],
            features["description"],
            embedding_str
            )

        # Insert historical events
        for event in events:
            # Find associated location
            location_id = await conn.fetchval("""
                SELECT id FROM geolens.locations WHERE name = $1
            """, event["location_name"])

            # Generate embedding for event description
            embedding = model.encode(event["description"])
            embedding_str = convert_embedding_to_pgvector(embedding)

            await conn.execute("""
                INSERT INTO geolens.historical_events 
                (location_id, event_date, event_type, description, embedding)
                VALUES ($1, $2, $3, $4, $5::vector)
            """,
            location_id,
            event["event_date"],
            event["event_type"],
            event["description"],
            embedding_str
            )

        # Insert relationships
        for rel in relationships:
            # Find location IDs
            from_id = await conn.fetchval("""
                SELECT id FROM geolens.locations WHERE name = $1
            """, rel["from"])
            
            to_id = await conn.fetchval("""
                SELECT id FROM geolens.locations WHERE name = $1
            """, rel["to"])

            await conn.execute("""
                INSERT INTO geolens.relationships 
                (from_location_id, to_location_id, relationship_type, strength, evidence)
                VALUES ($1, $2, $3, $4, $5)
            """,
            from_id,
            to_id,
            rel["relationship_type"],
            rel["strength"],
            rel["evidence"]
            )

        print("Sample data loaded successfully!")

    except Exception as e:
        print(f"Error loading sample data: {e}")
        raise

    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(load_sample_data())