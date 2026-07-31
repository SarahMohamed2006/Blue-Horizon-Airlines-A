from database import get_connection
from mcp.types import SamplingMessage, TextContent
from notifications import SessionState
from elicitation import confirm_cancel_flight
from mcp_app import mcp

# ---------------------------------------------------------------------------
# Assign Aircraft
# ---------------------------------------------------------------------------
@mcp.tool()
def assign_aircraft(flight_id: int, aircraft_id: int, employee_id: int):
    """
    Assign an available aircraft to a flight. Requires an authorized
    employee (Operations Manager or Dispatcher) AND a session that has
    authenticated via authenticate_manager (see notifications.py) — this
    tool is only meaningfully available after that session-level auth,
    which is what the tools/list_changed push signals to the client.
    """
    if not SessionState.is_manager_authenticated():
        return {"error": "This action requires an authenticated session. Call authenticate_manager first."}

    conn = get_connection()
    cursor = conn.cursor()

    # Check flight
    cursor.execute("""
        SELECT flight_id, status
        FROM Flights
        WHERE flight_id=?
    """, (flight_id,))
    flight = cursor.fetchone()

    if not flight:
        conn.close()
        return {"error": "Flight not found"}

    if flight["status"] == "Cancelled":
        conn.close()
        return {"error": "Cannot assign aircraft to a cancelled flight"}

    if flight["status"] == "Completed":
        conn.close()
        return {"error": "Flight already completed"}

    # Authorization
    cursor.execute("""
        SELECT role
        FROM Employees
        WHERE employee_id=?
    """, (employee_id,))
    employee = cursor.fetchone()

    if not employee:
        conn.close()
        return {"error": "Employee not found"}

    if employee["role"] not in ("Operations Manager", "Dispatcher"):
        conn.close()
        return {"error": "Unauthorized. Only Operations Manager or Dispatcher can assign aircraft."}

    # Check aircraft
    cursor.execute("""
        SELECT status
        FROM Aircraft
        WHERE aircraft_id=?
    """, (aircraft_id,))
    aircraft = cursor.fetchone()

    if not aircraft:
        conn.close()
        return {"error": "Aircraft not found"}

    if aircraft["status"] != "Available":
        conn.close()
        return {"error": "Aircraft is not available"}

    cursor.execute("""
        UPDATE Flights
        SET aircraft_id=?
        WHERE flight_id=?
    """, (aircraft_id, flight_id))

    cursor.execute("""
        INSERT INTO AircraftAssignments
            (flight_id, aircraft_id, assigned_at, assignment_reason)
        VALUES (?, ?, CURRENT_TIMESTAMP, 'Operational Assignment')
    """, (flight_id, aircraft_id))

    cursor.execute("""
        UPDATE Aircraft
        SET status='Assigned'
        WHERE aircraft_id=?
    """, (aircraft_id,))

    cursor.execute("""
        INSERT INTO FlightEvents
            (flight_id, event_type, severity, description, reported_at, status)
        VALUES (?, 'Aircraft Assigned', 'Low', 'Replacement aircraft assigned by operations.', CURRENT_TIMESTAMP, 'Closed')
    """, (flight_id,))

    conn.commit()
    conn.close()

    return {"success": True, "message": "Aircraft assigned successfully"}


