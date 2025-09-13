from typing import Dict
from src.repo.memory_store import MemoryStore


class RevenueService:
    def __init__(self, store: MemoryStore) -> None:
        self.store = store

    def revenue_for(self, cinema: str) -> int:
        return self.store.get_revenue(cinema)

    def all_revenue(self) -> Dict[str, int]:
        return self.store.all_revenue()
