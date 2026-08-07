from datetime import datetime


class EpisodicMemory:
    def __init__(self):
        self.episodes = []

    def store(self, event, metadata=None):
        episode = {
            "event": event,
            "metadata": metadata or {},
            "created_at": datetime.utcnow()
        }

        self.episodes.append(episode)

        return episode

    def get_all(self):
        return list(self.episodes)

    def get_recent(self, limit=10):
        return self.episodes[-limit:]

    def clear(self):
        self.episodes.clear()