# ---------------------------------------------------------------------------
# Assign Backup Crew
# ---------------------------------------------------------------------------
@mcp.tool()
def assign_backup_crew(flight_id: int, crew_id: int, employee_id: int):
    """
    Assign a crew member to a flight. Requires an authorized employee
    and an authenticated session.
    """
    if not SessionState.is_manager_authenticated():
        return {"error": "This action requires an authenticated session. Call authenticate_manager first."}

    conn = get_connection()
    cursor = conn.cursor()

    # Check flight
    cursor.execute("""
        SELECT flight_id, status
        FROM Flights
        WHERE flight_id=?
    """, (flight_id,))
    flight = cursor.fetchone()

    if not flight:
        conn.close()
        return {"error": "Flight not found"}

    if flight["status"] in ("Cancelled", "Completed"):
        conn.close()
        return {"error": "Cannot assign crew to this flight"}

    # Authorization
    cursor.execute("""
        SELECT role
        FROM Employees
        WHERE employee_id=?
    """, (employee_id,))
    employee = cursor.fetchone()

    if not employee:
        conn.close()
        return {"error": "Employee not found"}

    if employee["role"] not in ("Operations Manager", "Dispatcher"):
        conn.close()
        return {"error": "Unauthorized. Only Operations Manager or Dispatcher can assign crew."}

    # Check crew
    cursor.execute("""
        SELECT availability, hours_flown_today
        FROM Crew
        WHERE crew_id=?
    """, (crew_id,))
    crew = cursor.fetchone()

    if not crew:
        conn.close()
        return {"error": "Crew member not found"}

    if not crew["availability"]:
        conn.close()
        return {"error": "Crew member unavailable"}

    if crew["hours_flown_today"] >= 8:
        conn.close()
        return {"error": "Crew exceeded duty hours"}

    # Prevent duplicate assignment
    cursor.execute("""
        SELECT 1
        FROM FlightCrew
        WHERE flight_id=? AND crew_id=?
    """, (flight_id, crew_id))

    if cursor.fetchone():
        conn.close()
        return {"error": "Crew already assigned"}

    cursor.execute("""
        INSERT INTO FlightCrew (flight_id, crew_id)
        VALUES (?, ?)
    """, (flight_id, crew_id))

    cursor.execute("""
        INSERT INTO CrewAssignments
            (flight_id, crew_id, assigned_at, assignment_status)
        VALUES (?, ?, CURRENT_TIMESTAMP, 'Active')
    """, (flight_id, crew_id))

    cursor.execute("""
        UPDATE Crew
        SET availability=0
        WHERE crew_id=?
    """, (crew_id,))

    cursor.execute("""
        INSERT INTO FlightEvents
            (flight_id, event_type, severity, description, reported_at, status)
        VALUES (?, 'Backup Crew Assigned', 'Low', 'Backup crew assigned by Flight Operations.', CURRENT_TIMESTAMP, 'Closed')
    """, (flight_id,))

    conn.commit()
    conn.close()

    return {"success": True, "message": "Backup crew assigned successfully"}


# ---------------------------------------------------------------------------
# Reschedule Flight
# ---------------------------------------------------------------------------
@mcp.tool()
def reschedule_flight(flight_id: int, new_departure, new_arrival, employee_id: int):
    """
    Reschedule a flight's departure/arrival times. Requires an
    authorized employee and an authenticated session.
    """
    if not SessionState.is_manager_authenticated():
        return {"error": "This action requires an authenticated session. Call authenticate_manager first."}

    conn = get_connection()
    cursor = conn.cursor()

    # Check flight
    cursor.execute("""
        SELECT flight_id, status, departure_time
        FROM Flights
        WHERE flight_id=?
    """, (flight_id,))
    flight = cursor.fetchone()

    if not flight:
        conn.close()
        return {"error": "Flight not found"}

    if flight["status"] == "Cancelled":
        conn.close()
        return {"error": "Cancelled flights cannot be rescheduled"}

    if flight["status"] == "Completed":
        conn.close()
        return {"error": "Completed flights cannot be rescheduled"}

    # Authorization
    cursor.execute("""
        SELECT role
        FROM Employees
        WHERE employee_id=?
    """, (employee_id,))
    employee = cursor.fetchone()

    if not employee:
        conn.close()
        return {"error": "Employee not found"}

    if employee["role"] not in ("Operations Manager", "Dispatcher"):
        conn.close()
        return {"error": "Unauthorized. Only Operations Manager or Dispatcher can reschedule flights."}

    # Validate times
    if new_departure >= new_arrival:
        conn.close()
        return {"error": "Arrival time must be after departure time"}

    cursor.execute("""
        UPDATE Flights
        SET departure_time=?, arrival_time=?, status='Rescheduled'
        WHERE flight_id=?
    """, (new_departure, new_arrival, flight_id))

    cursor.execute("""
        INSERT INTO FlightEvents
            (flight_id, event_type, severity, description, reported_at, status)
        VALUES (?, 'Flight Rescheduled', 'Medium', 'Flight schedule updated by Operations Control.', CURRENT_TIMESTAMP, 'Closed')
    """, (flight_id,))

    conn.commit()
    conn.close()

    return {"success": True, "message": "Flight rescheduled successfully"}


