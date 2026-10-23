"""`uv run python -m tramlines.server` starts the viewer's server on http://127.0.0.1:8000."""

import uvicorn

if __name__ == "__main__":
    uvicorn.run("tramlines.server.app:app", host="127.0.0.1", port=8000)
