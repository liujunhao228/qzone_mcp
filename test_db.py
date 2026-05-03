import asyncio
from pathlib import Path
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

async def test_db():
    # Test with a simple path
    test_path = Path("F:/astrbot/qzone_mcp/test.db")
    print(f"Test path: {test_path}")
    print(f"Parent exists: {test_path.parent.exists()}")
    
    # Create parent dir if needed
    test_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Try to create engine
    try:
        database_url = f"sqlite+aiosqlite:///{test_path}"
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
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_db())
