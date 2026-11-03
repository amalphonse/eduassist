# -*- coding: utf-8 -*-
"""The school API — like _estate.py but for education.

Every function takes the acting user first and enforces scope INSIDE:
- Students can only see their own classes and assignments
- Teachers can only see their own classes and students
- Parents can only see their own children
- Admins can see everything

Every call (and every denial) is written to audit.jsonl for compliance.
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

# Risk tags for tools (like _estate.RISK)
RISK = {
    # Read operations
    "get_assignment": "read",
    "list_assignments": "read",
    "get_course": "read",
    "get_syllabus": "read",
    "get_schedule": "read",
    "search_resources": "read",
    "get_resource": "read",

    # Write operations (need approval)
    "get_hint": "write",  # Hints for graded work need teacher approval
    "submit_work": "write",

    # Destructive operations (always need approval)
    "grade_assignment": "destructive",
    "modify_course": "destructive",
}

# Path configuration
DATA_DIR = Path(__file__).parent / "data"
STATE_FILE = DATA_DIR / "state.json"
AUDIT_FILE = DATA_DIR / "audit.jsonl"


class Denied(Exception):
    """Raised when user lacks permission"""
    pass


# ─── Data Loading ───────────────────────────────────────────────────────────

def _load_json(filename: str) -> Any:
    """Load JSON file from data directory"""
    path = DATA_DIR / filename
    if not path.exists():
        return [] if filename.endswith("s.json") else {}
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _save_json(filename: str, data: Any) -> None:
    """Save JSON file to data directory"""
    path = DATA_DIR / filename
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def _students() -> list[dict]:
    """Load all students"""
    return _load_json("students.json")


def _assignments() -> list[dict]:
    """Load all assignments with state overrides"""
    base = _load_json("assignments.json")
    state = _load_json("state.json")
    # Apply state overrides
    assignments_state = state.get("assignments", {})
    result = []
    for a in base:
        if a["id"] in assignments_state:
            result.append({**a, **assignments_state[a["id"]]})
        else:
            result.append(a)
    return result


def _resources() -> list[dict]:
    """Load all learning resources"""
    return _load_json("resources.json")


def _courses() -> list[dict]:
    """Load all courses"""
    return _load_json("courses.json")


def _identity() -> dict:
    """Load identity database"""
    return _load_json("identity.json")


def _user(user_id: str) -> dict:
    """Get user by ID"""
    users = _identity().get("users", [])
    user = next((u for u in users if u["id"] == user_id), None)
    if not user:
        raise ValueError(f"Unknown user: {user_id}")
    return user


# ─── Audit Logging ──────────────────────────────────────────────────────────

def _audit(user_id: str, tool: str, args: dict, allowed: bool, **extra) -> None:
    """Write audit log entry"""
    entry = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "user": user_id,
        "tool": tool,
        "args": args,
        "allowed": allowed,
        **extra
    }
    AUDIT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(AUDIT_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")


# ─── Scope Enforcement ──────────────────────────────────────────────────────

def _in_scope(user: dict, assignment: dict | None, course_id: str | None = None) -> bool:
    """Check if user has access to this assignment or course"""
    role = user.get("role")

    if role == "admin":
        return True  # Admins see everything

    if assignment:
        # Students: only their own assignments
        if role == "student":
            return assignment.get("student_id") == user.get("student_id")

        # Teachers: only their classes' assignments
        if role == "teacher":
            course = assignment.get("course_id")
            return course in user.get("classes", [])

        # Parents: only their children's assignments
        if role == "parent":
            return assignment.get("student_id") in user.get("children", [])

    if course_id:
        # Check course access
        if role == "student" or role == "teacher":
            return course_id in user.get("classes", [])
        if role == "parent":
            # Parents can see courses their children are in
            children = user.get("children", [])
            students = _students()
            for child_id in children:
                child = next((s for s in students if s["id"] == child_id), None)
                if child and course_id in child.get("classes", []):
                    return True
            return False

    return False


def _scoped_assignment(user: dict, assignment_id: str, tool: str, args: dict) -> dict:
    """Get assignment if in scope, otherwise raise Denied"""
    assignment = next((a for a in _assignments() if a["id"] == assignment_id), None)

    if not assignment or not _in_scope(user, assignment):
        reason = f"assignment {assignment_id} not found in your scope"
        _audit(user["id"], tool, args, allowed=False, reason=reason)
        raise Denied(reason)

    return assignment


# ─── API Functions ──────────────────────────────────────────────────────────

def get_assignment(user: str, assignment_id: str) -> dict:
    """Get a single assignment by ID"""
    u = _user(user)
    args = {"assignment_id": assignment_id}
    assignment = _scoped_assignment(u, assignment_id, "get_assignment", args)
    _audit(u["id"], "get_assignment", args, allowed=True, rows_returned=1)
    return json.loads(json.dumps(assignment))  # Deep copy


def list_assignments(user: str, status: str | None = None, due_before: str | None = None,
                    course_id: str | None = None, limit: int = 50) -> list[dict]:
    """List assignments visible to the user"""
    u = _user(user)
    args = {"status": status, "due_before": due_before, "course_id": course_id, "limit": limit}

    # Filter by scope
    assignments = []
    for a in _assignments():
        if _in_scope(u, a):
            # Apply filters
            if status and a.get("status") != status:
                continue
            if due_before and a.get("due_date", "") > due_before:
                continue
            if course_id and a.get("course_id") != course_id:
                continue
            assignments.append(a)

    # Sort by due date, limit results
    assignments.sort(key=lambda x: x.get("due_date") or "9999-12-31")
    assignments = assignments[:limit]

    _audit(u["id"], "list_assignments", args, allowed=True, rows_returned=len(assignments))
    return json.loads(json.dumps(assignments))


def get_hint(user: str, assignment_id: str, problem_number: int, level: int = 1) -> dict:
    """Get a hint for a specific problem (may require teacher approval)"""
    u = _user(user)
    args = {"assignment_id": assignment_id, "problem_number": problem_number, "level": level}

    assignment = _scoped_assignment(u, assignment_id, "get_hint", args)

    # Find the problem
    problems = assignment.get("problems", [])
    problem = next((p for p in problems if p["number"] == problem_number), None)

    if not problem:
        raise Denied(f"Problem {problem_number} not found in assignment {assignment_id}")

    # Generate hint based on level
    hints = {
        1: f"Start by identifying the coefficients a, b, and c in the equation: {problem['text']}",
        2: f"For {problem['text']}, use the quadratic formula: x = (-b ± √(b² - 4ac)) / 2a",
        3: f"Calculate the discriminant (b² - 4ac) first. If it's positive, you'll have two real solutions."
    }

    hint_text = hints.get(level, hints[1])

    _audit(u["id"], "get_hint", args, allowed=True)

    return {
        "assignment_id": assignment_id,
        "problem_number": problem_number,
        "problem_text": problem["text"],
        "hint": hint_text,
        "level": level,
        "requires_approval": assignment.get("type") == "graded"
    }


def submit_work(user: str, assignment_id: str, answers: dict) -> dict:
    """Submit work for an assignment"""
    u = _user(user)
    args = {"assignment_id": assignment_id, "answers": answers}

    # Only students can submit
    if u.get("role") != "student":
        reason = "only students can submit work"
        _audit(u["id"], "submit_work", args, allowed=False, reason=reason)
        raise Denied(reason)

    assignment = _scoped_assignment(u, assignment_id, "submit_work", args)

    # Update state
    state = _load_json("state.json")
    if "submissions" not in state:
        state["submissions"] = {}

    submission_id = f"SUB-{assignment_id}-{u['student_id']}"
    state["submissions"][submission_id] = {
        "assignment_id": assignment_id,
        "student_id": u["student_id"],
        "answers": answers,
        "submitted_at": datetime.utcnow().isoformat() + "Z",
        "status": "submitted"
    }

    # Update assignment status
    if "assignments" not in state:
        state["assignments"] = {}
    if assignment_id not in state["assignments"]:
        state["assignments"][assignment_id] = {}
    state["assignments"][assignment_id]["status"] = "submitted"
    state["assignments"][assignment_id]["submitted_date"] = datetime.utcnow().isoformat()[:10]

    _save_json("state.json", state)
    _audit(u["id"], "submit_work", args, allowed=True)

    return {
        "success": True,
        "submission_id": submission_id,
        "message": "Work submitted successfully"
    }


def get_course(user: str, course_id: str) -> dict:
    """Get course information"""
    u = _user(user)
    args = {"course_id": course_id}

    if not _in_scope(u, None, course_id):
        reason = f"course {course_id} not in your scope"
        _audit(u["id"], "get_course", args, allowed=False, reason=reason)
        raise Denied(reason)

    course = next((c for c in _courses() if c["id"] == course_id), None)
    if not course:
        raise Denied(f"course {course_id} not found")

    _audit(u["id"], "get_course", args, allowed=True)
    return json.loads(json.dumps(course))


def get_syllabus(user: str, course_id: str) -> dict:
    """Get course syllabus"""
    u = _user(user)
    course = get_course(user, course_id)  # Reuses scope check
    return {
        "course_id": course_id,
        "course_name": course["name"],
        "syllabus": course.get("syllabus", {})
    }


def get_schedule(user: str, course_id: str | None = None) -> list[dict]:
    """Get class schedule"""
    u = _user(user)
    args = {"course_id": course_id}

    classes = u.get("classes", [])
    if course_id:
        if course_id not in classes:
            reason = f"course {course_id} not in your schedule"
            _audit(u["id"], "get_schedule", args, allowed=False, reason=reason)
            raise Denied(reason)
        classes = [course_id]

    courses = _courses()
    schedule = []
    for course_id in classes:
        course = next((c for c in courses if c["id"] == course_id), None)
        if course:
            schedule.append({
                "course_id": course["id"],
                "course_name": course["name"],
                "schedule": course.get("schedule", ""),
                "teacher_id": course.get("teacher_id")
            })

    _audit(u["id"], "get_schedule", args, allowed=True, rows_returned=len(schedule))
    return schedule


def search_resources(user: str, topics: list[str] | None = None, resource_type: str | None = None,
                     limit: int = 10) -> list[dict]:
    """Search for learning resources"""
    u = _user(user)
    args = {"topics": topics, "resource_type": resource_type, "limit": limit}

    resources = _resources()
    results = []

    for r in resources:
        # Filter by type
        if resource_type and r.get("type") != resource_type:
            continue

        # Filter by topics (match any)
        if topics:
            resource_topics = r.get("topics", [])
            if not any(t in resource_topics for t in topics):
                continue

        results.append(r)

    results = results[:limit]
    _audit(u["id"], "search_resources", args, allowed=True, rows_returned=len(results))
    return json.loads(json.dumps(results))


def get_resource(user: str, resource_id: str) -> dict:
    """Get a specific learning resource"""
    u = _user(user)
    args = {"resource_id": resource_id}

    resource = next((r for r in _resources() if r["id"] == resource_id), None)
    if not resource:
        reason = f"resource {resource_id} not found"
        _audit(u["id"], "get_resource", args, allowed=False, reason=reason)
        raise Denied(reason)

    _audit(u["id"], "get_resource", args, allowed=True)
    return json.loads(json.dumps(resource))


def reset() -> None:
    """Reset state to clean slate (for testing)"""
    _save_json("state.json", {"assignments": {}, "submissions": {}, "hints_given": []})
