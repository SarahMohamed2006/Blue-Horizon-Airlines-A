from mcp.server import elicitation

def build_cancel_flight_confirmation(
    flight_number: str,
    reason: str
):
    """
    Build confirmation data before cancelling a flight.
    """

    return {
        "flight_number": flight_number,
        "reason": reason,
        "message": (
            f"Flight {flight_number} will be cancelled.\n"
            f"Reason: {reason}\n\n"
            "Cancelling a flight may affect passengers and schedules.\n"
            "Do you want to continue?"
        )
    }

def build_aircraft_assignment_confirmation(
    flight_number: str,
    aircraft_id: int
):
    """
    Confirm assigning a replacement aircraft.
    """

    return {
        "flight_number": flight_number,
        "aircraft_id": aircraft_id,
        "message": (
            f"Aircraft {aircraft_id} will be assigned "
            f"to flight {flight_number}.\n"
            "Do you want to continue?"
        )
    }
def build_reschedule_confirmation(
    flight_number: str,
    new_departure: str,
    new_arrival: str
):
    """
    Confirm flight rescheduling.
    """

    return {
        "flight_number": flight_number,
        "new_departure": new_departure,
        "new_arrival": new_arrival,
        "message": (
            f"Flight {flight_number} will be rescheduled.\n"
            f"New departure: {new_departure}\n"
            f"New arrival: {new_arrival}\n\n"
            "Do you want to continue?"
        )
    }


def build_backup_crew_confirmation(
    flight_number: str,
    crew_id: int
):
    """
    Confirm assigning a backup crew member.
    """

    return {
        "flight_number": flight_number,
        "crew_id": crew_id,
        "message": (
            f"Crew member {crew_id} will be assigned "
            f"to flight {flight_number}.\n"
            "Do you want to continue?"
        )
    }









