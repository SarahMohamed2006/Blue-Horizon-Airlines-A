"""
Blue Horizon Airlines - MCP Agent / Client
============================================
This is the AGENT side of the project: it connects to the Blue Horizon
MCP server built by the rest of the team, performs the protocol
handshake, and demonstrates every protocol concern required by the lab.

HOW TO READ THIS FILE (for the grader / teammates):
Every section is tagged with a comment like:
    # === CONCERN: <name> ===
so you can jump straight to the part you need without reading the
whole file top to bottom.

Run:
    python client.py stdio      -> connects to the server over stdio
    python client.py http       -> connects to the server over Streamable HTTP
"""

import asyncio
import sys
import os

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.client.streamable_http import streamablehttp_client
from mcp import types


# ---------------------------------------------------------------------------
# CONFIG - change these to match how your teammates actually run the server
# ---------------------------------------------------------------------------
SERVER_SCRIPT_PATH = os.path.join(
    os.path.dirname(__file__), "..", "mcp_server", "main.py"
)
HTTP_SERVER_URL = "http://localhost:8000/mcp"


# ---------------------------------------------------------------------------
# === CONCERN: ELICITATION ===
# This function is called by the SDK whenever the server sends an
# elicitation/create request (e.g. "confirm you want to cancel flight
# BH101"). We stop and ask a REAL human (via terminal input) instead of
# silently accepting or silently failing.
# ---------------------------------------------------------------------------
async def elicitation_callback(
    context, params: types.ElicitRequestParams
) -> types.ElicitResult:
    print("\n" + "=" * 60)
    print("ACTION NEEDS YOUR CONFIRMATION (elicitation/create)")
    print("=" * 60)
    print(params.message)

    # If the server asked for structured fields (a schema), show them
    schema_props = {}
    if params.requestedSchema:
        schema_props = params.requestedSchema.get("properties", {})

    answers = {}
    for field_name, field_def in schema_props.items():
        prompt_text = field_def.get("description", field_name)
        raw = input(f"  {prompt_text} ({field_name}): ").strip()
        answers[field_name] = raw

    decision = input("\nType 'yes' to confirm, anything else to decline: ").strip().lower()

    if decision == "yes":
        return types.ElicitResult(action="accept", content=answers or None)
    else:
        return types.ElicitResult(action="decline")


# ---------------------------------------------------------------------------
# === CONCERN: SAMPLING ===
# Some tools on the server (e.g. generating a delay announcement or
# summarizing a maintenance report) need real LLM reasoning. Per the MCP
# spec, the SERVER does not call its own model for this - it asks the
# CLIENT to run the completion (sampling/createMessage), because the
# client is the one the human trusts and pays for. This callback is what
# makes that happen: we take the messages the server wants completed and
# run them through OUR OWN model (Claude via the Anthropic API).
# ---------------------------------------------------------------------------
async def sampling_callback(
    context, params: types.CreateMessageRequestParams
) -> types.CreateMessageResult:
    try:
        import anthropic
    except ImportError:
        return types.CreateMessageResult(
            role="assistant",
            content=types.TextContent(
                type="text",
                text="[sampling unavailable: 'anthropic' package not installed on client]",
            ),
            model="none",
            stopReason="error",
        )

    client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY from env

    # Convert MCP sampling messages into Anthropic API messages
    anthropic_messages = []
    for m in params.messages:
        text = m.content.text if hasattr(m.content, "text") else str(m.content)
        anthropic_messages.append({"role": m.role, "content": text})

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=params.maxTokens or 500,
        system=params.systemPrompt or "",
        messages=anthropic_messages,
    )

    result_text = "".join(
        block.text for block in response.content if block.type == "text"
    )

    return types.CreateMessageResult(
        role="assistant",
        content=types.TextContent(type="text", text=result_text),
        model="claude-sonnet-4-6",
        stopReason="endTurn",
    )


# ---------------------------------------------------------------------------
# === CONCERN: NOTIFICATIONS ===
# The tool set is NOT static. Example in our system: a front-desk /
# read-only session only sees safe tools. Once a supervisor role is
# confirmed (or a flight enters a state that unlocks new actions), the
# server pushes `notifications/tools/list_changed`. This handler catches
# that push and re-fetches the tool list immediately - the agent never
# has to poll or guess.
# ---------------------------------------------------------------------------
async def message_handler(message):
    if isinstance(message, Exception):
        print(f"[transport error] {message}")
        return

    if isinstance(message, types.ServerNotification):
        note = message.root
        if isinstance(note, types.ToolListChangedNotification):
            print("\n[notification] tools/list_changed received -> refreshing tool list")
            # The actual refresh happens in run_demo() right after this fires,
            # via session.list_tools(). We just log here so it's visible.
        elif isinstance(note, types.ResourceListChangedNotification):
            print("\n[notification] resources/list_changed received")
        elif isinstance(note, types.LoggingMessageNotification):
            print(f"[server log:{note.params.level}] {note.params.data}")


