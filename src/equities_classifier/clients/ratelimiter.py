"""rate limiter for HTTP / REST request of clients."""


# ruff and mypy per file settings
#

# fmt: off


from dataclasses import dataclass
from time import monotonic, sleep


@dataclass(slots=True)
class RateLimits:
    """Rate limit configuration."""

    max_batch_size: int
    requests_per_minute: int

    @property
    def min_request_interval(self) -> float:
        """Minimum interval between two requests in seconds."""

        return 60.0 / self.requests_per_minute


class RateLimiter:
    """Simple request rate limiter."""

    def __init__(self, requests_per_minute: int) -> None:
        """Initialize RateLimiter."""

        self._min_interval = 60.0 / requests_per_minute
        self._last_request: float | None = None

    def wait(self) -> None:
        """Wait until the next request is allowed."""

        if self._last_request is None:
            self._last_request = monotonic()
            return

        elapsed = monotonic() - self._last_request

        if elapsed < self._min_interval:
            sleep(self._min_interval - elapsed)

        self._last_request = monotonic()
