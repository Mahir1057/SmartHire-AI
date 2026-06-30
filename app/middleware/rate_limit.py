from time import monotonic

from fastapi import Request, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse, Response


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, requests_per_minute: int) -> None:
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self._buckets: dict[str, list[float]] = {}

    async def dispatch(self, request: Request, call_next) -> Response:
        client_host = request.client.host if request.client else "anonymous"
        now = monotonic()
        window_start = now - 60
        timestamps = [timestamp for timestamp in self._buckets.get(client_host, []) if timestamp > window_start]

        if len(timestamps) >= self.requests_per_minute:
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={"detail": "Rate limit exceeded"},
            )

        timestamps.append(now)
        self._buckets[client_host] = timestamps
        return await call_next(request)

