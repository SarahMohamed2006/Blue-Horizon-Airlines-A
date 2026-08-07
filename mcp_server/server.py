import sys
from mcp_app import mcp
from database import initialize_database

# Register MCP Components

import tools
import resources
import prompts

# Server

def start_server():
    """
    Start the Blue Horizon MCP server.

    Before starting the MCP transport, make sure the SQLite
    database is initialized and seeded.
    """

    # Initialize database

    initialize_database()

    # Select transport

    transport = "stdio"

    if len(sys.argv) > 1:
        transport = sys.argv[1].lower()

    # HTTP transport

    if transport == "http":

        print(
            "Blue Horizon MCP Server is running "
            "on http://localhost:8000"
        )

        mcp.run(
            transport="streamable-http",
            host="0.0.0.0",
            port=8000
        )

    # STDIO transport

    else:

        print(
            "Blue Horizon MCP Server is running "
            "using stdio"
        )

        mcp.run(
            transport="stdio"
        )

# Entry Point

if __name__ == "__main__":
    start_server()
