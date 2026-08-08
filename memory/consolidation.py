from memory.conflict_resolution import ConflictResolution


class ConsolidationLayer:
    def __init__(self, episodic_memory, semantic_memory):
        self.episodic_memory = episodic_memory
        self.semantic_memory = semantic_memory
        self.conflict_resolution = ConflictResolution()

    def consolidate(self):
        consolidated = 0

        for episode in self.episodic_memory.get_all():
            metadata = episode.get("metadata", {})
            key = metadata.get("key")

            if not key:
                continue

            current = self.semantic_memory.get_record(key)

            new_record = {
                "value": episode["event"],
                "updated_at": episode["created_at"],
                "metadata": metadata,
            }

            if current is None:
                self.semantic_memory.store(
                    key,
                    episode["event"],
                    metadata
                )
                consolidated += 1
                continue

            resolved = self.conflict_resolution.resolve_records(
                current,
                new_record
            )

            if resolved["value"] != current["value"]:
                current["status"] = "superseded"

                self.semantic_memory.store(
                    key,
                    resolved["value"],
                    resolved.get("metadata", metadata)
                )

                consolidated += 1

        return consolidated
