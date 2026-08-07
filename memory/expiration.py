from datetime import datetime, timedelta


class MemoryExpiration:
    def __init__(self, default_ttl_minutes=30):
        self.default_ttl_minutes = default_ttl_minutes

    def is_expired(self, created_at, ttl_minutes=None):
        ttl = ttl_minutes or self.default_ttl_minutes

        return datetime.utcnow() - created_at > timedelta(
            minutes=ttl
        )

    def filter_valid(self, items, ttl_minutes=None):
        return [
            item
            for item in items
            if not self.is_expired(
                item["created_at"],
                ttl_minutes
            )
        ]
