class PromoteOrDropRouter:
    def __init__(self):
        self.important_keywords = {
            "flight",
            "aircraft",
            "crew",
            "maintenance",
            "delay",
            "cancel",
            "reschedule",
            "emergency",
            "decision",
            "incident",
            "backup",
        }

    def route(self, content, metadata=None):
        metadata = metadata or {}
        text = str(content).lower()

        matched_keywords = [
            keyword
            for keyword in self.important_keywords
            if keyword in text
        ]

        if matched_keywords:
            return {
                "action": "promote",
                "content": content,
                "metadata": metadata,
                "reason": (
                    "Operational information that may be useful "
                    "in future sessions."
                ),
                "matched_keywords": matched_keywords,
            }

        return {
            "action": "drop",
            "content": content,
            "metadata": metadata,
            "reason": (
                "Routine information with no identified "
                "future operational value."
            ),
            "matched_keywords": [],
        }
