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

            # NOTE: consolidation is intentionally NOT triggered here.
            # The promote-or-drop router only ever writes to episodic
            # memory. Semantic memory is built exclusively by a separate,
            # periodic consolidation pass — see run_consolidation() below.
            return {
                "action": "promote",
                "episode": episode,
                "reason": decision["reason"],
            }

        return {
            "action": "drop",
            "reason": decision["reason"],
        }

    def run_consolidation(self):
        """
        Separate, periodic consolidation pass over episodic memory.

        This is the only path that writes to semantic memory. It should
        be invoked on a schedule (e.g. a periodic job, or at natural
        session boundaries) rather than after every promoted event, so
        that consolidation can genuinely batch, version, and resolve
        conflicts across multiple episodes rather than reacting to one
        write at a time.
        """
        return self.consolidation.consolidate()

    def recall(self, key):
        return self.semantic.get(key)

    def get_short_term(self):
        return self.short_term.get_all()

    def get_episodes(self):
        return self.episodic.get_all()

    def get_semantic(self):
        return self.semantic.get_all()
