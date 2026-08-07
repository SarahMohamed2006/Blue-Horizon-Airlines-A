import asyncio
import sys
import os

from mcp import ClientSession, StdioServerParameters, types
from mcp.client.stdio import stdio_client
from mcp.client.streamable_http import streamablehttp_client


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

        print(
            f"{percent:.0f}% {message or ''}"
        )

    else:

        print(
            f"{progress} {message or ''}"
        )


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

        print(
            f"{k}: {'yes' if v else 'no'}"
        )

    return data
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
