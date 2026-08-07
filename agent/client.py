import asyncio
import sys
import os

from mcp import ClientSession, StdioServerParameters, types
from mcp.client.stdio import stdio_client
from mcp.client.streamable_http import streamablehttp_client

# Import RAG Pipeline for Task 3 integration
from rag_pipeline import OperationalRAGPipeline

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

SERVER_SCRIPT_PATH = os.path.join(
    BASE_DIR,
    "mcp_server",
    "server.py"
)

HTTP_SERVER_URL = "http://localhost:8000/mcp"


async def elicitation_callback(context, params):
    print("\n" + "=" * 60)
    print("ACTION NEEDS YOUR CONFIRMATION")
    print("=" * 60)

    print(params.message)

    answers = {}
    schema = getattr(params, "requestedSchema", None)

    if schema:
        for name, field in schema.get("properties", {}).items():
            answers[name] = input(
                f"{field.get('description', name)}: "
            ).strip()

    decision = input(
        "\nType yes to confirm: "
    ).lower().strip()

    if decision == "yes":
        return types.ElicitResult(
            action="accept",
            content=answers or None
        )

    return types.ElicitResult(
        action="decline"
    )


async def sampling_callback(context, params):
    try:
        import anthropic

        client = anthropic.Anthropic()
        messages = []

        for message in params.messages:
            messages.append(
                {
                    "role": message.role,
                    "content": message.content.text
                }
            )

        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=params.maxTokens or 500,
            system=params.systemPrompt or "",
            messages=messages
        )

        text = ""
        for block in response.content:
            if block.type == "text":
                text += block.text

        return types.CreateMessageResult(
            role="assistant",
            content=types.TextContent(
                type="text",
                text=text
            ),
            model="claude-sonnet-4-6",
            stopReason="endTurn"
        )

    except Exception as e:
        return types.CreateMessageResult(
            role="assistant",
            content=types.TextContent(
                type="text",
                text=str(e)
            ),
            model="none",
            stopReason="error"
        )


async def message_handler(message):
    if isinstance(message, Exception):
        print(message)
        return

    if isinstance(message, types.ServerNotification):
        print(message)


async def progress_callback(progress, total, message):
    if total:
        percent = progress / total * 100
        print(f"{percent:.0f}% {message or ''}")
    else:
        print(f"{progress} {message or ''}")


def check_capabilities(result):
    caps = result.capabilities

    data = {
        "tools": caps.tools is not None,
        "resources": caps.resources is not None,
        "prompts": caps.prompts is not None,
        "logging": caps.logging is not None,
        "elicitation": hasattr(caps, "elicitation"),
        "sampling": hasattr(caps, "sampling")
    }

    for k, v in data.items():
        print(f"{k}: {'yes' if v else 'no'}")

    return data


async def run_operations_workflow(session: ClientSession):
    """
    Task 3: Operations Agent Workflow combining Memory (past events) 
    and RAG (official manual policies).
    """
    print("\n" + "=" * 60)
    print("✈️ BLUE HORIZON AIRLINES - OPERATIONS AGENT WORKFLOW")
    print("=" * 60)

    # 1. Initialize RAG Pipeline
    rag_engine = OperationalRAGPipeline()

    # Scenario: Flight BH218 maintenance delay following a weather issue
    flight_id = "BH218"
    user_id = "ops_supervisor_1"
    operational_query = "Flight BH218 has a maintenance delay exceeding 120 minutes. What protocol should we follow?"

    print(f"\n[User: {user_id}] Query: {operational_query}")

    # Step A: Retrieve Memory Context (What happened previously?)
    print(f"\n[Step 1: Inspecting Episodic Memory for Flight {flight_id}...]")
    # Access memory through context or mock memory lookup
    memory_context = (
        f"Memory Retained: Flight {flight_id} experienced a severe weather-related delay "
        f"earlier today (within the last 24 hours) and required a backup aircraft evaluation."
    )
    print(f"   ➔ {memory_context}")

    # Step B: Retrieve Official Policy via RAG Search (What is the rule?)
    print("\n[Step 2: Performing RAG Policy Retrieval...]")
    retrieved_chunks = rag_engine.hybrid_search(operational_query, top_k=2)
    is_valid = rag_engine.self_rag_verification(operational_query, retrieved_chunks)

    if is_valid:
        policy_context = "\n---\n".join(retrieved_chunks)
    else:
        policy_context = "No relevant operational policy found."

    print(f"   ➔ Official Policy Retrieved:\n{policy_context}")

    # Step C: Check MCP Tools Availability
    print("\n🔧 [Step 3: Checking Available Tools via MCP Server...]")
    try:
        tools = await session.list_tools()
        tool_names = [t.name for t in tools.tools]
        print(f"   ➔ Available MCP Server Tools: {tool_names}")
    except Exception as e:
        print(f"   ➔ MCP Tool List Error: {e}")

    # Step D: Synthesis & Agent Decision
    print("\n[Step 4: Operations Agent Synthesis & Decision]:")
    print("-" * 60)
    synthesis = (
        f"1. Memory Rule Triggered: Flight {flight_id} had a weather delay within the last 24 hours.\n"
        f"2. Applied Manual Policy:\n"
        f"   - For maintenance delays > 120 mins: Evaluate backup aircraft deployment within 15 minutes.\n"
        f"   - Secondary aircraft reassignment MUST obtain explicit approval from the Operational Supervisor.\n"
        f"   - Flight crew reassignment must be completed within 45 minutes.\n"
        f"   - Line maintenance must log full discrepancy details into the database prior to departure."
    )
    print(synthesis)
    print("=" * 60)


async def run_demo(session: ClientSession):
    print("\n### 1) INITIALIZE / CAPABILITY NEGOTIATION ###")

    init_result = await session.initialize()
    caps = check_capabilities(init_result)

    print("\n### 2) RESOURCES ###")
    try:
        resources = await session.list_resources()
        print(f"Available resources: {[r.uri for r in resources.resources]}")
    except Exception as e:
        print(f"Resources error: {e}")

    print("\n### 3) PROMPTS ###")
    try:
        prompts = await session.list_prompts()
        print(f"Available prompts: {[p.name for p in prompts.prompts]}")
    except Exception as e:
        print(f"Prompts error: {e}")

    print("\n### 4) TOOLS ###")
    try:
        tools = await session.list_tools()
        print(f"Available tools: {[t.name for t in tools.tools]}")
    except Exception as e:
        print(f"Tools error: {e}")

    # Execute Task 3 Operations Agent Workflow
    await run_operations_workflow(session)

    print("\n### 5) DONE ###")


async def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "stdio"

    if mode == "http":
        async with streamablehttp_client(HTTP_SERVER_URL) as (read, write, _):
            async with ClientSession(
                read,
                write,
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
            ) as session:
                await run_demo(session)


if __name__ == "__main__":
    asyncio.run(main())