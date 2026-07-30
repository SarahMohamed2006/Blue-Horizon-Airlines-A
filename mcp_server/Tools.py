from database import get_connection


# Assign Aircraft

def assign_aircraft(flight_id: int, aircraft_id: int):

    conn = get_connection()
    cursor = conn.cursor()

    # Check flight
    cursor.execute("""
        SELECT flight_id
        FROM Flights
        WHERE flight_id=?
    """, (flight_id,))

    if not cursor.fetchone():
        conn.close()
        return {"error": "Flight not found"}

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
        UPDATE Aircraft
        SET status='Assigned'
        WHERE aircraft_id=?
    """, (aircraft_id,))

    conn.commit()
    conn.close()

    return {
        "success": True,
        "message": "Aircraft assigned successfully"
    }


# Assign Backup Crew

def assign_backup_crew(flight_id: int, crew_id: int):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT flight_id
        FROM Flights
        WHERE flight_id=?
    """, (flight_id,))

    if not cursor.fetchone():
        conn.close()
        return {"error": "Flight not found"}

    cursor.execute("""
        SELECT availability
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

    cursor.execute("""
        INSERT INTO FlightCrew(flight_id, crew_id)
        VALUES (?, ?)
    """, (flight_id, crew_id))

    cursor.execute("""
        UPDATE Crew
        SET availability=0
        WHERE crew_id=?
    """, (crew_id,))

    conn.commit()
    conn.close()

    return {
        "success": True,
        "message": "Backup crew assigned"
    }


# Reschedule Flight

def reschedule_flight(
    flight_id: int,
    new_departure,
    new_arrival
):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT flight_id
        FROM Flights
        WHERE flight_id=?
    """, (flight_id,))

    if not cursor.fetchone():
        conn.close()
        return {"error": "Flight not found"}

    cursor.execute("""
        UPDATE Flights
        SET departure_time=?,
            arrival_time=?,
            status='Rescheduled'
        WHERE flight_id=?
    """, (
        new_departure,
        new_arrival,
        flight_id
    ))

    conn.commit()
    conn.close()

    return {
        "success": True,
        "message": "Flight rescheduled successfully"
    }


# Cancel Flight

def cancel_flight(flight_id: int):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT flight_id
        FROM Flights
        WHERE flight_id=?
    """, (flight_id,))

    if not cursor.fetchone():
        conn.close()
        return {"error": "Flight not found"}

    cursor.execute("""
        UPDATE Flights
        SET status='Cancelled'
        WHERE flight_id=?
    """, (flight_id,))

    conn.commit()
    conn.close()

    return {
        "success": True,
        "message": "Flight cancelled"
    }


# Complete Maintenance

def complete_maintenance(maintenance_id: int):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT maintenance_id
        FROM Maintenance
        WHERE maintenance_id=?
    """, (maintenance_id,))

    if not cursor.fetchone():
        conn.close()
        return {"error": "Maintenance record not found"}

    cursor.execute("""
        UPDATE Maintenance
        SET status='Completed'
        WHERE maintenance_id=?
    """, (maintenance_id,))

    conn.commit()
    conn.close()

    return {
        "success": True,
        "message": "Maintenance marked as completed"
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

    cursor.execute("""
        INSERT INTO OperationDecisions
        (
            flight_id,
            employee_id,
            decision,
            reason,
            created_at
        )
        VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
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