# ---------------------------------------------------------------------------
# Cancel Flight
# ---------------------------------------------------------------------------
@mcp.tool()
async def cancel_flight(flight_id: int, employee_id: int, reason: str, ctx):
    """
    Cancel a flight. Requires Operations Manager authorization, an
    authenticated session, AND explicit human confirmation via
    elicitation/create before the cancellation is committed — this is
    the highest-stakes write tool (it directly affects passengers), so
    it's the one gated on a real elicitation pause rather than proceeding
    the moment authorization checks pass.
    """
    if not SessionState.is_manager_authenticated():
        return {"error": "This action requires an authenticated session. Call authenticate_manager first."}

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT flight_id, flight_number, status
        FROM Flights
        WHERE flight_id=?
    """, (flight_id,))
    flight = cursor.fetchone()

    if not flight:
        conn.close()
        return {"error": "Flight not found"}

    if flight["status"] == "Cancelled":
        conn.close()
        return {"error": "Flight already cancelled"}

    if flight["status"] == "Completed":
        conn.close()
        return {"error": "Completed flight cannot be cancelled"}

    cursor.execute("""
        SELECT role
        FROM Employees
        WHERE employee_id=?
    """, (employee_id,))
    employee = cursor.fetchone()

    if not employee:
        conn.close()
        return {"error": "Employee not found"}

    if employee["role"] != "Operations Manager":
        conn.close()
        return {"error": "Unauthorized. Only Operations Manager can cancel flights."}

    # --- Elicitation: pause for explicit human confirmation before committing ---
    confirmed = await confirm_cancel_flight(ctx, flight["flight_number"], reason)
    if not confirmed:
        conn.close()
        return {"error": "Cancellation not confirmed"}

    cursor.execute("""
        UPDATE Flights
        SET status='Cancelled'
        WHERE flight_id=?
    """, (flight_id,))

    cursor.execute("""
        INSERT INTO FlightEvents
            (flight_id, event_type, severity, description, reported_at, status)
        VALUES (?, 'Flight Cancelled', 'High', ?, CURRENT_TIMESTAMP, 'Closed')
    """, (flight_id, reason))

    conn.commit()
    conn.close()

    return {"success": True, "message": "Flight cancelled successfully"}


# ---------------------------------------------------------------------------
# Complete Maintenance
# ---------------------------------------------------------------------------
@mcp.tool()
def complete_maintenance(maintenance_id: int, employee_id: int):
    """
    Mark a maintenance record complete and return the aircraft to service.
    Requires Maintenance Engineer or Operations Manager authorization,
    and an authenticated session.
    """
    if not SessionState.is_manager_authenticated():
        return {"error": "This action requires an authenticated session. Call authenticate_manager first."}

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT maintenance_id, aircraft_id, status
        FROM Maintenance
        WHERE maintenance_id=?
    """, (maintenance_id,))
    maintenance = cursor.fetchone()

    if not maintenance:
        conn.close()
        return {"error": "Maintenance record not found"}

    if maintenance["status"] == "Completed":
        conn.close()
        return {"error": "Maintenance already completed"}

    cursor.execute("""
        SELECT role
        FROM Employees
        WHERE employee_id=?
    """, (employee_id,))
    employee = cursor.fetchone()

    if not employee:
        conn.close()
        return {"error": "Employee not found"}

    if employee["role"] not in ("Maintenance Engineer", "Operations Manager"):
        conn.close()
        return {"error": "Unauthorized. Only Maintenance Engineer or Operations Manager can close out maintenance."}

    cursor.execute("""
        UPDATE Maintenance
        SET status='Completed'
        WHERE maintenance_id=?
    """, (maintenance_id,))

    cursor.execute("""
        UPDATE Aircraft
        SET status='Available'
        WHERE aircraft_id=?
    """, (maintenance["aircraft_id"],))

    cursor.execute("""
        INSERT INTO FlightEvents
            (flight_id, event_type, severity, description, reported_at, status)
        SELECT flight_id, 'Maintenance Completed', 'Low', 'Aircraft maintenance completed.', CURRENT_TIMESTAMP, 'Closed'
        FROM Flights
        WHERE aircraft_id=?
        LIMIT 1
    """, (maintenance["aircraft_id"],))

    conn.commit()
    conn.close()

    return {"success": True, "message": "Maintenance completed successfully"}


