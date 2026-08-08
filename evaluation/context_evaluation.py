import os
import sys
import time

# context_manager.py lives in <project_root>/agent/, not in evaluation/,
# so it has to be added to sys.path explicitly before it can be imported.
sys.path.append(
    os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "agent",
    )
)

from context_manager import ContextManager


# ============================================================
# Test Case Builder
# ============================================================

def build_long_tool_output(prefix, index):
    """
    Create realistic but low-value tool output.

    These outputs intentionally add noise to the context so that
    the strategies can be compared on long-context management.
    """

    return (
        f"{prefix} tool report #{index}: "
        "routine operational status checked. "
        "No additional critical operational decision was found. "
        "Passenger count verified. "
        "Gate availability checked. "
        "Baggage status checked. "
        "Boarding system status checked. "
        "Crew availability database queried. "
        "Aircraft status database queried. "
        "Schedule consistency checked. "
        "Weather feed checked. "
        "Airport operations feed checked. "
        "No additional action required. "
        "This is routine operational information."
    )


# ============================================================
# Long-Context Test Cases
# ============================================================

TEST_CASES = [
    {
        "name": "Weather Delay Long Transcript",

        "messages": [

            # IMPORTANT EARLY DECISION
            (
                "user",
                "Flight BH218 was delayed because of severe weather."
            ),
            (
                "agent",
                "Operations approved a backup aircraft for BH218."
            ),
            (
                "user",
                "The backup aircraft was assigned to BH218."
            ),

            # Tool-heavy noise
            *[
                (
                    "tool",
                    build_long_tool_output(
                        "Weather operations",
                        i
                    )
                )
                for i in range(1, 31)
            ],

            # Additional conversation
            (
                "user",
                "Passengers were notified about the delay."
            ),
            (
                "agent",
                "The delay announcement was sent."
            ),
            (
                "tool",
                "Passenger notification tool completed successfully."
            ),
            (
                "tool",
                "Gate information was synchronized."
            ),
            (
                "tool",
                "Boarding system status was checked."
            ),

            # Final question
            (
                "user",
                "What happened to BH218 earlier?"
            ),
        ],

        "expected_keywords": [
            "BH218",
            "weather",
            "backup aircraft",
        ],
    },

    {
        "name": "Maintenance Long Transcript",

        "messages": [

            # IMPORTANT EARLY DECISION
            (
                "user",
                "BH305 reported a critical maintenance problem."
            ),
            (
                "agent",
                "The aircraft was removed from service."
            ),
            (
                "user",
                "Operations assigned a backup aircraft to BH305."
            ),

            # Tool-heavy noise
            *[
                (
                    "tool",
                    build_long_tool_output(
                        "Maintenance operations",
                        i
                    )
                )
                for i in range(1, 31)
            ],

            (
                "user",
                "The replacement aircraft is ready."
            ),
            (
                "agent",
                "The replacement aircraft is now assigned."
            ),

            (
                "tool",
                "Maintenance database synchronized."
            ),
            (
                "tool",
                "Aircraft availability refreshed."
            ),
            (
                "tool",
                "Gate assignment verified."
            ),

            # Final question
            (
                "user",
                "What happened to BH305?"
            ),
        ],

        "expected_keywords": [
            "BH305",
            "maintenance",
            "backup aircraft",
        ],
    },

    {
        "name": "Crew Reassignment Long Transcript",

        "messages": [

            # IMPORTANT EARLY DECISION
            (
                "user",
                "Flight BH410 requires backup crew."
            ),
            (
                "agent",
                "Operations approved a qualified backup crew."
            ),
            (
                "user",
                "Backup crew was assigned to BH410."
            ),

            # Tool-heavy noise
            *[
                (
                    "tool",
                    build_long_tool_output(
                        "Crew operations",
                        i
                    )
                )
                for i in range(1, 31)
            ],

            (
                "tool",
                "Crew availability was checked."
            ),
            (
                "tool",
                "Duty limits were verified."
            ),
            (
                "tool",
                "Airport staffing database synchronized."
            ),

            # Final question
            (
                "user",
                "What was the previous crew action for BH410?"
            ),
        ],

        "expected_keywords": [
            "BH410",
            "backup crew",
        ],
    },

    {
        "name": "Flight Cancellation Long Transcript",

        "messages": [

            # IMPORTANT EARLY DECISION
            (
                "user",
                "Flight BH512 was cancelled because of an aircraft safety issue."
            ),
            (
                "agent",
                "Operations approved passenger rebooking."
            ),
            (
                "user",
                "Passengers were moved to the next available flight."
            ),

            # Tool-heavy noise
            *[
                (
                    "tool",
                    build_long_tool_output(
                        "Cancellation operations",
                        i
                    )
                )
                for i in range(1, 31)
            ],

            (
                "tool",
                "Rebooking database synchronized."
            ),
            (
                "tool",
                "Passenger manifest refreshed."
            ),
            (
                "tool",
                "Airport departure board synchronized."
            ),

            # Final question
            (
                "user",
                "Why was BH512 cancelled?"
            ),
        ],

        "expected_keywords": [
            "BH512",
            "cancelled",
            "safety",
        ],
    },
]


# ============================================================
# Build Context
# ============================================================

def build_context(messages, window_size=10, recent_size=5):

    manager = ContextManager(
        window_size=window_size,
        recent_size=recent_size
    )

    for role, content in messages:

        manager.add_message(
            role,
            content
        )

    return manager


# ============================================================
# Convert Strategy Output to Text
# ============================================================

