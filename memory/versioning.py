from datetime import datetime


class MemoryVersioning:
    def __init__(self):
        self.versions = {}

    def save_version(self, key, value):
        if key not in self.versions:
            self.versions[key] = []

        version = {
            "version": len(self.versions[key]) + 1,
            "value": value,
            "created_at": datetime.utcnow()
        }

        self.versions[key].append(version)

        return version

    def get_current(self, key):
        versions = self.versions.get(key, [])

        if not versions:
            return None

        return versions[-1]

    def get_history(self, key):
        return list(self.versions.get(key, []))
