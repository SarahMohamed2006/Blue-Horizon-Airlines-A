from memory.short_term import ShortTermMemory
from memory.episodic import EpisodicMemory
from memory.semantic import SemanticMemory
from memory.router import PromoteOrDropRouter
from memory.consolidation import ConsolidationLayer


class MemoryManager:
    def __init__(self):
        self.short_term = ShortTermMemory()
        self.episodic = EpisodicMemory()
        self.semantic = SemanticMemory()
        self.router = PromoteOrDropRouter()

        self.consolidation = ConsolidationLayer(
            self.episodic,
            self.semantic
        )

    def remember(self, content, metadata=None):
        self.short_term.add(content, metadata)

        item = self.short_term.get_all()[-1]

        decision = self.router.route(
            item["content"],
            item["metadata"]
        )

        if decision["action"] == "promote":
            episode = self.episodic.store(
                decision["content"],
                decision["metadata"]
            )

            self.consolidation.consolidate()

            return {
                "action": "promote",
                "episode": episode,
                "semantic": self.semantic.get_all()
            }

        return {
            "action": "drop"
        }

    def recall(self, key):
        return self.semantic.get(key)

    def get_short_term(self):
        return self.short_term.get_all()

    def get_episodes(self):
        return self.episodic.get_all()

    def get_semantic(self):
        return self.semantic.get_all()
from memory.manager import MemoryManager


def test_memory_manager_flow():
    manager = MemoryManager()

    result = manager.remember(
        "Flight BH218 was delayed because of weather",
        {"key": "BH218_status"}
    )

    assert result["action"] == "promote"
    assert manager.recall("BH218_status") == (
        "Flight BH218 was delayed because of weather"
    )


def test_memory_manager_drops_irrelevant_information():
    manager = MemoryManager()

    result = manager.remember(
        "Hello, how are you?"
    )

    assert result["action"] == "drop"
    assert manager.get_episodes() == []
