import sys
from pathlib import Path

sys.path.append(
    str(Path(__file__).resolve().parents[1])
)

from context_manager import ContextManager


def test_sliding_window():

    manager = ContextManager(window_size=3)

    manager.add_message("user", "Message 1")
    manager.add_message("user", "Message 2")
    manager.add_message("user", "Message 3")
    manager.add_message("user", "Message 4")

    result = manager.sliding_window()

    assert len(result) == 3
    assert result[0]["content"] == "Message 2"


def test_observation_masking():

    manager = ContextManager()

    manager.add_message(
        "user",
        "Contact me at test@example.com"
    )

    result = manager.observation_masking()

    assert "[EMAIL]" in result[0]["content"]


ddef test_recursive_summarization():

    manager = ContextManager(window_size=10)

    for i in range(8):
        manager.add_message(
            "user",
            f"Message {i}"
        )

    result = manager.recursive_summarization()

    assert isinstance(result, list)
    assert len(result) == 6

    assert result[0]["role"] == "system"
    assert "Historical context summary:" in result[0]["content"]

    assert len(result[1:]) == 5


def test_zone_based_pruning():

    manager = ContextManager()

    manager.add_message(
        "user",
        "Flight BH218 had a maintenance issue."
    )

    manager.add_message(
        "user",
        "Everything is normal."
    )

    result = manager.zone_based_pruning()

    assert len(result["important"]) == 1
    assert "maintenance" in result["important"][0]["content"].lower()
