from memory.short_term import ShortTermMemory
from memory.scratchpad import Scratchpad
from memory.episodic import EpisodicMemory
from memory.semantic import SemanticMemory
from memory.router import PromoteOrDropRouter
from memory.consolidation import ConsolidationLayer


def test_short_term_and_scratchpad_are_independent():
    memory = ShortTermMemory(max_size=2)
    scratchpad = Scratchpad()

    memory.add("message 1")
    memory.add("message 2")
    scratchpad.set("goal", "Handle BH218")

    memory.add("message 3")

    assert len(memory.get_all()) == 2
    assert scratchpad.get("goal") == "Handle BH218"


def test_router_promotes_operational_event():
    router = PromoteOrDropRouter()

    result = router.route(
        "Flight BH218 was delayed because of weather",
        {"key": "BH218_status"}
    )

    assert result["action"] == "promote"
    assert result["reason"]


def test_router_drops_irrelevant_message():
    router = PromoteOrDropRouter()

    result = router.route("Hello, how are you?")

    assert result["action"] == "drop"
    assert result["reason"]


def test_promoted_event_goes_to_episodic_memory():
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


def test_update_creates_new_version():
    episodic = EpisodicMemory()
    semantic = SemanticMemory()

    episodic.store(
        "BH218 used Aircraft A",
        {"key": "BH218_aircraft"}
    )

    consolidation = ConsolidationLayer(
        episodic,
        semantic
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


def test_conflict_is_resolved():
    episodic = EpisodicMemory()
    semantic = SemanticMemory()

    episodic.store(
        "BH218 assigned Aircraft A",
        {"key": "BH218_assignment"}
    )

    episodic.store(
        "BH218 assigned Aircraft B",
        {"key": "BH218_assignment"}
    )

    consolidation = ConsolidationLayer(
        episodic,
        semantic
    )
    consolidation.consolidate()

    assert semantic.get("BH218_assignment") is not None
    assert len(semantic.get_history("BH218_assignment")) >= 1


def test_expired_fact_is_not_returned():
    semantic = SemanticMemory()

    semantic.store(
        "Temporary aircraft assignment",
        "Aircraft C",
        {"key": "temporary_assignment", "ttl_minutes": 0}
    )

    assert semantic.get("temporary_assignment") is None


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
