from memory.short_term import ShortTermMemory
from memory.episodic import EpisodicMemory
from memory.semantic import SemanticMemory
from memory.router import PromoteOrDropRouter
from memory.consolidation import ConsolidationLayer


def main():
    short_term = ShortTermMemory()
    episodic = EpisodicMemory()
    semantic = SemanticMemory()
    router = PromoteOrDropRouter()

    print("=== SHORT-TERM ===")

    content = "Flight BH218 was delayed because of weather"

    short_term.add(
        content,
        {"key": "BH218_status"}
    )

    print(short_term.get_all())

    print("\n=== ROUTER ===")

    decision = router.route(
        content,
        {"key": "BH218_status"}
    )

    print(decision)

    if decision["action"] == "promote":
        episodic.store(
            decision["content"],
            decision["metadata"]
        )

    print("\n=== EPISODIC ===")
    print(episodic.get_all())

    print("\n=== CONSOLIDATION ===")

    consolidation = ConsolidationLayer(
        episodic,
        semantic
    )

    promoted = consolidation.consolidate()

    print("Promoted:", promoted)

    print("\n=== SEMANTIC ===")
    print(semantic.get_all())


if __name__ == "__main__":
    main()
