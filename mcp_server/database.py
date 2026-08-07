import sqlite3
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent

DB_DIR = PROJECT_ROOT / "db"
DB_PATH = DB_DIR / "blue_horizon.db"

SCHEMA_PATH = DB_DIR / "schema.sql"
SEED_PATH = DB_DIR / "seed.sql"


def get_connection():
    DB_DIR.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")

    return conn


def _database_is_initialized(conn):
    required_tables = {
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

    rows = conn.execute(
        """
        SELECT name
        FROM sqlite_master
        WHERE type = 'table'
        """
    ).fetchall()

    existing_tables = {row["name"] for row in rows}

    if not required_tables.issubset(existing_tables):
        return False

    count = conn.execute(
        "SELECT COUNT(*) AS count FROM Flights"
    ).fetchone()["count"]

    return count > 0


def initialize_database():
    if not SCHEMA_PATH.exists():
        raise FileNotFoundError(f"Schema file not found: {SCHEMA_PATH}")

    if not SEED_PATH.exists():
        raise FileNotFoundError(f"Seed file not found: {SEED_PATH}")

    conn = get_connection()

    try:
        if _database_is_initialized(conn):
            return

        schema_sql = SCHEMA_PATH.read_text(encoding="utf-8")
        conn.executescript(schema_sql)

        seed_sql = SEED_PATH.read_text(encoding="utf-8")
        conn.executescript(seed_sql)

        conn.commit()

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()


if __name__ == "__main__":
    initialize_database()
    print(f"Database initialized: {DB_PATH}")
