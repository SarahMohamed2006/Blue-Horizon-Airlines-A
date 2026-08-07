from datetime import datetime


class SemanticMemory:
    def __init__(self):
        self.facts = {}

    def store(self, key, value, metadata=None):
        self.facts[key] = {
            "value": value,
            "metadata": metadata or {},
            "updated_at": datetime.utcnow()
        }

        return self.facts[key]

    def get(self, key):
        item = self.facts.get(key)

        if item is None:
            return None

        return item["value"]

    def get_record(self, key):
        return self.facts.get(key)

    def get_all(self):
        return dict(self.facts)

    def delete(self, key):
        self.facts.pop(key, None)

    def clear(self):
        self.facts.clear()
