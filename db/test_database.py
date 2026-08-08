import pytest

from mcp_server.database import get_connection, initialize_database


REQUIRED_TABLES = {
    "Airports",
    "Aircraft",
    "Flights",
    "Crew",
    "FlightCrew",
    "Maintenance",
    "Employees",
    "AircraftAssignments",
    "CrewAssignments",
    "FlightEvents",
    "OperationDecisions",
    "Notifications",
}


def test_database_connection():
    initialize_database()

    conn = get_connection()

    try:
        result = conn.execute("SELECT 1").fetchone()
        assert result[0] == 1
    finally:
        conn.close()


def test_foreign_keys_enabled():
    initialize_database()

    conn = get_connection()

    try:
        result = conn.execute("PRAGMA foreign_keys").fetchone()
        assert result[0] == 1
    finally:
        conn.close()


def test_required_tables_exist():
    initialize_database()

    conn = get_connection()

    try:
        rows = conn.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
            """
        ).fetchall()

        tables = {row["name"] for row in rows}

        assert REQUIRED_TABLES.issubset(tables)
    finally:
        conn.close()


def test_seed_data_exists():
    initialize_database()

    conn = get_connection()

    try:
        expected_counts = {
            "Airports": 4,
            "Aircraft": 3,
            "Flights": 3,
            "Crew": 4,
            "FlightCrew": 5,
            "Maintenance": 2,
            "Employees": 4,
            "AircraftAssignments": 1,
            "CrewAssignments": 2,
            "FlightEvents": 2,
            "OperationDecisions": 1,
            "Notifications": 1,
        }

        for table, expected_count in expected_counts.items():
            count = conn.execute(
                f"SELECT COUNT(*) FROM {table}"
            ).fetchone()[0]

            assert count == expected_count
    finally:
        conn.close()


def test_flight_data():
    initialize_database()

    conn = get_connection()

    try:
        flight = conn.execute(
            """
            SELECT flight_number, status, aircraft_id
            FROM Flights
            WHERE flight_number = ?
            """,
            ("BH218",),
        ).fetchone()

        assert flight is not None
        assert flight["status"] == "Delayed"
        assert flight["aircraft_id"] == 2
    finally:
        conn.close()


def test_aircraft_assignment_data():
    initialize_database()

    conn = get_connection()

    try:
        assignment = conn.execute(
            """
            SELECT flight_id, aircraft_id, assignment_reason
            FROM AircraftAssignments
            WHERE flight_id = ?
            """,
            (2,),
        ).fetchone()

        assert assignment is not None
        assert assignment["aircraft_id"] == 1
        assert (
            assignment["assignment_reason"]
            == "Replacement aircraft assigned after technical issue"
        )
    finally:
        conn.close()


def test_operation_decision_data():
    initialize_database()

    conn = get_connection()

    try:
        decision = conn.execute(
            """
            SELECT flight_id, employee_id, decision
            FROM OperationDecisions
            WHERE flight_id = ?
            """,
            (2,),
        ).fetchone()

        assert decision is not None
        assert decision["employee_id"] == 2
        assert decision["decision"] == "Assign Backup Aircraft"
    finally:
        conn.close()


def test_database_crud():
    initialize_database()

    conn = get_connection()

    try:
        conn.execute("BEGIN")

        conn.execute(
            """
            INSERT INTO Airports
            (airport_id, name, weather, runway_status)
            VALUES (?, ?, ?, ?)
            """,
            (9999, "Test Airport", "Clear", "Open"),
        )

        airport = conn.execute(
            """
            SELECT name
            FROM Airports
            WHERE airport_id = ?
            """,
            (9999,),
        ).fetchone()

        assert airport["name"] == "Test Airport"

        conn.execute(
            """
            UPDATE Airports
            SET weather = ?
            WHERE airport_id = ?
            """,
            ("Cloudy", 9999),
        )

        airport = conn.execute(
            """
            SELECT weather
            FROM Airports
            WHERE airport_id = ?
            """,
            (9999,),
        ).fetchone()

        assert airport["weather"] == "Cloudy"

        conn.execute(
            """
            DELETE FROM Airports
            WHERE airport_id = ?
            """,
            (9999,),
        )

        airport = conn.execute(
            """
            SELECT *
            FROM Airports
            WHERE airport_id = ?
            """,
            (9999,),
        ).fetchone()

        assert airport is None

        conn.rollback()
    finally:
        conn.close()


def test_foreign_key_constraint():
    initialize_database()

    conn = get_connection()

    try:
        with pytest.raises(Exception):
            conn.execute(
                """
                INSERT INTO Aircraft
                (
                    aircraft_id,
                    tail_number,
                    model,
                    capacity,
                    status,
                    current_airport_id
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    9999,
                    "TEST-9999",
                    "Test Aircraft",
                    100,
                    "Available",
                    99999,
                ),
            )
    finally:
        conn.close()
