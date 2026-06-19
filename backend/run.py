"""Entry point that forces SelectorEventLoop for psycopg3 async compatibility on Windows.

Python 3.12+ asyncio.run() accepts loop_factory; using it avoids the deprecated
set_event_loop_policy() API and works on Python 3.14.
"""
import asyncio
import selectors
import sys

import uvicorn


async def _serve() -> None:
    config = uvicorn.Config("app.main:app", host="127.0.0.1", port=8000, reload=False)
    server = uvicorn.Server(config)
    await server.serve()


if __name__ == "__main__":
    if sys.platform == "win32":
        # ProactorEventLoop (Windows default) is incompatible with psycopg3 async.
        # Force SelectorEventLoop via loop_factory (asyncio.run parameter since 3.12).
        asyncio.run(
            _serve(),
            loop_factory=lambda: asyncio.SelectorEventLoop(selectors.SelectSelector()),
        )
    else:
        asyncio.run(_serve())
