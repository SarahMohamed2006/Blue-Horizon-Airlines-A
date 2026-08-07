import sqlite3
from pathlib import Path
# Project Paths
# Project root contains:
#   db/
#   mcp_server/
PROJECT_ROOT = Path(__file__).resolve().parent.parent

DB_DIR = PROJECT_ROOT / "db"
DB_PATH = DB_DIR / "blue_horizon.db"

SCHEMA_PATH = DB_DIR / "schema.sql"
SEED_PATH = DB_DIR / "seed.sql"


# Database Connection

def get_connection():
    """
    Create and return a connection to the Blue Horizon SQLite database.

    Every connection:
    - Uses sqlite3.Row so rows can be accessed by column name.
    - Enables SQLite foreign-key enforcement.
    """

    DB_DIR.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(str(DB_PATH))

    # Example:
    # row["flight_id"]
    # row["status"]
    conn.row_factory = sqlite3.Row

    # Enforce FOREIGN KEY constraints.
    conn.execute("PRAGMA foreign_keys = ON")

    return conn


# Database State Check

def _database_has_data(conn):
    """
    Check whether the main Flights table exists and contains data.

    This handles:
    - Database file does not exist.
    - Database file exists but is empty.
    - Database was created but seed data was never loaded.
    """

    table = conn.execute(
        """
        SELECT name
        FROM sqlite_master
        WHERE type = 'table'
          AND name = 'Flights'
        """
    ).fetchone()

    if table is None:
        return False

    count = conn.execute(
        "SELECT COUNT(*) AS count FROM Flights"
    ).fetchone()["count"]

    return count > 0


# Database Initialization

def initialize_database():
    """
    Initialize the Blue Horizon database.

    The function:
    1. Verifies schema.sql exists.
    2. Verifies seed.sql exists.
    3. Creates the schema when the database is empty.
    4. Loads seed data only when the database has no data.
    5. Does not duplicate seed data on every server startup.
    """

    if not SCHEMA_PATH.exists():
        raise FileNotFoundError(
            f"Schema file not found: {SCHEMA_PATH}"
        )

    if not SEED_PATH.exists():
        raise FileNotFoundError(
            f"Seed file not found: {SEED_PATH}"
        )

    conn = get_connection()

    try:
        # If the database already contains the Flights table
        # with data, do not run the seed again.
        if _database_has_data(conn):
            return

        # Create database schema

        schema_sql = SCHEMA_PATH.read_text(
            encoding="utf-8"
        )

        conn.executescript(schema_sql)

        # Load initial seed data

        seed_sql = SEED_PATH.read_text(
            encoding="utf-8"
        )

        conn.executescript(seed_sql)

        conn.commit()

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()

# Manual Initialization


if __name__ == "__main__":
    initialize_database()

    print(
        f"Database initialized successfully: {DB_PATH}"
    )
