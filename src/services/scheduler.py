from __future__ import annotations
import threading
from datetime import datetime
from typing import Dict, Optional
from src.utils.errors import DomainError


class Scheduler:
    """
    Minimal in-process scheduler that auto-starts shows at their start_time.
    - Uses a per-show threading.Timer.
    - Timers are lost on process restart (acceptable for this machine round).
    """

    def __init__(self, start_callback) -> None:
        """
        start_callback: callable(show_id:str) -> None
        Typically wired to ShowService.start_show.
        """
        self._start_cb = start_callback
        self._timers: Dict[str, threading.Timer] = {}
        self._lock = threading.Lock()

    def schedule_start(self, show_id: str, start_time: datetime) -> None:
        """(Re)schedule auto-start for a show_id. If time already passed, do nothing."""
        delay = (start_time - datetime.now()).total_seconds()
        if delay <= 0:
            # Past start time — do not auto-start; manual START command may be used.
            return
        with self._lock:
            self._cancel_nolock(show_id)
            t = threading.Timer(delay, self._trigger_start, args=(show_id,))
            t.daemon = True
            t.start()
            self._timers[show_id] = t

    def cancel(self, show_id: str) -> None:
        """Cancel a pending auto-start (e.g., if started manually earlier)."""
        with self._lock:
            self._cancel_nolock(show_id)

    def _cancel_nolock(self, show_id: str) -> None:
        t = self._timers.pop(show_id, None)
        if t is not None:
            try:
                t.cancel()
            except Exception:
                pass

    def _trigger_start(self, show_id: str) -> None:
        # Timer thread: attempt to start; ignore domain errors (e.g., already started/ended)
        try:
            self._start_cb(show_id)
        except DomainError:
            pass
        except Exception:
            # Swallow any unexpected error to avoid killing the timer thread.
            pass
        finally:
            # Cleanup timer reference
            with self._lock:
                self._timers.pop(show_id, None)
