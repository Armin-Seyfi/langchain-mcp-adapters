"""
Connect LangChain to the HubSpot MCP server.

This first run is read-only:
- discover the tools exposed by the MCP server
- call get_user_details to inspect the authenticated account's available access

The HubSpot access token is loaded from .env and is never printed.
"""

import asyncio
import os

from dotenv import load_dotenv
from langchain_mcp_adapters.client import MultiServerMCPClient

from langchain.agents import create_agent
from langchain_openai import ChatOpenAI


HUBSPOT_MCP_URL = "https://mcp.hubspot.com/"


async def main() -> None:
    """Discover HubSpot MCP tools and inspect the connected test account."""
    load_dotenv()

    access_token = os.getenv("HUBSPOT_ACCESS_TOKEN")
    if not access_token:
        raise RuntimeError(
            "HUBSPOT_ACCESS_TOKEN was not found. Add it to the local .env file."
        )

    # MultiServerMCPClient speaks MCP and converts the server's tools
    # into LangChain-compatible tools.
    client = MultiServerMCPClient(
        {
            "hubspot": {
                "transport": "streamable_http",
                "url": HUBSPOT_MCP_URL,
                "headers": {
                    "Authorization": f"Bearer {access_token}",
                },
            }
        }
    )

    tools = await client.get_tools()

    # Inspect the input schema before calling a tool.
    # This makes the tool contract explicit and avoids guessing its arguments.
    search_tool = next(
        (tool for tool in tools if tool.name.endswith("search_crm_objects")),
        None,
    )

    if search_tool is None:
        raise RuntimeError("search_crm_objects was not exposed by HubSpot.")

    print("\nsearch_crm_objects input schema:")
    print(search_tool.args)

    print(f"Discovered {len(tools)} HubSpot MCP tools:")
    for tool in tools:
        print(f"- {tool.name}: {tool.description[:120]}")

    # This is a read-only MCP tool. It reports the current user's
    # identity, permissions, and which CRM objects/tools are available.
    details_tool = next(
        (tool for tool in tools if tool.name.endswith("get_user_details")),
        None,
    )
    if details_tool is None:
        raise RuntimeError(
            "The connected server did not expose get_user_details."
        )

    result = await details_tool.ainvoke({})
    print("\nget_user_details result:")
    print(result)

    # Use one read-only MCP tool so the agent has a narrow, auditable capability.
    model = ChatOpenAI(model="gpt-4o-mini", temperature=0)

    agent = create_agent(
        model=model,
        tools=[search_tool],
        system_prompt=(
            "You are a CRM research assistant. "
            "Use the provided HubSpot search tool to retrieve evidence. "
            "Answer only from the tool result. "
            "If no matching record is returned, say that no record was found. "
            "Do not invent missing values. "
            "Do not include internal record IDs, portal IDs, or direct CRM record URLs."
            "Report only the requested business properties."
        ),
    )

    user_query = (
        "Find the company named HubSpot. Report its name and domain. "
        "If the CRM search returns no matching record, say so."
    )

    result = await agent.ainvoke(
        {"messages": [{"role": "user", "content": user_query}]}
    )

    # Print the interaction trace so the tool evidence can be inspected.
    print("\nAgent and tool trace:")
    for message in result["messages"]:
        print(f"\n{type(message).__name__}:")
        print(message.content)
        if getattr(message, "tool_calls", None):
            print("Tool calls:", message.tool_calls)

if __name__ == "__main__":
    asyncio.run(main())
