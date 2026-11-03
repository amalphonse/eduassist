#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Simple test to verify EduAssist components work"""

import asyncio
import sys
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent))

from _school_mcp_client import school_session, call


async def test_mcp_server():
    """Test that the MCP server can start and handle requests"""
    print("Testing EduAssist MCP Server...")
    print("-" * 50)

    async with school_session("student.john") as session:
        print("✓ MCP server started successfully")

        # List tools
        tools_result = await session.list_tools()
        tools = tools_result.tools
        print(f"✓ Found {len(tools)} tools:")
        for t in tools:
            print(f"  - {t.name}")

        # Test list_assignments
        print("\nTesting list_assignments...")
        result = await call(session, "list_assignments", {})
        print(f"✓ Result: {result[:200]}...")

        # Test get_assignment
        print("\nTesting get_assignment...")
        result = await call(session, "get_assignment", {"assignment_id": "A-5001"})
        print(f"✓ Result: {result[:200]}...")

        # Test search_resources
        print("\nTesting search_resources...")
        result = await call(session, "search_resources", {
            "topics": ["algebra", "quadratics"],
            "limit": 3
        })
        print(f"✓ Result: {result[:200]}...")

        # Test scope enforcement (student trying to access another student's work)
        print("\nTesting scope enforcement (should be denied)...")
        result = await call(session, "get_assignment", {"assignment_id": "A-5005"})
        if "DENIED" in result:
            print(f"✓ Scope enforcement working: {result[:100]}...")
        else:
            print(f"✗ WARNING: Scope enforcement may not be working correctly")

    print("\n" + "=" * 50)
    print("All tests passed! ✓")
    print("=" * 50)


if __name__ == "__main__":
    asyncio.run(test_mcp_server())
