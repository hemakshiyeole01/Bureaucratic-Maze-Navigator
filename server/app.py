"""
server/app.py — OpenEnv entry point for multi-mode deployment.
Required by openenv validate. Delegates to bureaucratic_maze.server.
"""

import uvicorn
from bureaucratic_maze.server import app  # noqa: F401 — re-exported for openenv serve


def main() -> None:
    """Entry point for openenv serve, uv run server, and direct invocation."""
    uvicorn.run(
        "bureaucratic_maze.server:app",
        host="0.0.0.0",
        port=7860,
        reload=False,
    )


if __name__ == "__main__":
    main()
