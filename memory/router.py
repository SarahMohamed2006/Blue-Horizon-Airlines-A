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
            "incident"
        }

    def should_promote(self, content):
        text = str(content).lower()

        return any(
            keyword in text
            for keyword in self.important_keywords
        )

    def route(self, content, metadata=None):
        if self.should_promote(content):
            return {
                "action": "promote",
                "content": content,
                "metadata": metadata or {}
            }

        return {
            "action": "drop",
            "content": content,
            "metadata": metadata or {}
        }
