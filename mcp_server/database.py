import sqlite3
from pathlib import Path


# Project root = folder that contains db/ and mcp_server/
PROJECT_ROOT = Path(__file__).resolve().parent.parent

DB_DIR = PROJECT_ROOT / "db"
DB_PATH = DB_DIR / "blue_horizon.db"

SCHEMA_PATH = DB_DIR / "schema.sql"
SEED_PATH = DB_DIR / "seed.sql"


def get_connection():
    """
    Create and return a connection to the Blue Horizon SQLite database.

    The connection uses sqlite3.Row so database records can be accessed
    using column names, for example:

        row["status"]

    Foreign-key enforcement is enabled for every connection.
    """

    DB_DIR.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(str(DB_PATH))

    # Allow:
    # row["flight_id"]
    # row["status"]
    conn.row_factory = sqlite3.Row

    # Enforce foreign-key relationships.
    conn.execute("PRAGMA foreign_keys = ON")

    return conn


def initialize_database():
    """
    Create the database schema if it does not already exist.

    The seed file is applied only when the database is created for
    the first time, so calling this function does not duplicate seed data.
    """

    database_exists = DB_PATH.exists()

    conn = get_connection()

    try:
        if not database_exists:
            if not SCHEMA_PATH.exists():
                raise FileNotFoundError(
                    f"Schema file not found: {SCHEMA_PATH}"
                )

            if not SEED_PATH.exists():
                raise FileNotFoundError(
                    f"Seed file not found: {SEED_PATH}"
                )

            # Create all tables.
            schema_sql = SCHEMA_PATH.read_text(encoding="utf-8")
            conn.executescript(schema_sql)

            # Insert initial data.
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
    print(f"Database initialized successfully: {DB_PATH}")
