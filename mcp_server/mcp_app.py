from mcp.server.fastmcp import FastMCP

mcp = FastMCP(
    name="Blue Horizon Flight Operations",
    instructions="""
    Blue Horizon Flight Operations Control Assistant.

    This server helps airline operations controllers manage
    flight disruptions, aircraft assignment, crew scheduling,
    maintenance events, weather conditions, operational decisions,
    and passenger notifications.
    """
)
