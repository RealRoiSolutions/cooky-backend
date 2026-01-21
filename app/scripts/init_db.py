import asyncio
import asyncpg
import sys
import os

# Add project root to sys.path
sys.path.append(os.getcwd())

from app.core.config import settings

async def create_database():
    from sqlalchemy.engine.url import make_url
    url = make_url(settings.DATABASE_URL)
    
    db_name = url.database
    user = url.username
    password = url.password
    host = url.host
    port = url.port
    
    print(f"Connecting to postgres to check/create database '{db_name}'...")
    
    try:
        conn = await asyncpg.connect(user=user, password=password, host=host, port=port, database='postgres')
        exists = await conn.fetchval(f"SELECT 1 FROM pg_database WHERE datname = '{db_name}'")
        
        if not exists:
            print(f"Database '{db_name}' does not exist. Creating...")
            await conn.execute(f'CREATE DATABASE "{db_name}"')
            print(f"Database '{db_name}' created successfully.")
        else:
            print(f"Database '{db_name}' already exists.")
            
        await conn.close()
    except Exception as e:
        print(f"Error creating database: {e}")
        print("Ensure Postgres is running and credentials in .env are correct.")

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(create_database())
