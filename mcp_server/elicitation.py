"""
Elicitation helpers for Blue Horizon Flight Operations.

Each function here actually invokes elicitation/create via FastMCP's
ctx.elicit(...) and returns the human's decision. Call these from
inside an async tool handler (which must accept a `ctx: Context`
parameter) and gate the write action on the result — don't just
build a message and proceed regardless.
"""

from pydantic import BaseModel
from mcp.server.fastmcp import Context


class ConfirmResponse(BaseModel):
    confirm: bool


async def confirm_cancel_flight(ctx: Context, flight_number: str, reason: str) -> bool:
    """
    Pause and ask a human to confirm cancelling a flight.
    Returns True only if the human explicitly accepted and confirmed.
    """
    result = await ctx.elicit(
        message=(
            f"Flight {flight_number} will be cancelled.\n"
            f"Reason: {reason}\n\n"
            "Cancelling a flight may affect passengers and schedules.\n"
            "Do you want to continue?"
        ),
        schema=ConfirmResponse,
    )

    if result.action != "accept":
        return False

    return bool(result.data.confirm)


async def confirm_aircraft_assignment(ctx: Context, flight_number: str, aircraft_id: int) -> bool:
    """
    Pause and ask a human to confirm assigning a replacement aircraft.
    """
    result = await ctx.elicit(
        message=(
            f"Aircraft {aircraft_id} will be assigned to flight {flight_number}.\n"
            "Do you want to continue?"
        ),
        schema=ConfirmResponse,
    )

    if result.action != "accept":
        return False

    return bool(result.data.confirm)


async def confirm_reschedule(ctx: Context, flight_number: str, new_departure: str, new_arrival: str) -> bool:
    """
    Pause and ask a human to confirm rescheduling a flight.
    """
    result = await ctx.elicit(
        message=(
            f"Flight {flight_number} will be rescheduled.\n"
            f"New departure: {new_departure}\n"
            f"New arrival: {new_arrival}\n\n"
            "Do you want to continue?"
        ),
        schema=ConfirmResponse,
    )

    if result.action != "accept":
        return False

    return bool(result.data.confirm)


async def confirm_backup_crew(ctx: Context, flight_number: str, crew_id: int) -> bool:
    """
    Pause and ask a human to confirm assigning a backup crew member.
    """
    result = await ctx.elicit(
        message=(
            f"Crew member {crew_id} will be assigned to flight {flight_number}.\n"
            "Do you want to continue?"
        ),
        schema=ConfirmResponse,
    )

    if result.action != "accept":
        return False

    return bool(result.data.confirm)
