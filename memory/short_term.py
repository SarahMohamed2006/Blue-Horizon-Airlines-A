from collections import deque
from datetime import datetime, timedelta


class ShortTermMemory:
    def __init__(self, max_size=20, expiration_minutes=30):
        self.max_size = max_size
        self.expiration_minutes = expiration_minutes
        self.items = deque(maxlen=max_size)

    def add(self, content, metadata=None):
        self.items.append({
            "content": content,
            "metadata": metadata or {},
            "created_at": datetime.utcnow()
        })

    def get_all(self):
        now = datetime.utcnow()
        valid_items = []

        for item in self.items:
            age = now - item["created_at"]

            if age <= timedelta(minutes=self.expiration_minutes):
                valid_items.append(item)

        self.items.clear()

        for item in valid_items:
            self.items.append(item)

        return list(self.items)

    def clear(self):
        self.items.clear()

    def size(self):
        return len(self.items)
