# EduAssist - Multi-Agent Student Support System

**Built on Lab 2b Architecture Principles**

## Overview

EduAssist is a multi-agent AI tutor that helps students with homework, course materials, and learning resources. It reuses the proven architecture from lab 2b (Calder & Rowe service desk) but adapted for education.

## Architecture

### The Same Patterns, Different Domain

| Lab 2b (Service Desk) | EduAssist (Education) |
|---|---|
| Router → Orders/Policy/Desk specialists | Router → Homework/Course/Library specialists |
| Ticket lookup with fuzzy matching | Assignment lookup with smart search |
| Scope enforcement (regions) | Scope enforcement (grade levels, classes) |
| Human approval for refunds/credits | Teacher approval for answers/feedback |
| Audit log of all actions | Learning analytics log |
| MCP server for estate data | MCP server for student data |

### The Multi-Agent Graph

```
                  ┌──────────┐
   student    ──→ │  router  │──→ homework   (get_assignment · list_assignments · submit_work · get_hint)
   /teacher       │ (1 call) │──→ course     (get_syllabus · get_schedule · get_materials)
   /parent        │          │──→ library    (search_resources · get_video · get_article)
                  │          │──→ answer     (no tools: reply with what specialists found)
                  └──────────┘
        specialists hand back to router; router counts hops against MAX_HOPS
```

### User Roles & Scopes

| Role | Can Read | Can Write | Scope |
|---|---|---|---|
| `student.john` | Own assignments, grades, resources | Submit homework, ask questions | Own classes only |
| `teacher.smith` | All students in their classes | Grade, provide feedback, approve hints | Their classes only |
| `parent.doe` | Own child's data only | Nothing (read-only) | Own child only |
| `admin.principal` | Everything | Manage courses, users, approve teacher actions | School-wide |

### The Three Blanks (Same as Lab 2b)

**Blank 1: ROUTING_RULES**
```python
ROUTING_RULES = """
Route to 'homework' for questions about assignments, problem-solving, hints, or submissions.
Route to 'course' for questions about syllabus, schedule, course materials, or what's coming up.
Route to 'library' for requests for learning resources, videos, articles, or study materials.
Route to 'answer' if the question is just a greeting, thanks, or doesn't need any tools.
If a student asks for complete answers to graded work, route to 'answer' with a refusal
  (offer hints instead).
"""
```

**Blank 2: needs_teacher()**
```python
def needs_teacher(tool_name: str, args: dict) -> bool:
    # Hints and answers for graded assignments must be approved by teacher
    if tool_name == "get_hint" and args.get("assignment_type") == "graded":
        return True
    if tool_name == "submit_work":
        return False  # Students can submit freely
    # Any destructive action needs approval
    return RISK.get(tool_name, "destructive") != "read"
```

**Blank 3: MAX_HOPS**
```python
MAX_HOPS = 3  # Students often need homework + course materials + library resources
```

## Data Model

### Students Table
```json
{
  "id": "S-1001",
  "name": "John Doe",
  "grade": "10",
  "classes": ["MATH-101", "ENG-201", "SCI-301"],
  "parent_id": "P-2001"
}
```

### Assignments Table
```json
{
  "id": "A-5001",
  "course_id": "MATH-101",
  "title": "Quadratic Equations Practice",
  "type": "graded|practice",
  "due_date": "2026-11-15",
  "status": "assigned|submitted|graded",
  "points": 100,
  "topics": ["algebra", "quadratics"],
  "student_id": "S-1001"
}
```

### Learning Resources Table
```json
{
  "id": "R-3001",
  "title": "Quadratic Formula Explained",
  "type": "video|article|practice",
  "url": "https://...",
  "topics": ["algebra", "quadratics"],
  "grade_level": "9-12"
}
```

## The Gate: Teacher Approval

When a student asks for a hint on graded work:

1. **AI generates hint** - The homework specialist crafts an appropriate hint
2. **Gate interrupts** - Graph pauses before showing hint to student
3. **Teacher reviews** - Teacher sees: student name, question, proposed hint
4. **Approve/Modify/Reject** - Teacher can approve as-is, modify it, or reject
5. **Student receives** - Only after approval does the student see the hint

## Reusable Components from Lab 2b

