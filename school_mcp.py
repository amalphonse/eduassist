# -*- coding: utf-8 -*-
"""The school API as an MCP server — like estate_mcp.py but for education.

    python eduassist/school_mcp.py [--as <user_id>]

One tool per `_school.py` function, same names, same arguments minus `user`.
The acting user is fixed when the server starts. Every permission check runs
inside `_school.py`; this file is just the wire.

A denial comes back as text, not an exception, so the agent can read it and
re-plan.
"""
from __future__ import annotations

import argparse
import json
import os
import sys

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from mcp.server.mcpserver import MCPServer  # mcp 2.x
except ImportError:
    from mcp.server.fastmcp import FastMCP as MCPServer  # mcp 1.x

import _school as S


def _acting_user() -> str:
    """Get the user this server acts as"""
    ap = argparse.ArgumentParser(description="School MCP Server")
    ap.add_argument("--as", dest="user", default="student.john",
                   help="Act as this user (default: student.john)")
    return ap.parse_args().user


USER = _acting_user()

server = MCPServer(
    "eduassist",
    instructions=(f"You are connected to the school system as {USER}. "
                  "Help students learn by providing hints and resources, never complete answers. "
                  "Respect teacher oversight and academic integrity."),
    log_level="WARNING",
)


def _text(value) -> str:
    """Convert result to text (JSON for structured data)"""
    return json.dumps(value, ensure_ascii=False, indent=1)


def _denied(e: Exception) -> str:
    """Convert denial to helpful text"""
    return (f"DENIED: {e}. Do not retry this call with the same arguments. "
            f"Explain what you needed and why it was refused, and either re-plan "
            f"within your scope or suggest the student ask their teacher.")


# ─── Read Operations ────────────────────────────────────────────────────────

@server.tool(description="Get details of a specific assignment by ID. Returns assignment info, "
                         "problems, due date, and status. Use this when a student asks about a "
                         "specific assignment. Risk: read.")
def get_assignment(assignment_id: str) -> str:
    try:
        return _text(S.get_assignment(USER, assignment_id))
    except S.Denied as e:
        return _denied(e)


@server.tool(description="List assignments for the current user. Filter by status (assigned, "
                         "submitted, graded), due date, or course. Returns assignments in "
                         "chronological order. Risk: read.")
def list_assignments(status: str | None = None, due_before: str | None = None,
                    course_id: str | None = None, limit: int = 50) -> str:
    try:
        return _text(S.list_assignments(USER, status, due_before, course_id, limit))
    except S.Denied as e:
        return _denied(e)


@server.tool(description="List all courses accessible to the current user. Students see their "
                         "enrolled courses, teachers see courses they teach, admins see all. Risk: read.")
def list_courses() -> str:
    try:
        return _text(S.list_courses(USER))
    except S.Denied as e:
        return _denied(e)


@server.tool(description="Get course information including name, grade level, teacher, schedule, "
                         "and syllabus. Use this when students ask about course details. Risk: read.")
def get_course(course_id: str) -> str:
    try:
        return _text(S.get_course(USER, course_id))
    except S.Denied as e:
        return _denied(e)


@server.tool(description="Get the syllabus for a course: topics covered, grading breakdown, "
                         "requirements. Use when students ask what will be on the test or what "
                         "topics are coming up. Risk: read.")
def get_syllabus(course_id: str) -> str:
    try:
        return _text(S.get_syllabus(USER, course_id))
    except S.Denied as e:
        return _denied(e)


@server.tool(description="Get class schedule for the current user. Optionally filter to one "
                         "course. Returns meeting times and teachers. Risk: read.")
def get_schedule(course_id: str | None = None) -> str:
    try:
        return _text(S.get_schedule(USER, course_id))
    except S.Denied as e:
        return _denied(e)


@server.tool(description="Search for learning resources (videos, articles, practice problems). "
                         "Filter by topics (e.g. ['algebra', 'quadratics']) and/or resource type "
                         "(video, article, practice). Returns URLs and descriptions. Risk: read.")
def search_resources(topics: list[str] | None = None, resource_type: str | None = None,
                    limit: int = 10) -> str:
    try:
        # Handle JSON string input
        if isinstance(topics, str):
            topics = json.loads(topics)
        return _text(S.search_resources(USER, topics, resource_type, limit))
    except S.Denied as e:
        return _denied(e)
    except json.JSONDecodeError as e:
        return f"INVALID: topics must be a JSON array, got: {e}"


@server.tool(description="Get a specific learning resource by ID. Returns full details including "
                         "URL, description, topics, and duration. Risk: read.")
def get_resource(resource_id: str) -> str:
    try:
        return _text(S.get_resource(USER, resource_id))
    except S.Denied as e:
        return _denied(e)


# ─── Write Operations ───────────────────────────────────────────────────────

@server.tool(description="Get a hint for a specific problem on an assignment. Provides progressive "
                         "hints (level 1-3) that guide thinking without giving the answer. For graded "
                         "assignments, this requires teacher approval. Never call this more than once "
                         "per problem without student confirmation. Risk: write.")
def get_hint(assignment_id: str, problem_number: int, level: int = 1) -> str:
    try:
        return _text(S.get_hint(USER, assignment_id, problem_number, level))
    except S.Denied as e:
        return _denied(e)


@server.tool(description="Submit answers for an assignment. Students use this to turn in their work. "
                         "Takes a dictionary mapping problem numbers to answers. Returns submission "
                         "confirmation. Risk: write.")
def submit_work(assignment_id: str, answers: dict) -> str:
    try:
        # Handle JSON string input
        if isinstance(answers, str):
            answers = json.loads(answers)
        return _text(S.submit_work(USER, assignment_id, answers))
    except S.Denied as e:
        return _denied(e)
    except json.JSONDecodeError as e:
        return f"INVALID: answers must be a JSON object, got: {e}"


if __name__ == "__main__":
    server.run("stdio")
