"""
Notification helpers for Blue Horizon Flight Operations.

Two different things live in this file, and they are NOT the same
concept even though both are called "notifications":

1. Event payloads (below) — plain dicts describing something that
   happened. These are NOT MCP protocol notifications. No client
   ever receives these directly; they're used as the `message`
   content when writing a row to the Notifications table via
   send_notification() in tools.py. Keep using them for that.

2. session_state / notify_tools_changed (bottom of file) — this is
   the real MCP notification. It tracks whether the current session
   has authenticated as an Operations Manager, and pushes an actual
   `notifications/tools/list_changed` message when that changes,
   so write tools (cancel_flight, assign_aircraft, etc.) appear for
   the client without a reconnect.
"""


# ---------------------------------------------------------------------------
# Event payloads — used as Notifications table content, not protocol messages
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Real tools/list_changed notification
#
# Trigger: a session starts read-only. Calling authenticate_manager()
# with a valid Operations Manager employee_id flips session_state and
# pushes a genuine notifications/tools/list_changed message so write
# tools appear without the client reconnecting.
#
# NOTE: this uses ctx.session.send_notification(...) with a raw
# ToolListChangedNotification, which is the low-level call available
# on any MCP server session regardless of FastMCP version. If your
# installed FastMCP version exposes a higher-level helper (some do,
# e.g. ctx.session.send_tool_list_changed()), you can swap to that —
# check `python -c "from mcp.server.session import ServerSession;
# print([m for m in dir(ServerSession) if 'tool' in m.lower()])"`
# against your actual installed package to confirm which is available.
# ---------------------------------------------------------------------------

from database import get_connection
from mcp.types import ToolListChangedNotification, ServerNotification


class SessionState:
    """
    Tracks per-server authentication state.
    NOTE: this is a simple module-level flag suitable for a single-session
    stdio demo. For real multi-client streamable-HTTP use, this needs to
    be keyed per session (e.g. by ctx.session or a session id) instead of
    being global.
    """
    authenticated_manager_id: int | None = None

    @classmethod
    def is_manager_authenticated(cls) -> bool:
        return cls.authenticated_manager_id is not None


async def authenticate_manager(employee_id: int, ctx) -> dict:
    """
    Authenticate an Operations Manager for this session. On success,
    flips session state and pushes a real tools/list_changed
    notification so write tools become available.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT role FROM Employees WHERE employee_id=?", (employee_id,))
    employee = cursor.fetchone()
    conn.close()

    if not employee:
        return {"error": "Employee not found"}

    if employee["role"] != "Operations Manager":
        return {"error": "Only an Operations Manager can authenticate for elevated access"}

    SessionState.authenticated_manager_id = employee_id
    await notify_tools_changed(ctx)

    return {"success": True, "message": "Authenticated. Write tools are now available."}


def deauthenticate_manager():
    """Clear elevated session state (e.g. on logout/session end)."""
    SessionState.authenticated_manager_id = None


async def notify_tools_changed(ctx):
    """
    Push the actual notifications/tools/list_changed protocol message.
    """
    await ctx.session.send_notification(
        ServerNotification(ToolListChangedNotification(method="notifications/tools/list_changed"))
    )
