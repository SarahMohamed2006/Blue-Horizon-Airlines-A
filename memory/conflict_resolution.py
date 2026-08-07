from datetime import datetime


class ConflictResolution:
    def resolve(self, old_value, new_value):
        if old_value == new_value:
            return old_value

        return new_value

    def resolve_records(self, old_record, new_record):
        if old_record is None:
            return new_record

        if new_record is None:
            return old_record

        old_time = old_record.get("updated_at")
        new_time = new_record.get("updated_at")

        if old_time is None or new_time is None:
            return new_record

        if new_time >= old_time:
            return new_record

        return old_record 
