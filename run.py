import os
from app.web import app

if __name__ == "__main__":
    import uvicorn

    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(
        app,
        host=host,
        port=port,
        timeout_keep_alive=300,
        limit_concurrency=None,
        limit_max_requests=None,
        backlog=4096,
        h11_max_incomplete_event_size=64 * 1024 * 1024,
    )

