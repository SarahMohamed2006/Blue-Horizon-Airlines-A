from datetime import datetime, timedelta

from memory.short_term import ShortTermMemory
from memory.scratchpad import Scratchpad
from memory.episodic import EpisodicMemory
from memory.semantic import SemanticMemory
from memory.router import PromoteOrDropRouter
from memory.consolidation import ConsolidationLayer
from memory.expiration import MemoryExpiration


def test_short_term_memory():
    memory = ShortTermMemory(max_size=2)
    memory.add("message 1")
    memory.add("message 2")
    memory.add("message 3")

    items = memory.get_all()

    assert len(items) == 2
    assert items[0]["content"] == "message 2"
    assert items[1]["content"] == "message 3"


def test_short_term_expiration():
    memory = ShortTermMemory(expiration_minutes=30)
    memory.add("old message")

    memory.items[0]["created_at"] = datetime.utcnow() - timedelta(minutes=31)

    assert memory.get_all() == []


def test_scratchpad():
    scratchpad = Scratchpad()

    scratchpad.set("flight", "BH218")

    assert scratchpad.get("flight") == "BH218"

    scratchpad.delete("flight")

    assert scratchpad.get("flight") is None


def test_router_promotes_operational_event():
    router = PromoteOrDropRouter()

    result = router.route(
        "Flight BH218 was delayed because of weather",
        {"key": "BH218_status"}
    )

    assert result["action"] == "promote"
    assert result["reason"]
    assert result["matched_keywords"]


def test_router_drops_irrelevant_event():
    router = PromoteOrDropRouter()

    result = router.route("Hello, how are you?")

    assert result["action"] == "drop"
    assert result["reason"]


def test_promoted_event_reaches_episodic_memory():
    router = PromoteOrDropRouter()
    episodic = EpisodicMemory()

    result = router.route(
        "Flight BH218 was delayed",
        {"key": "BH218_status"}
    )

    if result["action"] == "promote":
        episodic.store(
            result["content"],
            result["metadata"]
        )

    assert len(episodic.get_all()) == 1


def test_consolidation_builds_semantic_memory():
    episodic = EpisodicMemory()
    semantic = SemanticMemory()

    episodic.store(
        "Flight BH218 was delayed",
        {"key": "BH218_status"}
    )

    consolidation = ConsolidationLayer(
        episodic,
        semantic
    )

    consolidation.consolidate()

    assert semantic.get("BH218_status") == "Flight BH218 was delayed"


def test_semantic_versioning():
    episodic = EpisodicMemory()
    semantic = SemanticMemory()

    consolidation = ConsolidationLayer(
        episodic,
        semantic
    )

    episodic.store(
        "BH218 used Aircraft A",
        {"key": "BH218_aircraft"}
    )

    consolidation.consolidate()

    episodic.store(
        "BH218 used Aircraft B",
        {"key": "BH218_aircraft"}
    )

    consolidation.consolidate()

    history = semantic.get_history("BH218_aircraft")

    assert len(history) >= 2
    assert semantic.get("BH218_aircraft") == "BH218 used Aircraft B"


def test_conflict_resolution():
    episodic = EpisodicMemory()
    semantic = SemanticMemory()

    consolidation = ConsolidationLayer(
        episodic,
        semantic
    )

    episodic.store(
        "BH218 assigned Aircraft A",
        {"key": "BH218_assignment"}
    )

    consolidation.consolidate()

    episodic.store(
        "BH218 assigned Aircraft B",
        {"key": "BH218_assignment"}
    )

    consolidation.consolidate()

    assert semantic.get("BH218_assignment") == "BH218 assigned Aircraft B"

    history = semantic.get_history("BH218_assignment")

    assert len(history) >= 2


def test_memory_expiration():
    expiration = MemoryExpiration()

    created_at = datetime.utcnow() - timedelta(minutes=31)

    assert expiration.is_expired(created_at)


def test_full_memory_flow():
    short_term = ShortTermMemory()
    episodic = EpisodicMemory()
    semantic = SemanticMemory()
    router = PromoteOrDropRouter()

    content = "Flight BH218 had a maintenance delay"

    short_term.add(
        content,
        {"key": "BH218_status"}
    )

    for item in short_term.get_all():
        decision = router.route(
            item["content"],
            item["metadata"]
        )

        if decision["action"] == "promote":
            episodic.store(
                decision["content"],
                decision["metadata"]
            )

    consolidation = ConsolidationLayer(
        episodic,
        semantic
    )

    consolidation.consolidate()

    assert semantic.get("BH218_status") == content


def run_tests():
    tests = [
        test_short_term_memory,
        test_short_term_expiration,
        test_scratchpad,
        test_router_promotes_operational_event,
        test_router_drops_irrelevant_event,
        test_promoted_event_reaches_episodic_memory,
        test_consolidation_builds_semantic_memory,
        test_semantic_versioning,
        test_conflict_resolution,
        test_memory_expiration,
        test_full_memory_flow,
    ]

    passed = 0

    for test in tests:
        try:
            test()
            print(f"PASS: {test.__name__}")
            passed += 1
        except Exception as e:
            print(f"FAIL: {test.__name__} -> {e}")

    print(f"\n{passed}/{len(tests)} tests passed")


if __name__ == "__main__":
    run_tests()
