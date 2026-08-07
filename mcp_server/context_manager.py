from collections import deque
from time import perf_counter


class ContextManager:
    """
    Long-context management for the Blue Horizon Airlines Operations Agent.

    Supported strategies:
        1. Sliding Window
        2. Observation Masking
        3. Recursive Summarization
        4. Zone-Based Pruning
    """

    def __init__(self, window_size=10, recent_size=5):
        self.window_size = window_size
        self.recent_size = recent_size
        self.history = []

    # ============================================================
    # COMMON
    # ============================================================

    def add_message(self, role, content):
        """Add one observation to the conversation history."""

        self.history.append({
            "role": role,
            "content": content
        })

    def clear(self):
        """Clear the current context."""

        self.history = []

    def get_history(self):
        """Return the complete context."""

        return list(self.history)

    # ============================================================
    # TOKEN ESTIMATION
    # ============================================================

    @staticmethod
    def estimate_tokens(messages):
        """
        Lightweight token estimation.

        We intentionally avoid requiring a tokenizer dependency.
        Approximation:
            tokens ≈ number of words * 1.3
        """

        text = " ".join(
            str(message.get("content", ""))
            for message in messages
        )

        words = text.split()

        return int(len(words) * 1.3)

    # ============================================================
    # 1. SLIDING WINDOW
    # ============================================================

    def sliding_window(self):
        """
        Keep only the most recent N observations.
        """

        return self.history[-self.window_size:]

    # ============================================================
    # 2. OBSERVATION MASKING
    # ============================================================

    def observation_masking(self):
        """
        Remove or mask sensitive / unnecessary observations
        while preserving the conversation structure.
        """

        masked_context = []

        for message in self.history:

            text = str(message["content"])

            # Email
            text = text.replace("@", "[EMAIL]")

            # Phone numbers
            text = text.replace("+20", "[PHONE]")

            # Payment information
            text = text.replace("Visa", "[CARD]")
            text = text.replace("MasterCard", "[CARD]")

            masked_context.append({
                "role": message["role"],
                "content": text
            })

        return masked_context

    # ============================================================
    # 3. RECURSIVE SUMMARIZATION
    # ============================================================

    def recursive_summarization(self):
        """
        Compress older observations while preserving recent context.

        The context is divided into:
            - old information
            - recent information

        Older information is recursively compressed into a summary.
        """

        if len(self.history) <= self.recent_size:
            return self.history

        old_messages = self.history[:-self.recent_size]
        recent_messages = self.history[-self.recent_size:]

        # Build a compact summary from old observations.
        summary_parts = []

        for message in old_messages:
            summary_parts.append(
                f"{message['role']}: {message['content']}"
            )

        summary_text = " | ".join(summary_parts)

        summary_message = {
            "role": "system",
            "content": (
                "Historical context summary: "
                + summary_text
            )
        }

        return [summary_message] + recent_messages

    # ============================================================
    # 4. ZONE-BASED PRUNING
    # ============================================================

    def zone_based_pruning(self):
        """
        Divide observations into importance zones.

        Critical:
            cancellation, emergency, maintenance, delay,
            aircraft, crew, operational decisions.

        Recent:
            latest observations.

        Normal:
            low-value observations.

        Critical information is always preserved.
        """

        critical = []
        normal = []

        critical_keywords = [
            "cancel",
            "cancelled",
            "cancellation",
            "delay",
            "delayed",
            "maintenance",
            "emergency",
            "aircraft",
            "backup",
            "crew",
            "assign",
            "assigned",
            "operational decision",
            "weather",
            "reschedule",
            "rescheduled"
        ]

        for message in self.history:

            text = str(message["content"]).lower()

            if any(keyword in text for keyword in critical_keywords):
                critical.append(message)
            else:
                normal.append(message)

        # Always preserve recent observations.
        recent = self.history[-self.recent_size:]

        # Avoid duplicates.
        result = []

        seen = set()

        for message in critical + recent:

            key = (
                message["role"],
                message["content"]
            )

            if key not in seen:
                result.append(message)
                seen.add(key)

        return result

    # ============================================================
    # STRATEGY SELECTOR
    # ============================================================

    def apply_strategy(self, strategy):
        """
        Apply one of the four context-management strategies.
        """

        strategies = {
            "sliding_window": self.sliding_window,
            "observation_masking": self.observation_masking,
            "recursive_summarization": self.recursive_summarization,
            "zone_based_pruning": self.zone_based_pruning,
        }

        if strategy not in strategies:
            raise ValueError(
                f"Unknown strategy: {strategy}"
            )

        return strategies[strategy]()

    # ============================================================
    # PERFORMANCE MEASUREMENT
    # ============================================================

    def evaluate_strategy(self, strategy):
        """
        Measure token count and latency for one strategy.
        """

        start = perf_counter()

        result = self.apply_strategy(strategy)

        latency = perf_counter() - start

        tokens = self.estimate_tokens(result)

        return {
            "strategy": strategy,
            "messages": len(result),
            "tokens": tokens,
            "latency_ms": round(latency * 1000, 4),
            "result": result
        }
