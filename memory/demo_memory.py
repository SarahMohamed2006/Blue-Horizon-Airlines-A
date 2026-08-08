from memory.short_term import ShortTermMemory
from memory.scratchpad import Scratchpad
from memory.router import PromoteOrDropRouter
from memory.episodic import EpisodicMemory
from memory.semantic import SemanticMemory
from memory.consolidation import ConsolidationLayer


def main():
    short_term = ShortTermMemory(max_size=3)
    scratchpad = Scratchpad()
    router = PromoteOrDropRouter()
    episodic = EpisodicMemory()
    semantic = SemanticMemory()

    print("=== SHORT-TERM MEMORY ===")

    short_term.add(
        "Flight BH218 was delayed because of weather",
        {"key": "BH218_status"}
    )

    short_term.add(
        "Flight BH218 was assigned Aircraft A",
        {"key": "BH218_aircraft"}
    )

    short_term.add(
        "Flight BH218 requires maintenance review",
        {"key": "BH218_maintenance"}
    )

    for item in short_term.get_all():
        print(item)

    print("\n=== SCRATCHPAD ===")

    scratchpad.set("current_flight", "BH218")
    scratchpad.set("current_task", "Resolve operational issue")

    print("Flight:", scratchpad.get("current_flight"))
    print("Task:", scratchpad.get("current_task"))

    print("\n=== PROMOTE OR DROP ===")

    for item in short_term.get_all():
        decision = router.route(
            item["content"],
            item["metadata"]
        )

        print(decision)

        if decision["action"] == "promote":
            episodic.store(
                decision["content"],
                decision["metadata"]
            )

    print("\n=== EPISODIC MEMORY ===")

    for item in episodic.get_all():
        print(item)

    print("\n=== CONSOLIDATION ===")

    consolidation = ConsolidationLayer(
        episodic,
        semantic
    )

    result = consolidation.consolidate()

    print("Consolidation result:", result)

    print("\n=== SEMANTIC MEMORY ===")

    for key in [
        "BH218_status",
        "BH218_aircraft",
        "BH218_maintenance"
    ]:
        print(key, ":", semantic.get(key))

    print("\n=== VERSIONING / CONFLICT ===")

    episodic.store(
        "BH218 was assigned Aircraft B",
        {"key": "BH218_aircraft"}
    )

    consolidation.consolidate()

    print("Current aircraft:", semantic.get("BH218_aircraft"))
    print(
        "Aircraft history:",
        semantic.get_history("BH218_aircraft")
    )

    print("\n=== DEMO COMPLETED ===")


if __name__ == "__main__":
    main()
