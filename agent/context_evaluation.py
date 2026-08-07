import time

from context_manager import ContextManager


# ============================================================
# Test Cases
# ============================================================

TEST_CASES = [
    {
        "name": "Weather Delay",
        "messages": [
            ("user", "Flight BH218 was delayed because of bad weather."),
            ("agent", "A backup aircraft may be required."),
            ("user", "Operations approved the backup aircraft."),
            ("agent", "Backup aircraft assigned to BH218."),
            ("user", "The passengers were notified."),
            ("agent", "The delay announcement was sent."),
            ("user", "Crew duty limits were checked."),
            ("agent", "Crew remained within duty limits."),
            ("user", "What happened to BH218 earlier?"),
        ],
        "expected_keywords": [
            "BH218",
            "weather",
            "backup aircraft",
        ],
    },
    {
        "name": "Maintenance Issue",
        "messages": [
            ("user", "BH305 reported a maintenance problem."),
            ("agent", "The aircraft was removed from service."),
            ("user", "Maintenance severity was marked critical."),
            ("agent", "A replacement aircraft is required."),
            ("user", "Operations assigned a backup aircraft."),
            ("agent", "The replacement aircraft is now assigned."),
            ("user", "What happened to BH305?"),
        ],
        "expected_keywords": [
            "BH305",
            "maintenance",
            "backup aircraft",
        ],
    },
    {
        "name": "Crew Reassignment",
        "messages": [
            ("user", "Flight BH410 requires backup crew."),
            ("agent", "Crew availability was checked."),
            ("user", "A qualified crew member was available."),
            ("agent", "Backup crew was assigned."),
            ("user", "What was the previous crew action?"),
        ],
        "expected_keywords": [
            "BH410",
            "backup crew",
        ],
    },
]


# ============================================================
# Build Context
# ============================================================

def build_context(messages, window_size=10):
    manager = ContextManager(window_size=window_size)

    for role, content in messages:
        manager.add_message(role, content)

    return manager


# ============================================================
# Convert Strategy Output to Text
# ============================================================

def flatten_context(result):
    """
    Convert the output of any strategy into a single text
    representation for evaluation.
    """

    if isinstance(result, list):

        return " ".join(
            item["content"]
            for item in result
        )

    if isinstance(result, dict):

        parts = []

        if "summary" in result:
            parts.append(result["summary"])

        if "important" in result:
            parts.extend(
                item["content"]
                for item in result["important"]
            )

        if "recent" in result:
            parts.extend(
                item["content"]
                for item in result["recent"]
            )

        return " ".join(parts)

    return str(result)


# ============================================================
# Accuracy
# ============================================================

def calculate_accuracy(context_text, expected_keywords):
    """
    Simple retrieval accuracy:
    percentage of expected keywords preserved
    in the resulting context.
    """

    text = context_text.lower()

    if not expected_keywords:
        return 1.0

    found = sum(
        1
        for keyword in expected_keywords
        if keyword.lower() in text
    )

    return found / len(expected_keywords)


# ============================================================
# Token Approximation
# ============================================================

def estimate_tokens(text):
    """
    Lightweight token approximation.

    This is intentionally model-independent.
    A rough estimate of 1 token ~= 4 characters.
    """

    return max(1, len(text) // 4)


# ============================================================
# Evaluate Strategy
# ============================================================

def evaluate_strategy(manager, strategy_name, expected_keywords):

    start = time.perf_counter()

    if strategy_name == "Sliding Window":

        result = manager.sliding_window()

    elif strategy_name == "Observation Masking":

        result = manager.observation_masking()

    elif strategy_name == "Recursive Summarization":

        result = manager.recursive_summarization()

    elif strategy_name == "Zone-Based Pruning":

        result = manager.zone_based_pruning()

    else:
        raise ValueError(
            f"Unknown strategy: {strategy_name}"
        )

    latency_ms = (
        time.perf_counter() - start
    ) * 1000

    context_text = flatten_context(result)

    accuracy = calculate_accuracy(
        context_text,
        expected_keywords
    )

    tokens = estimate_tokens(context_text)

    return {
        "strategy": strategy_name,
        "accuracy": round(accuracy, 3),
        "tokens": tokens,
        "latency_ms": round(latency_ms, 3),
    }


# ============================================================
# Run Evaluation
# ============================================================

def run_evaluation():

    strategies = [
        "Sliding Window",
        "Observation Masking",
        "Recursive Summarization",
        "Zone-Based Pruning",
    ]

    all_results = []

    for test_case in TEST_CASES:

        manager = build_context(
            test_case["messages"],
            window_size=3
        )

        for strategy in strategies:

            result = evaluate_strategy(
                manager,
                strategy,
                test_case["expected_keywords"]
            )

            result["test_case"] = test_case["name"]

            all_results.append(result)

    return all_results


# ============================================================
# Print Comparison Table
# ============================================================

def print_results(results):

    print("\n" + "=" * 80)
    print("CONTEXT STRATEGY EVALUATION")
    print("=" * 80)

    print(
        f"{'Test Case':<25}"
        f"{'Strategy':<28}"
        f"{'Accuracy':<12}"
        f"{'Tokens':<10}"
        f"{'Latency(ms)':<12}"
    )

    print("-" * 87)

    for result in results:

        print(
            f"{result['test_case']:<25}"
            f"{result['strategy']:<28}"
            f"{result['accuracy']:<12}"
            f"{result['tokens']:<10}"
            f"{result['latency_ms']:<12}"
        )


# ============================================================
# Main
# ============================================================

if __name__ == "__main__":

    results = run_evaluation()

    print_results(results)
