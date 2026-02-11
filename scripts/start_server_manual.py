import asyncio
import os
import signal
import sys
import logging

import uvicorn

from src.api import main

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def _init():
    logger.info("Manual init: calling initialize_system()")
    await main.initialize_system()

def _shutdown_loop(loop):
    try:
        logger.info("Manual shutdown: calling shutdown_system()")
        loop.run_until_complete(main.shutdown_system())
    except Exception as e:
        logger.exception("Error during manual shutdown: %s", e)

if __name__ == '__main__':
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    # Run initialization
    loop.run_until_complete(_init())

    # Start uvicorn with lifespan disabled (we already initialized)
    config = uvicorn.Config("src.api.main:app", host=os.getenv("HOST", "127.0.0.1"), port=int(os.getenv("PORT", 8001)), lifespan="off", log_level="info")
    server = uvicorn.Server(config)

    def _handle_sigterm(*_):
        logger.info("Received shutdown signal")
        server.should_exit = True

    signal.signal(signal.SIGINT, _handle_sigterm)
    signal.signal(signal.SIGTERM, _handle_sigterm)

    try:
        logger.info("Starting uvicorn server (manual) on %s:%s", config.host, config.port)
        server.run()
    finally:
        _shutdown_loop(loop)
        logger.info("Server stopped")
