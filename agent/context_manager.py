from time import perf_counter


class ContextManager:
    """
    Long-context management for the Blue Horizon Airlines
    Operations Agent.

    Supported strategies:
        1. Sliding Window
        2. Observation Masking
        3. Recursive Summarization
        4. Zone-Based Pruning
    """

    def __init__(self, window_size=10, recent_size=5):
        if window_size <= 0:
            raise ValueError("window_size must be greater than 0")

        if recent_size <= 0:
            raise ValueError("recent_size must be greater than 0")

        self.window_size = window_size
        self.recent_size = recent_size

        # Keep the original conversation history.
        self.history = []

    # ============================================================
    # COMMON
    # ============================================================

    def add_message(self, role, content):
        """Add one observation to the conversation history."""

        if not isinstance(role, str):
            raise TypeError("role must be a string")

        if not isinstance(content, str):
            raise TypeError("content must be a string")

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

        Approximation:
            tokens ~= number of words * 1.3
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

        return list(self.history[-self.window_size:])

    # ============================================================
    # 2. OBSERVATION MASKING
    # ============================================================

    def observation_masking(self):
        """
        Mask sensitive information while preserving
        the conversation structure.
        """

        masked_context = []

        for message in self.history:

            text = str(message["content"])

            # Email
            text = text.replace("@", "[EMAIL]")

            # Egyptian phone prefix
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
        Compress older observations while preserving
        the most recent observations.
        """

        if len(self.history) <= self.recent_size:
            return list(self.history)

        old_messages = self.history[:-self.recent_size]
        recent_messages = self.history[-self.recent_size:]

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
        Preserve operationally important observations
        and recent observations.

        Critical information includes:
            - cancellation
            - delay
            - maintenance
            - emergency
            - aircraft
            - backup aircraft
            - crew
            - operational decisions
            - weather
            - rescheduling
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

            if any(
                keyword in text
                for keyword in critical_keywords
            ):
                critical.append(message)
            else:
                normal.append(message)

        # Always preserve recent observations.
        recent = self.history[-self.recent_size:]

        return {
            "important": critical,
            "recent": recent
        }

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

        tokens = self.estimate_tokens(
            result if isinstance(result, list)
            else (
                result.get("important", [])
                + result.get("recent", [])
            )
        )

        return {
            "strategy": strategy,
            "messages": (
                len(result)
                if isinstance(result, list)
                else len(result.get("important", []))
                + len(result.get("recent", []))
            ),
            "tokens": tokens,
            "latency_ms": round(latency * 1000, 4),
            "result": result
        }
