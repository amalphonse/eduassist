# -*- coding: utf-8 -*-
"""EduAssist — A Multi-Agent Student Support System

Built on the same architecture as Lab 2b, but for education:
- Router decides which specialist helps (homework, course, library)
- Each specialist has domain-specific tools from the school MCP server
- Teachers approve hints for graded work (human-in-the-loop gate)
- Students, teachers, and parents each see only their scope

    python eduassist/eduassist_main.py --as student.john         # terminal chat
    python eduassist/eduassist_main.py --as student.john --web   # web page at http://127.0.0.1:7867
    python eduassist/eduassist_main.py --as teacher.smith --web  # as a teacher
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
import threading
import uuid
from pathlib import Path
from typing import Annotated, TypedDict

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from rich.markup import escape

import _school
from _kit import MODEL, banner, client, say
from _school_mcp_client import call, school_session, openai_tools

try:
    from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
    from langchain_core.tools import StructuredTool
    from langchain_openai import ChatOpenAI
    from langgraph.checkpoint.memory import MemorySaver
    from langgraph.graph import END, START, StateGraph
    from langgraph.graph.message import add_messages
    from langgraph.prebuilt import create_react_agent
    from langgraph.types import Command, interrupt
except ImportError as e:
    sys.exit(f"missing package ({e.name}). Run:  pip install -r requirements-graph.txt")


# ═════════════════════════════════════════════════════════════════════════════
# THE THREE BLANKS — Configure routing, approval gates, and hop budget
# ═════════════════════════════════════════════════════════════════════════════

# BLANK 1 · Routing Rules
ROUTING_RULES = """\
Route to 'homework' for questions about assignments, homework help, hints, problem-solving, or submitting work.
Route to 'course' for questions about syllabus, class schedule, course materials, or what's coming up in class.
Route to 'library' for requests for learning resources, videos, articles, practice problems, or study materials.
Route to 'answer' if the question is just a greeting, thanks, or doesn't need any tools.

IMPORTANT: If a student asks for complete answers to graded assignments, route to 'answer' with a refusal.
Offer hints instead. Never give full solutions to graded work.