def flatten_context(result):
    """
    Convert the output of any strategy into one text
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

            parts.append(
                result["summary"]
            )

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

def calculate_accuracy(
    context_text,
    expected_keywords
):
    """
    Calculate retrieval accuracy.

    Accuracy =
        preserved expected keywords
        /
        total expected keywords
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
    Model-independent token approximation.

    Rough approximation:
        1 token ~= 4 characters
    """

    return max(
        1,
        len(text) // 4
    )


# ============================================================
# Evaluate Strategy
# ============================================================

def evaluate_strategy(
    manager,
    strategy_name,
    expected_keywords
):

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

    context_text = flatten_context(
        result
    )

    accuracy = calculate_accuracy(
        context_text,
        expected_keywords
    )

    tokens = estimate_tokens(
        context_text
    )

    return {
        "strategy": strategy_name,
        "accuracy": round(
            accuracy,
            3
        ),
        "tokens": tokens,
        "latency_ms": round(
            latency_ms,
            3
        ),
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

        # Same original context for every strategy.
        manager = build_context(
            test_case["messages"],
            window_size=10,
            recent_size=5
        )

        for strategy in strategies:

            result = evaluate_strategy(
                manager,
                strategy,
                test_case["expected_keywords"]
            )

            result["test_case"] = (
                test_case["name"]
            )

            all_results.append(result)

    return all_results


# ============================================================
# Print Comparison Table
# ============================================================

def print_results(results):

    print()
    print("=" * 100)
    print("LONG-CONTEXT STRATEGY EVALUATION")
    print("=" * 100)

    print(
        f"{'Test Case':<35}"
        f"{'Strategy':<30}"
        f"{'Accuracy':<12}"
        f"{'Tokens':<10}"
        f"{'Latency(ms)':<12}"
    )

    print("-" * 100)

    for result in results:

        print(
            f"{result['test_case']:<35}"
            f"{result['strategy']:<30}"
            f"{result['accuracy']:<12}"
            f"{result['tokens']:<10}"
            f"{result['latency_ms']:<12}"
        )


# ============================================================
# Choose Best Strategy
# ============================================================

def choose_best_strategy(results):
    """
    Choose the best strategy using:

        Accuracy -> higher is better
        Tokens   -> lower is better
        Latency  -> lower is better

    Accuracy receives the highest weight.
    """

    strategy_scores = {}

    # --------------------------------------------------------
    # Group results by strategy
    # --------------------------------------------------------

    for result in results:

        strategy = result["strategy"]

        if strategy not in strategy_scores:

            strategy_scores[strategy] = {
                "accuracy": [],
                "tokens": [],
                "latency": []
            }

        strategy_scores[strategy]["accuracy"].append(
            result["accuracy"]
        )

        strategy_scores[strategy]["tokens"].append(
            result["tokens"]
        )

        strategy_scores[strategy]["latency"].append(
            result["latency_ms"]
        )

    # --------------------------------------------------------
    # Calculate averages
    # --------------------------------------------------------

    averages = {}

    for strategy, values in strategy_scores.items():

        averages[strategy] = {

            "accuracy":
                sum(values["accuracy"])
                / len(values["accuracy"]),

            "tokens":
                sum(values["tokens"])
                / len(values["tokens"]),

            "latency":
                sum(values["latency"])
                / len(values["latency"])
        }

    # --------------------------------------------------------
    # Normalization
    # --------------------------------------------------------

    max_accuracy = max(
        value["accuracy"]
        for value in averages.values()
    )

    min_tokens = min(
        value["tokens"]
        for value in averages.values()
    )

    max_tokens = max(
        value["tokens"]
        for value in averages.values()
    )

    min_latency = min(
        value["latency"]
        for value in averages.values()
    )

    max_latency = max(
        value["latency"]
        for value in averages.values()
    )

    # --------------------------------------------------------
    # Calculate scores
    # --------------------------------------------------------

    scores = {}

    for strategy, value in averages.items():

        # Accuracy: higher is better.
        accuracy_score = (
            value["accuracy"] / max_accuracy
            if max_accuracy > 0
            else 0
        )

        # Tokens: lower is better.
        if max_tokens == min_tokens:

            token_score = 1.0

        else:

            token_score = (
                (max_tokens - value["tokens"])
                / (max_tokens - min_tokens)
            )

        # Latency: lower is better.
        if max_latency == min_latency:

            latency_score = 1.0

        else:

            latency_score = (
                (max_latency - value["latency"])
                / (max_latency - min_latency)
            )

        # Accuracy is the most important metric.
        score = (
            0.50 * accuracy_score
            + 0.30 * token_score
            + 0.20 * latency_score
        )

        scores[strategy] = score

    # --------------------------------------------------------
    # Select best strategy
    # --------------------------------------------------------

    best_strategy = max(
        scores,
        key=scores.get
    )

    print()
    print("=" * 100)
    print("AVERAGE STRATEGY COMPARISON")
    print("=" * 100)

    print(
        f"{'Strategy':<30}"
        f"{'Avg Accuracy':<18}"
        f"{'Avg Tokens':<15}"
        f"{'Avg Latency(ms)':<18}"
    )

    print("-" * 100)

    for strategy, value in averages.items():

        print(
            f"{strategy:<30}"
            f"{value['accuracy']:<18.3f}"
            f"{value['tokens']:<15.1f}"
            f"{value['latency']:<18.3f}"
        )

    print()
    print("=" * 100)
    print("FINAL STRATEGY SCORES")
    print("=" * 100)

    for strategy, score in scores.items():

        print(
            f"{strategy:<35}"
            f"score = {score:.3f}"
        )

    print("-" * 100)

    print(
        f"Best Strategy: {best_strategy}"
    )

    return best_strategy


# ============================================================
# Main
# ============================================================

if __name__ == "__main__":

    results = run_evaluation()

    print_results(results)

    choose_best_strategy(results)
