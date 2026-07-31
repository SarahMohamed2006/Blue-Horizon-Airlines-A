from database import get_connection


# Assign Aircraft

def assign_aircraft(flight_id: int, aircraft_id: int):

    conn = get_connection()
    cursor = conn.cursor()

    # Check flight
    cursor.execute("""
    SELECT
        flight_id,
        status
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
    (
        flight_id,
        aircraft_id,
        assigned_at,
        assignment_reason
    )
    VALUES
    (
        ?,
        ?,
        CURRENT_TIMESTAMP,
        'Operational Assignment'
    )
""", (
    flight_id,
    aircraft_id
))

    cursor.execute("""
        UPDATE Aircraft
        SET status='Assigned'
        WHERE aircraft_id=?
    """, (aircraft_id,))
    cursor.execute("""
    INSERT INTO FlightEvents
    (
        flight_id,
        event_type,
        severity,
        description,
        reported_at,
        status
    )
    VALUES
    (
        ?,
        'Aircraft Assigned',
        'Low',
        'Replacement aircraft assigned by operations.',
        CURRENT_TIMESTAMP,
        'Closed'
    )
""", (flight_id,))

    conn.commit()
    conn.close()

    return {
        "success": True,
        "message": "Aircraft assigned successfully"
    }


# Assign Backup Crew
def assign_backup_crew(
    flight_id: int,
    crew_id: int
):

    conn = get_connection()
    cursor = conn.cursor()

    # Check flight

    cursor.execute("""
        SELECT
            flight_id,
            status
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

    # Check crew

    cursor.execute("""
        SELECT
            availability,
            hours_flown_today
        FROM Crew
        WHERE crew_id=?
    """, (crew_id,))

    crew = cursor.fetchone()

    if not crew:
        conn.close()
        return {"error": "Crew member not found"}

    if crew["availability"] == 0:
        conn.close()
        return {"error": "Crew member unavailable"}

    if crew["hours_flown_today"] >= 8:
        conn.close()
        return {"error": "Crew exceeded duty hours"}

    # Prevent duplicate assignment

    cursor.execute("""
        SELECT *
        FROM FlightCrew
        WHERE flight_id=? AND crew_id=?
    """, (flight_id, crew_id))

    if cursor.fetchone():
        conn.close()
        return {"error": "Crew already assigned"}

    # Assign crew

    cursor.execute("""
        INSERT INTO FlightCrew
        (
            flight_id,
            crew_id
        )
        VALUES
        (
            ?,
            ?
        )
    """, (
        flight_id,
        crew_id
    ))

    cursor.execute("""
        INSERT INTO CrewAssignments
        (
            flight_id,
            crew_id,
            assigned_at,
            assignment_status
        )
        VALUES
        (
            ?,
            ?,
            CURRENT_TIMESTAMP,
            'Active'
        )
    """, (
        flight_id,
        crew_id
    ))

    cursor.execute("""
        UPDATE Crew
        SET availability=0
        WHERE crew_id=?
    """, (crew_id,))

    cursor.execute("""
        INSERT INTO FlightEvents
        (
            flight_id,
            event_type,
            severity,
            description,
            reported_at,
            status
        )
        VALUES
        (
            ?,
            'Backup Crew Assigned',
            'Low',
            'Backup crew assigned by Flight Operations.',
            CURRENT_TIMESTAMP,
            'Closed'
        )
    """, (flight_id,))

    conn.commit()
    conn.close()

    return {
        "success": True,
        "message": "Backup crew assigned successfully"
    }

# Reschedule Flight
def reschedule_flight(
    flight_id: int,
    new_departure,
    new_arrival
):

    conn = get_connection()
    cursor = conn.cursor()

    # Check flight

    cursor.execute("""
        SELECT
            flight_id,
            status,
            departure_time
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

    # Validate times

    if new_departure >= new_arrival:
        conn.close()
        return {
            "error": "Arrival time must be after departure time"
        }

    # Update schedule

    cursor.execute("""
        UPDATE Flights
        SET
            departure_time=?,
            arrival_time=?,
            status='Rescheduled'
        WHERE flight_id=?
    """, (
        new_departure,
        new_arrival,
        flight_id
    ))

    # Record event

    cursor.execute("""
        INSERT INTO FlightEvents
        (
            flight_id,
            event_type,
            severity,
            description,
            reported_at,
            status
        )
        VALUES
        (
            ?,
            'Flight Rescheduled',
            'Medium',
            'Flight schedule updated by Operations Control.',
            CURRENT_TIMESTAMP,
            'Closed'
        )
    """, (flight_id,))

    conn.commit()
    conn.close()

    return {
        "success": True,
        "message": "Flight rescheduled successfully"
    }


# Cancel Flight
def cancel_flight(
    flight_id: int,
    employee_id: int,
    reason: str
):

    conn = get_connection()
    cursor = conn.cursor()

    # Check flight

    cursor.execute("""
        SELECT
            flight_id,
            status
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

    if employee["role"] != "Operations Manager":
        conn.close()
        return {
            "error": "Unauthorized. Only Operations Manager can cancel flights."
        }

    # Cancel flight

    cursor.execute("""
        UPDATE Flights
        SET status='Cancelled'
        WHERE flight_id=?
    """, (flight_id,))

    # Save event

    cursor.execute("""
        INSERT INTO FlightEvents
        (
            flight_id,
            event_type,
            severity,
            description,
            reported_at,
            status
        )
        VALUES
        (
            ?,
            'Flight Cancelled',
            'High',
            ?,
            CURRENT_TIMESTAMP,
            'Closed'
        )
    """, (
        flight_id,
        reason
    ))

    conn.commit()
    conn.close()

    return {
        "success": True,
        "message": "Flight cancelled successfully"
    }



# Complete Maintenance
def complete_maintenance(
    maintenance_id: int
):

    conn = get_connection()
    cursor = conn.cursor()

    # Check maintenance record

    cursor.execute("""
        SELECT
            maintenance_id,
            aircraft_id,
            status
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

    # Complete maintenance

    cursor.execute("""
        UPDATE Maintenance
        SET status='Completed'
        WHERE maintenance_id=?
    """, (maintenance_id,))

    # Aircraft becomes available

    cursor.execute("""
        UPDATE Aircraft
        SET status='Available'
        WHERE aircraft_id=?
    """, (maintenance["aircraft_id"],))

    # Record event

    cursor.execute("""
        INSERT INTO FlightEvents
        (
            flight_id,
            event_type,
            severity,
            description,
            reported_at,
            status
        )
        SELECT
            flight_id,
            'Maintenance Completed',
            'Low',
            'Aircraft maintenance completed.',
            CURRENT_TIMESTAMP,
            'Closed'
        FROM Flights
        WHERE aircraft_id=?
        LIMIT 1
    """, (maintenance["aircraft_id"],))

    conn.commit()
    conn.close()

    return {
        "success": True,
        "message": "Maintenance completed successfully"
    }

# Record Operation Decision

def create_operation_decision(
    flight_id: int,
    employee_id: int,
    decision: str,
    reason: str
):

    conn = get_connection()
    cursor = conn.cursor()

    # Check flight

    cursor.execute("""
        SELECT status
        FROM Flights
        WHERE flight_id=?
    """, (flight_id,))

    flight = cursor.fetchone()

    if not flight:
        conn.close()
        return {"error": "Flight not found"}

    # Check employee

    cursor.execute("""
        SELECT role
        FROM Employees
        WHERE employee_id=?
    """, (employee_id,))

    employee = cursor.fetchone()

    if not employee:
        conn.close()
        return {"error": "Employee not found"}

    # Authorization

    allowed_roles = [
        "Operations Manager",
        "Flight Operations Officer"
    ]

    if employee["role"] not in allowed_roles:
        conn.close()
        return {
            "error": "Unauthorized employee"
        }

    # Validate decision

    allowed_decisions = [

        "Cancel Flight",

        "Reschedule Flight",

        "Assign Backup Aircraft",

        "Assign Backup Crew",

        "Delay Flight",

        "Continue Operations"

    ]

    if decision not in allowed_decisions:

        conn.close()

        return {

            "error": "Invalid operational decision"

        }

    # Save decision

    cursor.execute("""

        INSERT INTO OperationDecisions
        (
            flight_id,
            employee_id,
            decision,
            reason,
            created_at
        )

        VALUES
        (
            ?,
            ?,
            ?,
            ?,
            CURRENT_TIMESTAMP
        )

    """, (

        flight_id,

        employee_id,

        decision,

        reason

    ))

    conn.commit()

    conn.close()

    return {

        "success": True,

        "message": "Operation decision recorded"

    }


# Send Notification

def send_notification(
    flight_id: int,
    recipient: str,
    message: str
):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO Notifications
        (
            flight_id,
            recipient,
            message,
            sent_at,
            status
        )
        VALUES
        (
            ?,
            ?,
            ?,
            CURRENT_TIMESTAMP,
            'Pending'
        )
    """, (
        flight_id,
        recipient,
        message
    ))

    conn.commit()
    conn.close()

    return {
        "success": True,
        "message": "Notification created"
    }


def resolve_operational_issue(
    flight_id: int,
    employee_id: int,
    issue_type: str,
    decision: str,
    reason: str
):
    """
    Resolve an operational issue by executing the selected action
    and recording the decision.
    """

    conn = get_connection()
    cursor = conn.cursor()

    # Check flight

    cursor.execute("""
        SELECT flight_id
        FROM Flights
        WHERE flight_id = ?
    """, (flight_id,))

    if not cursor.fetchone():
        conn.close()
        return {"error": "Flight not found"}
    
    # Execute decision

    if decision == "Cancel Flight":

        cursor.execute("""
            UPDATE Flights
            SET status='Cancelled'
            WHERE flight_id=?
        """, (flight_id,))

    elif decision == "Reschedule Flight":

        cursor.execute("""
            UPDATE Flights
            SET status='Rescheduled'
            WHERE flight_id=?
        """, (flight_id,))

    elif decision == "Assign Backup Aircraft":

        cursor.execute("""
            SELECT aircraft_id
            FROM Aircraft
            WHERE status='Available'
            LIMIT 1
        """)

        aircraft = cursor.fetchone()

        if not aircraft:
            conn.close()
            return {"error": "No available aircraft"}

        cursor.execute("""
            UPDATE Flights
            SET aircraft_id=?
            WHERE flight_id=?
        """, (
            aircraft["aircraft_id"],
            flight_id
        ))

        cursor.execute("""
            UPDATE Aircraft
            SET status='Assigned'
            WHERE aircraft_id=?
        """, (
            aircraft["aircraft_id"],
        ))

    elif decision == "Assign Backup Crew":

        cursor.execute("""
            SELECT crew_id
            FROM Crew
            WHERE availability=1
            LIMIT 1
        """)

        crew = cursor.fetchone()

        if not crew:
            conn.close()
            return {"error": "No available crew"}

        cursor.execute("""
            INSERT INTO FlightCrew
            (
                flight_id,
                crew_id
            )
            VALUES (?,?)
        """, (
            flight_id,
            crew["crew_id"]
        ))

        cursor.execute("""
            UPDATE Crew
            SET availability=0
            WHERE crew_id=?
        """, (
            crew["crew_id"],
        ))

    else:
        conn.close()
        return {"error": "Unknown decision"}

    
    # Save operation decision

    cursor.execute("""
        INSERT INTO OperationDecisions
        (
            flight_id,
            employee_id,
            decision,
            reason,
            created_at
        )
        VALUES
        (
            ?,
            ?,
            ?,
            ?,
            CURRENT_TIMESTAMP
        )
    """, (
        flight_id,
        employee_id,
        decision,
        reason
    ))

    conn.commit()
    conn.close()

    return {

        "success": True,

        "issue_type": issue_type,

        "decision": decision,

        "reason": reason

    }
