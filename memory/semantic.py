from datetime import datetime

from memory.expiration import MemoryExpiration
from memory.versioning import MemoryVersioning


class SemanticMemory:
    def __init__(self):
        self.facts = {}
        self.versioning = MemoryVersioning()
        self.expiration = MemoryExpiration()

    def store(self, key, value, metadata=None):
        metadata = metadata or {}

        version = self.versioning.save_version(key, value)

        record = {
            "value": value,
            "metadata": metadata,
            "version": version["version"],
            "created_at": version["created_at"],
            "updated_at": datetime.utcnow(),
            "status": "current",
        }

        self.facts[key] = record

        return record

    def get(self, key):
        record = self.get_record(key)

        if record is None:
            return None

        return record["value"]

    def get_record(self, key):
        record = self.facts.get(key)

        if record is None:
            return None

        ttl = record["metadata"].get("ttl_minutes")

        if ttl is not None:
            if self.expiration.is_expired(
                record["created_at"],
                ttl
            ):
                record["status"] = "expired"
                return None

        return record

    def get_all(self):
        return dict(self.facts)

    def get_history(self, key):
        return self.versioning.get_history(key)

    def delete(self, key):
        self.facts.pop(key, None)

    def clear(self):
        self.facts.clear()
        self.versioning.versions.clear()
