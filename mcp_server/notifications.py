
"""
Notification helpers for Blue Horizon Flight Operations.
"""

def flight_cancelled(flight_number: str):
    return {
        "event": "flight.cancelled",
        "message": "Flight cancelled successfully.",
        "flight_number": flight_number,
    }


def flight_rescheduled(flight_number: str):
    return {
        "event": "flight.rescheduled",
        "message": "Flight rescheduled successfully.",
        "flight_number": flight_number,
    }


def aircraft_assigned(flight_number: str, aircraft_id: int):
    return {
        "event": "aircraft.assigned",
        "message": "Aircraft assigned successfully.",
        "flight_number": flight_number,
        "aircraft_id": aircraft_id,
    }


def backup_crew_assigned(flight_number: str, crew_id: int):
    return {
        "event": "crew.assigned",
        "message": "Backup crew assigned successfully.",
        "flight_number": flight_number,
        "crew_id": crew_id,
    }


def maintenance_completed(maintenance_id: int):
    return {
        "event": "maintenance.completed",
        "message": "Maintenance completed successfully.",
        "maintenance_id": maintenance_id,
    }


def operation_decision_recorded(decision_id: int):
    return {
        "event": "operation.decision.recorded",
        "message": "Operation decision recorded successfully.",
        "decision_id": decision_id,
    }


def notification_sent(recipient: str):
    return {
        "event": "notification.sent",
        "message": "Notification sent successfully.",
        "recipient": recipient,
    }
