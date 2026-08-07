import sys
from pathlib import Path


# Add the agent directory to Python path.
sys.path.append(
    str(Path(__file__).resolve().parents[1])
)


from context_manager import ContextManager


# ============================================================
# Sliding Window Test
# ============================================================

def test_sliding_window():

    manager = ContextManager(
        window_size=3
    )

    manager.add_message(
        "user",
        "Message 1"
    )

    manager.add_message(
        "user",
        "Message 2"
    )

    manager.add_message(
        "user",
        "Message 3"
    )

    manager.add_message(
        "user",
        "Message 4"
    )

    result = manager.sliding_window()

    assert len(result) == 3

    assert result[0]["content"] == "Message 2"

    assert result[-1]["content"] == "Message 4"


# ============================================================
# Observation Masking Test
# ============================================================

def test_observation_masking():

    manager = ContextManager()

    manager.add_message(
        "user",
        "Contact me at test@example.com"
    )

    result = manager.observation_masking()

    assert len(result) == 1

    assert "[EMAIL]" in result[0]["content"]


# ============================================================
# Recursive Summarization Test
# ============================================================

def test_recursive_summarization():

    manager = ContextManager(
        window_size=10,
        recent_size=5
    )

    for i in range(8):

        manager.add_message(
            "user",
            f"Message {i}"
        )

    result = manager.recursive_summarization()

    # One summary + five recent messages
    assert isinstance(result, list)

    assert len(result) == 6

    assert result[0]["role"] == "system"

    assert (
        "Historical context summary:"
        in result[0]["content"]
    )

    assert len(result[1:]) == 5


# ============================================================
# Zone-Based Pruning Test
# ============================================================

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

    # The result contains two zones.
    assert isinstance(result, dict)

    assert "important" in result

    assert "recent" in result

    # The maintenance message must be preserved.
    assert len(result["important"]) == 1

    assert (
        "maintenance"
        in result["important"][0]["content"].lower()
    )


# ============================================================
# Invalid Configuration Test
# ============================================================

def test_invalid_window_size():

    try:
        ContextManager(window_size=0)
        assert False

    except ValueError:
        assert True


def test_invalid_recent_size():

    try:
        ContextManager(recent_size=0)
        assert False

    except ValueError:
        assert True


# ============================================================
# Message Validation Test
# ============================================================

def test_message_validation():

    manager = ContextManager()

    try:
        manager.add_message(
            123,
            "Hello"
        )
        assert False

    except TypeError:
        assert True

    try:
        manager.add_message(
            "user",
            123
        )
        assert False

    except TypeError:
        assert True
