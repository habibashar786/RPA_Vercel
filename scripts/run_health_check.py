import asyncio
import json

from src.api import main

async def run_check():
    try:
        await main.initialize_system()
        resp = await main.health_check()
        print(json.dumps(resp.model_dump(), indent=2))
    except Exception as e:
        print("ERROR:", e)
    finally:
        try:
            await main.shutdown_system()
        except Exception:
            pass

if __name__ == '__main__':
    asyncio.run(run_check())