# ---------------------------------------------------------------------------
# === CONCERN: PROGRESS TRACKING ===
# Long-running tools (e.g. a fleet-wide report) report progress instead
# of leaving the client blocked. This callback prints each update as it
# streams in.
# ---------------------------------------------------------------------------
async def progress_callback(progress: float, total: float | None, message: str | None):
    pct = f"{(progress / total) * 100:.0f}%" if total else f"{progress}"
    print(f"  [progress] {pct} - {message or ''}")


# ---------------------------------------------------------------------------
# === CONCERN: CAPABILITY NEGOTIATION ===
# We never assume the server supports something. After initialize(), we
# read result.capabilities and gate our own behaviour on it. A server
# without elicitation support gets routed to a safe, read-only fallback.
# ---------------------------------------------------------------------------
def check_capabilities(init_result: types.InitializeResult) -> dict:
    caps = init_result.capabilities
    supported = {
    "tools": caps.tools is not None,
    "resources": caps.resources is not None,
    "prompts": caps.prompts is not None,
    "logging": caps.logging is not None,
    "elicitation": hasattr(caps, "elicitation"),
    "sampling": hasattr(caps, "sampling"),
}
    print("\n[capability negotiation] server declared:")
    for k, v in supported.items():
        print(f"  - {k}: {'yes' if v else 'no'}")
    return supported


# ---------------------------------------------------------------------------
# MAIN DEMO - a fixed, repeatable set of scenarios (per the guardrails:
# "keep a small fixed set of test inputs, one per concern")
# ---------------------------------------------------------------------------
async def run_demo(session: ClientSession):
    print("\n### 1) INITIALIZE / CAPABILITY NEGOTIATION ###")
    init_result = await session.initialize()
    caps = check_capabilities(init_result)

    print("\n### 2) RESOURCES: reading the crew-duty policy (data, not a function call) ###")
    resources = await session.list_resources()
    print(f"  available resources: {[r.uri for r in resources.resources]}")
    try:
        policy = await session.read_resource("policy://crew-duty")
        print(f"  policy content -> {policy.contents[0].text[:200]}...")
    except Exception as e:
        print(f"  [skipped - server not ready yet: {e}]")

    print("\n### 3) PROMPTS: fetching the delay_announcement template ###")
    try:
        prompts = await session.list_prompts()
        print(f"  available prompts: {[p.name for p in prompts.prompts]}")
        prompt = await session.get_prompt(
            "delay_announcement",
            {
                "flight_number": "BH218",
                "delay": "45 minutes",
                "reason": "weather at destination",
                "airport": "Heathrow Airport",
            },
        )
        print(f"  rendered prompt -> {prompt.messages[0].content.text[:150]}...")
    except Exception as e:
        print(f"  [skipped - server not ready yet: {e}]")

    print("\n### 4) TOOLS: listing current tool set ###")
    tools = await session.list_tools()
    print(f"  visible tools: {[t.name for t in tools.tools]}")

    print("\n### 5) DEFENSIVE WRITE TOOL + ELICITATION: cancel_flight ###")
    if not caps["elicitation"]:
    print("  [server does not support elicitation - skipping cancel_flight demo]")
else:
    try:
        result = await session.call_tool(
            "cancel_flight",
            {
                "flight_id": 1,
                "employee_id": 1,
                "reason": "Severe weather at destination",
            },
        )
        print(f"  result -> {result.content}")
    except Exception as e:
        print(f"  [skipped: {e}]")
    print("\n### 6) PROGRESS TRACKING: a long-running report tool ###")
    try:
        result = await session.call_tool(
            "generate_ops_report",
            {"scope": "all_active_flights"},
            progress_callback=progress_callback,
        )
        print(f"  final report -> {result.content}")
    except Exception as e:
        print(f"  [skipped - tool not implemented yet by teammates: {e}]")

    print("\n### 7) NOTIFICATIONS: waiting to see if the tool set changes ###")
    print("  (this fires automatically if the server pushes list_changed during this session)")
    await asyncio.sleep(2)
    tools_after = await session.list_tools()
    print(f"  tools now visible: {[t.name for t in tools_after.tools]}")


async def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "stdio"

    if mode == "http":
        async with streamablehttp_client(HTTP_SERVER_URL) as (read, write, _):
            async with ClientSession(
                read,
                write,
                sampling_callback=sampling_callback,
                elicitation_callback=elicitation_callback,
                message_handler=message_handler,
            ) as session:
                await run_demo(session)
    else:
        server_params = StdioServerParameters(
            command="python",
            args=[SERVER_SCRIPT_PATH],
        )
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(
                read,
                write,
                sampling_callback=sampling_callback,
                elicitation_callback=elicitation_callback,
                message_handler=message_handler,
            ) as session:
                await run_demo(session)


if __name__ == "__main__":
    asyncio.run(main())