If the student needs information from multiple domains (e.g., homework due dates AND course schedule),
let the router hand off between specialists.
"""

# BLANK 2 · Teacher Approval Gate
def needs_teacher(tool_name: str, args: dict) -> bool:
    """Return True if this tool call needs teacher approval before running"""
    # Hints for graded assignments require teacher approval
    # (The hint function will indicate if approval is needed in its response)
    if tool_name == "get_hint":
        return True  # Teacher should review all hints

    # Submit work doesn't need approval (students should submit freely)
    if tool_name == "submit_work":
        return False

    # All other writes need approval (be safe by default)
    return _school.RISK.get(tool_name, "destructive") != "read"


# BLANK 3 · Hop Budget
MAX_HOPS = 3  # Students often need homework + course + library resources


# ═════════════════════════════════════════════════════════════════════════════
# Specialists and Tools Configuration
# ═════════════════════════════════════════════════════════════════════════════

SPECIALISTS = {
    "homework": ["get_assignment", "list_assignments", "get_hint", "submit_work"],
    "course": ["get_course", "get_syllabus", "get_schedule"],
    "library": ["search_resources", "get_resource"],
}
ROUTES = list(SPECIALISTS) + ["answer"]


class State(TypedDict):
    messages: Annotated[list, add_messages]
    hops: int
    route: str
    why: str


# ═════════════════════════════════════════════════════════════════════════════
# MCP Tools Integration
# ═════════════════════════════════════════════════════════════════════════════

async def mcp_tools(session) -> list[StructuredTool]:
    """Convert school MCP tools to LangChain tools"""
    listed = (await session.list_tools()).tools
    out = []

    for t in listed:
        schema = getattr(t, "input_schema", None) or getattr(t, "inputSchema", None) or {"type": "object", "properties": {}}

        def bind(name):
            async def run(**kw):
                return await call(session, name, kw)
            return run

        out.append(StructuredTool(
            name=t.name,
            description=t.description or t.name,
            args_schema=schema,
            coroutine=bind(t.name)
        ))

    return out


def _gated(tool: StructuredTool) -> StructuredTool:
    """Wrap a tool so it pauses for teacher approval before running"""
    inner = tool.coroutine or (lambda **kw: asyncio.to_thread(tool.func, **kw))

    async def run(**kw):
        if needs_teacher(tool.name, kw):
            decision = interrupt({"tool": tool.name, "args": kw})
            if str(decision).lower() not in ("y", "yes", "approve", "approved", "ok"):
                return f"DENIED by teacher: {tool.name} not approved."
        return await inner(**kw)

    return StructuredTool(
        name=tool.name,
        description=tool.description,
        args_schema=tool.args_schema,
        coroutine=run
    )


# ═════════════════════════════════════════════════════════════════════════════
# Graph Builder
# ═════════════════════════════════════════════════════════════════════════════

def build_graph(session_tools: list, llm, user_id: str):
    """Build the multi-agent graph for EduAssist"""
    by_name = {t.name: t for t in session_tools}
    agents = {}

    for name, wanted in SPECIALISTS.items():
        tools = [(_gated(by_name[n]) if _school.RISK.get(n) != "read" else by_name[n])
                 for n in wanted if n in by_name]

        # Customize prompts by specialist type
        if name == "homework":
            prompt = (f"You are the {name} specialist for EduAssist, acting as {user_id}. "
                      "Help students with their assignments. Use your tools to find assignments, provide hints, "
                      "and help with submissions. For graded work, provide hints that guide thinking but never "
                      "give complete answers. If a tool is denied, explain why and suggest alternatives. "
                      "Answer in a few sentences for the router, not for the student directly.")
        elif name == "course":
            prompt = (f"You are the {name} specialist for EduAssist, acting as {user_id}. "
                      "Help students understand their course schedule, syllabus, and upcoming topics. "
                      "Use your tools to find course information and schedules. "
                      "Answer in a few sentences for the router, not for the student directly.")
        elif name == "library":
            prompt = (f"You are the {name} specialist for EduAssist, acting as {user_id}. "
                      "Help students find learning resources like videos, articles, and practice problems. "
                      "Search for resources that match the topics they're studying. "
                      "Answer in a few sentences for the router, not for the student directly.")
        else:
            prompt = (f"You are the {name} specialist for EduAssist, acting as {user_id}. "
                      "Use only your tools. If a tool is denied, say so and stop. "
                      "Answer in a few sentences for the router, not for the student directly.")

        agents[name] = create_react_agent(llm, tools, prompt=prompt)

    async def router(state: State) -> dict:
        """Route to the appropriate specialist or answer"""
        if state.get("hops", 0) >= MAX_HOPS:
            return {"route": "answer", "why": f"budget: {MAX_HOPS} hop(s) used"}

        sys_msg = SystemMessage(content=(
            "You route student questions to the right specialist. Options: "
            + ", ".join(ROUTES) + ". 'answer' means reply now with what is already in the conversation.\n"
            "Rules:\n" + ROUTING_RULES + "\nReturn JSON only: {\"next\": \"<option>\", \"why\": \"<one line>\"}"
        ))

        out = await llm.ainvoke([sys_msg, *state["messages"]], response_format={"type": "json_object"})
        try:
            d = json.loads(out.content)
        except (json.JSONDecodeError, TypeError):
            d = {}

        route = d.get("next") if d.get("next") in ROUTES else "answer"
        return {"route": route, "why": str(d.get("why", ""))[:160]}

    def make_specialist(name: str):
        async def node(state: State) -> dict:
            res = await agents[name].ainvoke({"messages": state["messages"]})
            new = res["messages"][len(state["messages"]):]
            # Tag messages so we know which specialist spoke
            for m in new:
                if isinstance(m, AIMessage):
                    m.name = name
            return {"messages": new, "hops": state.get("hops", 0) + 1}
        return node

    async def answer(state: State) -> dict:
        """Synthesize final answer for the student"""
        sys_msg = SystemMessage(content=(
            f"You are EduAssist, a helpful learning assistant acting as {user_id}. "
            "Reply to the student using only what the specialists found in this conversation. "
            "If something was denied or not found, explain that clearly and suggest alternatives. "
            "Be encouraging and supportive. Keep responses concise and focused on helping the student learn."
        ))

        out = await llm.ainvoke([sys_msg, *state["messages"]])
        out.name = "answer"
        return {"messages": [out], "hops": 0}

    # Build the graph
    g = StateGraph(State)
    g.add_node("router", router)
    for name in SPECIALISTS:
        g.add_node(name, make_specialist(name))
    g.add_node("answer", answer)

    g.add_edge(START, "router")
    g.add_conditional_edges("router", lambda s: s["route"], {r: r for r in ROUTES})
    for name in SPECIALISTS:
        g.add_edge(name, "router")
    g.add_edge("answer", END)

    return g.compile(checkpointer=MemorySaver())


# ═════════════════════════════════════════════════════════════════════════════
# Runner Class
# ═════════════════════════════════════════════════════════════════════════════

class Runner:
    """Owns the MCP session and compiled graph on a background loop"""

    def __init__(self, user_id: str, llm=None):
        self.user_id = user_id
        self._llm = llm
        self.loop = asyncio.new_event_loop()
        self.ready = threading.Event()
        self.graph = None
        self.tools: list = []
        threading.Thread(target=self._serve, daemon=True).start()
        self.ready.wait(30)
        if self.graph is None:
            raise RuntimeError("the school server did not start")

    def _serve(self):
        asyncio.set_event_loop(self.loop)
        self.loop.run_until_complete(self._main())

    async def _main(self):
        async with school_session(self.user_id) as session:
            self.tools = await mcp_tools(session)
            llm = self._llm or ChatOpenAI(model=MODEL, temperature=0)
            self.graph = build_graph(self.tools, llm, self.user_id)
            self.ready.set()
            await asyncio.Event().wait()  # Keep running

    def _run(self, coro):
        return asyncio.run_coroutine_threadsafe(coro, self.loop).result()

    def turn(self, thread_id: str, text: str | None = None, resume: str | None = None) -> dict:
        """Send a message or resume from a gate"""
        cfg = {"configurable": {"thread_id": thread_id}}
        payload = Command(resume=resume) if resume is not None else {"messages": [HumanMessage(content=text)], "hops": 0}

        async def go():
            before = len((await self.graph.aget_state(cfg)).values.get("messages", []))
            await self.graph.ainvoke(payload, cfg)
            st = await self.graph.aget_state(cfg)
            msgs = st.values.get("messages", [])[before:]
            pending = None
            for task in st.tasks:
                for it in getattr(task, "interrupts", ()):
                    pending = it.value

            return {
                "messages": [{
                    "role": m.type,
                    "name": getattr(m, "name", None),
                    "text": _text(m),
                    "tool_calls": [tc["name"] for tc in getattr(m, "tool_calls", [])]
                } for m in msgs],
                "pending": pending,
                "route": st.values.get("route"),
                "why": st.values.get("why")
            }

        return self._run(go())


def _text(m) -> str:
    """Extract text from message content"""
    def flat(c):
        if isinstance(c, list):
            return " ".join(flat(p) for p in c)
        if isinstance(c, dict):
            return str(c.get("text", "") or "")
        return str(c or "")

    c = m.content
    if isinstance(c, str) and c.startswith("["):
        try:
            c = json.loads(c)
        except json.JSONDecodeError:
            pass
    return flat(c).strip()


# ═════════════════════════════════════════════════════════════════════════════
# Terminal Chat REPL
# ═════════════════════════════════════════════════════════════════════════════

def repl(runner: Runner) -> None:
    """Interactive terminal chat"""
    thread = uuid.uuid4().hex[:8]
    say(f"  [dim]thread {thread} · as {runner.user_id} · {len(runner.tools)} tools · "
        f"MAX_HOPS={MAX_HOPS} · blank, q to quit[/dim]\n")
    say("  try:  What homework do I have this week?   ·   I'm stuck on problem 5 in my quadratic equations   ·   "
        "What videos can help me with photosynthesis?\n")

    while True:
        try:
            text = input("  you > ").strip()
        except EOFError:
            break
        if not text or text == "q":
            break

        out = runner.turn(thread, text=text)
        while True:
            for m in out["messages"]:
                if m["role"] == "ai" and m["tool_calls"]:
                    say(f"    [dim]{m['name'] or 'agent'} → {', '.join(m['tool_calls'])}[/dim]")
                elif m["role"] == "tool":
                    say(f"    [dim]  ← {escape(m['text'][:110])}[/dim]")
                elif m["role"] == "ai" and m["name"] == "answer":
                    say(f"\n  [bold]EduAssist >[/bold] {escape(m['text'])}\n")
                elif m["role"] == "ai" and m["text"]:
                    say(f"    [cyan]{m['name']}:[/cyan] {escape(m['text'][:300])}")

            if not out["pending"]:
                break

            p = out["pending"]
            say(f"\n  [red]TEACHER APPROVAL[/red] {p['tool']} {escape(json.dumps(p['args'])[:160])}")
            try:
                decision = input("  approve? [y/N] > ").strip() or "n"
            except EOFError:
                decision = "n"
            out = runner.turn(thread, resume=decision)


# ═════════════════════════════════════════════════════════════════════════════
# Main Entry Point
# ═════════════════════════════════════════════════════════════════════════════

def main() -> None:
    ap = argparse.ArgumentParser(description="EduAssist — Multi-Agent Student Support System")
    ap.add_argument("--as", dest="user", default="student.john",
                   help="Act as this user (default student.john)")
    ap.add_argument("--web", action="store_true",
                   help="Serve the chat page instead of terminal")
    ap.add_argument("--port", type=int, default=7867)
    ap.add_argument("--host", default="127.0.0.1",
                   help="0.0.0.0 only inside Docker, and only with CHAT_SECRET")
    args = ap.parse_args()

    banner("EduAssist", "Multi-Agent Student Support System")
    client()  # Load .env, check API key
    runner = Runner(args.user)

    if args.web:
        from _chat_web import serve
        serve(runner, host=args.host, port=args.port,
              title=f"EduAssist · {args.user}")
    else:
        repl(runner)


if __name__ == "__main__":
    main()
