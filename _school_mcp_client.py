# -*- coding: utf-8 -*-
"""MCP client for the school server - like _mcp_client.py but for EduAssist.

    async with school_session("student.john") as session:
        tools = openai_tools((await session.list_tools()).tools)
        text  = await call(session, "get_assignment", {"assignment_id": "A-5001"})
"""
from __future__ import annotations

import os
import sys
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncIterator

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

SERVER = Path(__file__).resolve().parent / "school_mcp.py"


@asynccontextmanager
async def school_session(user_id: str) -> AsyncIterator[ClientSession]:
    """Spawn the school MCP server as `user_id` and yield a ready session."""
    passthrough = {k: v for k, v in os.environ.items() if k.startswith("SCHOOL_")}
    params = StdioServerParameters(
        command=sys.executable,
        args=[str(SERVER), "--as", user_id],
        cwd=str(SERVER.parent),
        env=passthrough or None
    )
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            yield session


def openai_tools(session_tools) -> list[dict]:
    """MCP tool listing → OpenAI function-calling `tools`"""
    tools = getattr(session_tools, "tools", session_tools)
    return [{"type": "function",
             "function": {"name": t.name, "description": t.description or "",
                          "parameters": getattr(t, "input_schema", None) or t.inputSchema}}
            for t in tools]


async def call(session: ClientSession, name: str, args: dict) -> str:
    """Run one tool; return its text"""
    result = await session.call_tool(name, args or {})
    parts = [c.text for c in getattr(result, "content", []) if getattr(c, "type", "") == "text"]
    text = "\n".join(parts).strip()
    if getattr(result, "is_error", False):
        return f"ERROR: {text or 'tool call failed'}"
    return text