### Direct Reuse (copy as-is):
- `_chat_web.py` - The chat page (works perfectly for students)
- `_mcp_client.py` - MCP client for tools
- Graph structure from `build_graph()` - Router, specialists, answer node
- Gate mechanism `_gated()` - Human-in-the-loop approval
- `Runner` class - MCP session, event loop, checkpointing

### Adapted (same pattern, different domain):
- `_estate.py` → `_school.py` - Scope enforcement for students/teachers/parents
- `estate_mcp.py` → `school_mcp.py` - MCP server for student data
- `SPECIALISTS` - Different tools (homework/course/library vs orders/policy/desk)

### Dockerfile (minimal changes):
```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt requirements-graph.txt ./
RUN pip install --no-cache-dir -r requirements-graph.txt
COPY eduassist/ eduassist/
COPY school_data/ school_data/
ENV MAI_CLASSIFY=0 MAI_TRACE=0 SCHOOL_STATE_DIR=/tmp/school SCHOOL_USER=student.john
EXPOSE 7867
CMD ["python", "eduassist/eduassist_main.py", "--web", "--host", "0.0.0.0", "--port", "7867"]
```

## Deployment

Same as lab 2b:
```bash
docker build -t eduassist .
docker run --rm -p 7867:7867 \
  -e OPENAI_API_KEY=<your-key> \
  -e OPENAI_BASE_URL=https://learn.modernaipro.com/api/llm/v1 \
  -e CHAT_SECRET=$(openssl rand -hex 24) \
  eduassist
```

Access at: `http://127.0.0.1:7867/?k=<CHAT_SECRET>`

## Key Innovations Beyond Lab 2b

1. **Hint System** - Progressive hints that don't give away the answer
2. **Learning Analytics** - Track which topics students struggle with
3. **Parent Dashboard** - Parents can see (not modify) their child's progress
4. **Adaptive Difficulty** - Based on student performance, suggest easier/harder resources
5. **Plagiarism Detection** - Flag when submitted work looks AI-generated

## Security & Privacy

Following lab 2b's security model:

1. **Scope at the data layer** - Students can't access other students' work
2. **Role-based permissions** - Enforced in `_school.py`, not in prompts
3. **Audit logging** - Every action logged for review
4. **FERPA compliance** - Student data never in prompts to external LLMs
5. **Teacher approval gate** - Prevents AI from giving inappropriate help

## Example Interactions

**Student asks for help:**
```
Student: "I'm stuck on problem 5 in my quadratic equations homework"

Router → homework specialist
Homework → get_assignment(student="S-1001", topic="quadratic")
Homework → get_hint(assignment="A-5001", problem=5, level=1)
[GATE] Teacher reviews hint before it's shown
Teacher: APPROVED
Answer → "Here's a hint: Remember that the quadratic formula is..."
```

**Student asks for course schedule:**
```
Student: "What do I have for homework this week?"

Router → homework specialist + course specialist
Homework → list_assignments(student="S-1001", due_before="2026-11-08")
Course → get_schedule(student="S-1001", week="current")
Answer → "This week you have: 1) Math homework due Friday..."
```

## Success Metrics

- **Student engagement** - Time spent, questions asked
- **Teacher efficiency** - Time saved on routine questions
- **Learning outcomes** - Grade improvements in classes using EduAssist
- **Teacher approval rate** - % of AI hints approved without modification
- **Student satisfaction** - Survey scores

## Future Enhancements

1. **Speech interface** - Students can ask questions verbally
2. **Handwriting recognition** - Upload photos of math problems
3. **Study group mode** - Multiple students collaborate with AI facilitation
4. **Assessment generation** - Teachers can generate practice problems
5. **Personalized study plans** - AI creates week-by-week learning plans

## Cost Estimate (using Lab 1a patterns)

Per student per month:
- **Model calls**: ~300 questions × $0.003 = $0.90
- **Embeddings**: ~100 resource searches × $0.0001 = $0.01
- **Fixed costs**: Infrastructure, storage = $1.00
- **Total**: ~$2/student/month

At 1000 students: $2000/month = $24,000/year

ROI: If each teacher saves 2 hours/week on answering routine questions:
- 5 teachers × 2 hours × 40 weeks × $50/hour = $20,000/year
- Break-even at 1000 students with positive ROI from year 1
