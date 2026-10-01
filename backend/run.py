"""Dev launcher: set the Windows event loop policy BEFORE uvicorn creates its loop.

Usage: py run.py [--host 0.0.0.0] [--port 8000]

Why this exists: uvicorn's default Proactor event loop on Windows kills the whole
server with "OSError: [WinError 64] The specified network name is no longer
available" as soon as a client (browser / Vite proxy) drops a keep-alive
connection. That aborts the accept loop, so the backend stops answering and
images/health checks fail with 500s. The Selector loop tolerates aborted accepts.

Setting the policy inside app.main is too late — uvicorn builds the loop before
importing the app — so it must happen here, prior to uvicorn.run().
"""

from __future__ import annotations

import asyncio
import sys

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

import uvicorn  # noqa: E402

from app.config import settings  # noqa: E402


def main() -> None:
    host = settings.api_host
    port = settings.api_port
    if "--host" in sys.argv:
        host = sys.argv[sys.argv.index("--host") + 1]
    if "--port" in sys.argv:
        port = int(sys.argv[sys.argv.index("--port") + 1])

    uvicorn.run(
        "app.main:app",
        host=host,
        port=port,
        log_level=settings.log_level.lower(),
    )


if __name__ == "__main__":
    main()
