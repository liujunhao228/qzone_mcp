import asyncio
from pathlib import Path
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

async def test_db():
    # Test with .qzone directory
    qzone_dir = Path.home() / ".qzone"
    db_path = qzone_dir / "test_qzone.db"
    print(f"DB path: {db_path}")
    print(f"Parent exists: {db_path.parent.exists()}")
    
    # Create parent dir if needed
    db_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Remove existing test file
    if db_path.exists():
        db_path.unlink()
    
    # Try to create engine
    try:
        database_url = f"sqlite+aiosqlite:///{db_path}"
        print(f"Database URL: {database_url}")
        
        engine = create_async_engine(
            database_url,
            echo=True,
            connect_args={"check_same_thread": False}
        )
        
        async with engine.begin() as conn:
            await conn.execute(text("CREATE TABLE test (id INTEGER PRIMARY KEY)"))
            await conn.execute(text("INSERT INTO test (id) VALUES (1)"))
            result = await conn.execute(text("SELECT * FROM test"))
            print(f"Result: {result.fetchall()}")
        
        await engine.dispose()
        print("Database test successful!")
    except Exception as e:
        print(f"Error: {type(e).__name__}: {e}")

if __name__ == "__main__":
    asyncio.run(test_db())