# ---------------------------------------------------------------------------
# Record Operation Decision
#
# SAMPLING: before saving, this asks the CLIENT's model (via
# ctx.session.create_message, i.e. sampling/createMessage) to produce a
# short risk assessment of the decision. This is genuine reasoning the
# server itself doesn't do — the server has no LLM of its own here, and
# an employee's typed `reason` isn't checked against anything. The
# generated assessment is stored alongside the decision so a later
# reviewer sees both what the employee said and an independent read on
# risk, rather than trusting the free-text reason at face value.
# ---------------------------------------------------------------------------
@mcp.tool()
async def create_operation_decision(flight_id: int, employee_id: int, decision: str, reason: str, ctx):
    """
    Record an operational decision for a flight (audit trail only —
    does not execute the decision; see resolve_operational_issue).
    """
    if not SessionState.is_manager_authenticated():
    return {
        "error": "This action requires an authenticated session."
    }
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT status
        FROM Flights
        WHERE flight_id=?
    """, (flight_id,))
    flight = cursor.fetchone()

    if not flight:
        conn.close()
        return {"error": "Flight not found"}

    cursor.execute("""
        SELECT role
        FROM Employees
        WHERE employee_id=?
    """, (employee_id,))
    employee = cursor.fetchone()

    if not employee:
        conn.close()
        return {"error": "Employee not found"}

    allowed_roles = ["Operations Manager", "Flight Operations Officer"]
    if employee["role"] not in allowed_roles:
        conn.close()
        return {"error": "Unauthorized employee"}

    allowed_decisions = [
        "Cancel Flight",
        "Reschedule Flight",
        "Assign Backup Aircraft",
        "Assign Backup Crew",
        "Delay Flight",
        "Continue Operations",
    ]

    if decision not in allowed_decisions:
        conn.close()
        return {"error": "Invalid operational decision"}

    # --- Sampling: ask the client's model for an independent risk read ---
    risk_assessment = ""
    try:
        sampling_result = await ctx.session.create_message(
            messages=[
                SamplingMessage(
                    role="user",
                    content=TextContent(
                        type="text",
                        text=(
                            f"An airline operations decision is being recorded.\n"
                            f"Flight ID: {flight_id}\n"
                            f"Decision: {decision}\n"
                            f"Employee-stated reason: {reason}\n\n"
                            "In 2-3 sentences, assess the operational risk of this "
                            "decision and note anything the stated reason does not "
                            "address (e.g. passenger impact, downstream schedule "
                            "effects, crew duty limits)."
                        ),
                    ),
                )
            ],
            max_tokens=200,
        )
        if sampling_result.content.type == "text":
            risk_assessment = sampling_result.content.text
    except Exception as exc:
        # Client may not support sampling, or may decline. Don't block the
        # decision on it — record that no assessment was available.
        risk_assessment = f"(risk assessment unavailable: {exc})"

    cursor.execute("""
        INSERT INTO OperationDecisions
            (flight_id, employee_id, decision, reason, risk_assessment, created_at)
        VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
    """, (flight_id, employee_id, decision, reason, risk_assessment))

    conn.commit()
    conn.close()

    return {
        "success": True,
        "message": "Operation decision recorded",
        "risk_assessment": risk_assessment,
    }


# ---------------------------------------------------------------------------
# Send Notification
# ---------------------------------------------------------------------------
@mcp.tool()
def send_notification(flight_id: int, recipient: str, message: str):
    """
    Queue a notification related to a flight.
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO Notifications
            (flight_id, recipient, message, sent_at, status)
        VALUES (?, ?, ?, CURRENT_TIMESTAMP, 'Pending')
    """, (flight_id, recipient, message))

    conn.commit()
    conn.close()

    return {"success": True, "message": "Notification created"}


# ---------------------------------------------------------------------------
# Resolve Operational Issue
#
# NOTE: this now delegates to the single-purpose functions above instead
# of re-implementing their logic inline, so there is exactly one place
# each business rule (auth, validation, state transition) lives.
# ---------------------------------------------------------------------------
@mcp.tool()
async def resolve_operational_issue(flight_id: int, employee_id: int, issue_type: str, decision: str, reason: str, ctx):
    """
    Resolve an operational issue by executing the selected action
    and recording the decision. Delegates to the specific action
    functions so validation/authorization logic isn't duplicated.
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT flight_id
        FROM Flights
        WHERE flight_id = ?
    """, (flight_id,))

    if not cursor.fetchone():
        conn.close()
        return {"error": "Flight not found"}
    conn.close()

    if decision == "Cancel Flight":
        result = await cancel_flight(flight_id, employee_id, reason, ctx)

    elif decision == "Reschedule Flight":
        # Reschedule requires explicit new times; this generic resolver
        # cannot invent them, so it reports that the caller needs to use
        # reschedule_flight directly with new_departure/new_arrival.
        return {"error": "Reschedule requires new_departure/new_arrival — call reschedule_flight directly"}

    elif decision == "Assign Backup Aircraft":
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT aircraft_id
            FROM Aircraft
            WHERE status='Available'
            LIMIT 1
        """)
        aircraft = cursor.fetchone()
        conn.close()

        if not aircraft:
            return {"error": "No available aircraft"}

        result = assign_aircraft(flight_id, aircraft["aircraft_id"], employee_id)

    elif decision == "Assign Backup Crew":
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT crew_id
            FROM Crew
            WHERE availability=1
            LIMIT 1
        """)
        crew = cursor.fetchone()
        conn.close()

        if not crew:
            return {"error": "No available crew"}

        result = assign_backup_crew(flight_id, crew["crew_id"], employee_id)

    else:
        return {"error": "Unknown decision"}

    if "error" in result:
        return result

    # Save the operation decision for audit purposes
    decision_result = await create_operation_decision(flight_id, employee_id, decision, reason, ctx)
    if "error" in decision_result:
        return decision_result

    return {
        "success": True,
        "issue_type": issue_type,
        "decision": decision,
        "reason": reason,
    }


# ---------------------------------------------------------------------------
# Generate Operations Report
#
# PROGRESS TRACKING: this pulls full status (flight, aircraft, crew,
# destination weather) for every non-completed, non-cancelled flight.
# For a large operation this is genuinely slow — several queries per
# flight, not one lookup — so instead of blocking with no feedback until
# the whole thing finishes, it reports progress after each flight via
# ctx.report_progress(). A client that included a progress token in its
# request sees live updates; one that didn't just gets the final result,
# so this degrades safely for clients without progress support.
# ---------------------------------------------------------------------------
@mcp.tool()
async def generate_operations_report(ctx):
    """
    Build a full operations snapshot across all active flights,
    reporting progress as each flight is processed.
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT flight_id, flight_number, destination_airport_id, aircraft_id
        FROM Flights
        WHERE status NOT IN ('Completed', 'Cancelled')
        ORDER BY flight_id
    """)
    flights = cursor.fetchall()
    conn.close()

    total = len(flights)
    report = []

    for i, flight in enumerate(flights, start=1):
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT tail_number, model, status
            FROM Aircraft
            WHERE aircraft_id=?
        """, (flight["aircraft_id"],))
        aircraft = cursor.fetchone()

        cursor.execute("""
            SELECT c.name, c.role
            FROM Crew c
            JOIN FlightCrew fc ON c.crew_id = fc.crew_id
            WHERE fc.flight_id=?
        """, (flight["flight_id"],))
        crew = cursor.fetchall()

        cursor.execute("""
            SELECT weather, runway_status
            FROM Airports
            WHERE airport_id=?
        """, (flight["destination_airport_id"],))
        weather = cursor.fetchone()

        conn.close()

        report.append({
            "flight_number": flight["flight_number"],
            "aircraft": dict(aircraft) if aircraft else None,
            "crew": [dict(c) for c in crew],
            "destination_weather": dict(weather) if weather else None,
        })

        await ctx.report_progress(
            progress=i,
            total=total,
            message=f"Processed flight {flight['flight_number']} ({i}/{total})",
        )

    return {
        "success": True,
        "flights_processed": total,
        "report": report,
    }
