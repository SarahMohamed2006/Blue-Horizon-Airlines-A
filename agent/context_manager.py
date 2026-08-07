from time import perf_counter


class ContextManager:
    """
    Long-context management for the Blue Horizon Airlines
    Operations Agent.

    Supported strategies:
        1. Sliding Window
        2. Observation and Tool-Output Masking
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

        # Keep the complete original history.
        # Every strategy works on the same context.
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

        return max(1, int(len(words) * 1.3))

    # ============================================================
    # 1. SLIDING WINDOW
    # ============================================================

    def sliding_window(self):
        """
        Keep only the most recent N observations.
        """

        return list(self.history[-self.window_size:])

    # ============================================================
    # 2. OBSERVATION AND TOOL-OUTPUT MASKING
    # ============================================================

    def observation_masking(self):
        """
        Mask unnecessary/sensitive observation details and
        large tool outputs while preserving useful information.

        Tool outputs are detected when the role is 'tool'.
        Large tool-output content is replaced by a compact marker.

        Sensitive information such as emails, phone numbers,
        and payment-card names is also masked.
        """

        masked_context = []

        for message in self.history:

            role = message["role"]
            text = str(message["content"])

            # ----------------------------------------------------
            # Sensitive information masking
            # ----------------------------------------------------

            text = text.replace("@", "[EMAIL]")

            text = text.replace("+20", "[PHONE]")

            text = text.replace("Visa", "[CARD]")
            text = text.replace("VISA", "[CARD]")

            text = text.replace("MasterCard", "[CARD]")
            text = text.replace("MASTERCARD", "[CARD]")

            # ----------------------------------------------------
            # Tool-output masking
            # ----------------------------------------------------

            if role.lower() == "tool":

                # Keep short tool outputs because they may contain
                # useful operational information.
                if len(text) > 300:
                    text = (
                        "[MASKED TOOL OUTPUT] "
                        "Large tool output removed to reduce "
                        "context size."
                    )

            masked_context.append({
                "role": role,
                "content": text
            })

        return masked_context

    # ============================================================
    # 3. RECURSIVE SUMMARIZATION
    # ============================================================

    def recursive_summarization(self):
        """
        Compress older observations into one historical summary
        while preserving the most recent observations.
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
        Divide context into:

            important:
                operationally critical observations

            recent:
                most recent observations

        Critical operational information is preserved.
        """

        important = []

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
            "rescheduled",
            "divert",
            "diverted",
            "gate",
            "safety",
            "fuel",
            "outage",
            "closure"
        ]

        for message in self.history:

            text = str(message["content"]).lower()

            if any(
                keyword in text
                for keyword in critical_keywords
            ):
                important.append(message)

        # Always preserve recent observations.
        recent = list(
            self.history[-self.recent_size:]
        )

        # Remove duplicates from important zone.
        unique_important = []

        seen = set()

        for message in important:

            key = (
                message["role"],
                message["content"]
            )

            if key not in seen:

                unique_important.append(message)

                seen.add(key)

        return {
            "important": unique_important,
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

        if isinstance(result, dict):

            messages = []

            if "important" in result:
                messages.extend(result["important"])

            if "recent" in result:
                messages.extend(result["recent"])

        else:
            messages = result

        tokens = self.estimate_tokens(messages)

        return {
            "strategy": strategy,
            "messages": len(messages),
            "tokens": tokens,
            "latency_ms": round(
                latency * 1000,
                4
            ),
            "result": result
        }
