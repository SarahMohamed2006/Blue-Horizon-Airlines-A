from collections import deque


class ContextManager:
    def __init__(self, window_size=10):
        self.window_size = window_size
        self.history = deque(maxlen=window_size)

    
    # Sliding Window
    
    def add_message(self, role, content):
        self.history.append({
            "role": role,
            "content": content
        })

    def sliding_window(self):
        return list(self.history)

    
    # Observation Masking
    
    def observation_masking(self):
        masked = []

        for item in self.history:
            text = item["content"]

            text = text.replace("@", "[EMAIL]")
            text = text.replace("+20", "[PHONE]")
            text = text.replace("Visa", "[CARD]")

            masked.append({
                "role": item["role"],
                "content": text
            })

        return masked

    
    # Recursive Summarization
    
    def recursive_summary(self):
        if len(self.history) <= 5:
            return list(self.history)

        summary = []

        for item in list(self.history)[:-5]:
            summary.append(item["content"])

        return {
            "summary":
                " | ".join(summary),
            "recent":
                list(self.history)[-5:]
        }

    
    # Zone Based Pruning
    
    def zone_based_pruning(self):

        important = []
        recent = []

        for item in self.history:

            if any(word in item["content"].lower() for word in [
                "cancel",
                "delay",
                "maintenance",
                "emergency",
                "assign"
            ]):
                important.append(item)
            else:
                recent.append(item)

        return {
            "important": important,
            "recent": recent[-5:]
        }