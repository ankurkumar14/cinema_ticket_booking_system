import threading
from collections import defaultdict


class ShowLockManager:
    """Provides a dedicated lock per show_id for atomic seat/revenue updates."""

    def __init__(self) -> None:
        self._locks = defaultdict(threading.Lock)
        self._global = threading.Lock()

    def get(self, show_id: str) -> threading.Lock:
        # defaultdict ensures presence; a tiny global lock is not needed here
        return self._locks[show_id]
