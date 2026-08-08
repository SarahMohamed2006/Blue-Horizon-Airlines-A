"""
Tests for agent/client.py.

These require the `mcp` package (see requirements.txt) and, for the
end-to-end tests, a working Python environment able to launch
mcp_server/server.py as a subprocess over stdio. They cannot run inside
a sandbox that has no network access to install `mcp` — in that case
this file prints a clear skip message instead of failing with a raw
ImportError.
"""

import asyncio
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace

sys.path.append(
    str(Path(__file__).resolve().parents[1] / "agent")
)

try:
    import client as agent_client
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False


@unittest.skipUnless(MCP_AVAILABLE, "mcp package is not installed in this environment")
class TestCheckCapabilities(unittest.TestCase):
    """Pure unit test — no live server needed."""

    def test_reports_all_capabilities_present(self):
        fake_result = SimpleNamespace(
            capabilities=SimpleNamespace(
                tools=object(),
                resources=object(),
                prompts=object(),
                logging=object(),
                elicitation=object(),
                sampling=object(),
            )
        )

        data = agent_client.check_capabilities(fake_result)

        self.assertTrue(all(data.values()))

    def test_reports_missing_capabilities(self):
        fake_result = SimpleNamespace(
            capabilities=SimpleNamespace(
                tools=None,
                resources=None,
                prompts=None,
                logging=None,
            )
        )

        data = agent_client.check_capabilities(fake_result)

        self.assertFalse(data["tools"])
        self.assertFalse(data["resources"])
        self.assertFalse(data["elicitation"])
        self.assertFalse(data["sampling"])


@unittest.skipUnless(MCP_AVAILABLE, "mcp package is not installed in this environment")
class TestServerScriptPath(unittest.TestCase):
    """
    Regression test for the path bug that used to make the stdio client
    unable to find mcp_server/server.py at all (it looked for it under
    agent/mcp_server/ instead of the project root's mcp_server/).
    """

    def test_server_script_path_exists(self):
        self.assertTrue(
            Path(agent_client.SERVER_SCRIPT_PATH).is_file(),
            f"SERVER_SCRIPT_PATH does not point at a real file: "
            f"{agent_client.SERVER_SCRIPT_PATH}",
        )


@unittest.skipUnless(MCP_AVAILABLE, "mcp package is not installed in this environment")
class TestStdioEndToEnd(unittest.TestCase):
    """
    Full end-to-end smoke test: launches the real MCP server over stdio
    and confirms initialize / list_tools / list_resources / list_prompts
    all succeed. Requires aiosqlite and the rest of requirements.txt to
    be installed, since mcp_server/server.py initializes a real database
    on startup.
    """

    def test_stdio_session_lists_expected_tools(self):
        async def run():
            server_params = agent_client.StdioServerParameters(
                command=sys.executable,
                args=[agent_client.SERVER_SCRIPT_PATH],
            )

            async with agent_client.stdio_client(server_params) as (read, write):
                async with agent_client.ClientSession(read, write) as session:
                    await session.initialize()

                    tools = await session.list_tools()
                    tool_names = {t.name for t in tools.tools}

                    for expected in (
                        "authenticate_manager",
                        "deauthenticate_manager",
                        "cancel_flight",
                        "assign_aircraft",
                    ):
                        self.assertIn(expected, tool_names)

                    resources = await session.list_resources()
                    self.assertTrue(len(resources.resources) > 0)

        asyncio.run(run())


if __name__ == "__main__":
    if not MCP_AVAILABLE:
        print(
            "Skipping tests/test_client.py: the 'mcp' package is not "
            "installed in this environment. Run `pip install -r "
            "requirements.txt` first."
        )
        sys.exit(0)

    unittest.main()
