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
