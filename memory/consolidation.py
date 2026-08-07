class ConsolidationLayer:
    def __init__(self, episodic_memory, semantic_memory):
        self.episodic_memory = episodic_memory
        self.semantic_memory = semantic_memory

    def consolidate(self):
        promoted = 0

        for episode in self.episodic_memory.get_all():
            metadata = episode.get("metadata", {})
            key = metadata.get("key")

            if not key:
                continue

            self.semantic_memory.store(
                key,
                episode["event"],
                metadata
            )

            promoted += 1

        return promoted
