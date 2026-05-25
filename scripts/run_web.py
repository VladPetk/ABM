"""
Launch the polarlab web app (FastAPI + static frontend) locally.

    python scripts/run_web.py             # default localhost:8000
    python scripts/run_web.py --port 8001
    python scripts/run_web.py --host 0.0.0.0 --port 80    # public bind
"""
from __future__ import annotations

import argparse


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--host", default="127.0.0.1")
    p.add_argument("--port", type=int, default=8000)
    p.add_argument("--reload", action="store_true", help="Hot-reload on code change")
    args = p.parse_args()

    import uvicorn
    uvicorn.run(
        "abm.web.server:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        log_level="info",
    )


if __name__ == "__main__":
    main()
