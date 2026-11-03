# EduAssist - Multi-Agent Student Support System

**Status: Core architecture complete, ready for final assembly**

## What's Been Built

### ✅ Complete Components

1. **Data Model** (`eduassist/data/`)
   - `students.json` - Student records with classes and grades
   - `assignments.json` - Homework with problems, due dates, grading
   - `resources.json` - Learning materials (videos, articles, practice)
   - `courses.json` - Course information, syllabi, schedules
   - `identity.json` - Users (students, teachers, parents, admins) with roles
   - `state.json` - Runtime state for submissions and modifications

2. **School API** (`eduassist/_school.py`)
   - Scope enforcement (students see only their work, teachers only their classes)
   - Audit logging (every action logged for compliance)
   - Risk tags (read/write/destructive operations)
   - Functions:
     - `get_assignment()`, `list_assignments()`
     - `get_hint()` - with teacher approval for graded work
     - `submit_work()` - students submit answers
     - `get_course()`, `get_syllabus()`, `get_schedule()`
     - `search_resources()`, `get_resource()`

3. **MCP Server** (`eduassist/school_mcp.py`)
   - Exposes school API as MCP tools
   - Denials return as text (agents can read and re-plan)
   - Acts as specific user (`--as student.john`)

4. **Architecture Design** (`eduassist/DESIGN.md`)
   - Complete system design
   - Reusable components from lab 2b mapped
   - Security & privacy considerations
   - Cost estimates and ROI calculations

## Next Steps to Complete

### 1. Copy Reusable Files from Labs

```bash
cd /Users/anjuma/fde/mai-fde-labs

# Copy the chat web page (works as-is)
cp labs/_chat_web.py eduassist/

# Copy the MCP client  (works as-is)
cp labs/_mcp_client.py eduassist/

# Copy kit utilities
cp labs/_kit.py eduassist/
```

### 2. Create the Main EduAssist Application

Create `eduassist/eduassist_main.py` based on `labs/lab_2b_multiagent.py`:

**Key changes from lab 2b:**
- SPECIALISTS = {
    "homework": ["get_assignment", "list_assignments", "get_hint", "submit_work"],
    "course": ["get_course", "get_syllabus", "get_schedule"],
    "library": ["search_resources", "get_resource"]
  }
- ROUTING_RULES tailored for education
- needs_teacher() function for approval gate
- MAX_HOPS = 3 (students often need multiple resources)

### 3. Create Deployment Files

**`eduassist/Dockerfile`:**
```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt requirements-graph.txt ./
RUN pip install --no-cache-dir -r requirements-graph.txt
COPY eduassist/ eduassist/
ENV SCHOOL_USER=student.john
EXPOSE 7867
CMD ["python", "eduassist/eduassist_main.py", "--web", "--host", "0.0.0.0", "--port", "7867"]
```

**`eduassist/.env.example`:**
```bash
OPENAI_API_KEY=your-key-here
OPENAI_BASE_URL=https://learn.modernaipro.com/api/llm/v1
SCHOOL_USER=student.john
CHAT_SECRET=generate-with-openssl-rand
```

### 4. Test Locally

```bash
# Terminal mode
python eduassist/eduassist_main.py --as student.john

# Web mode
python eduassist/eduassist_main.py --web --as student.john
# Access at http://127.0.0.1:7867

# As different users
python eduassist/eduassist_main.py --web --as teacher.smith
python eduassist/eduassist_main.py --web --as parent.doe
```

### 5. Deploy to AWS

Same process as lab 2b:

```bash
# Build
docker build -t eduassist eduassist/

# Push to ECR
aws ecr create-repository --repository-name eduassist --region us-east-2
docker tag eduassist:latest <account>.dkr.ecr.us-east-2.amazonaws.com/eduassist:latest
docker push <account>.dkr.ecr.us-east-2.amazonaws.com/eduassist:latest

# Deploy to App Runner or EC2 (see DEPLOYMENT.md in eduassist/)
```

## Example Interactions

**Student asks for help:**
```
Student John: "I'm stuck on problem 5 in my quadratic equations homework"

Router → homework specialist
Homework → list_assignments(student="student.john", course="MATH-101")
Homework → get_assignment(assignment_id="A-5001")
Homework → get_hint(assignment="A-5001", problem=5, level=1)
[GATE] Teacher Smith sees: "Hint for John Doe, Problem 5: Start by identifying a, b, c..."
Teacher: APPROVED
Answer → "Here's a hint for problem 5: Start by identifying the coefficients a, b, and c in your equation..."
```

**Student asks about homework:**
```
Student: "What homework do I have this week?"

Router → homework + course specialists
Homework → list_assignments(due_before="2026-11-08")
Course → get_schedule()
Answer → "This week you have:
  1. Quadratic Equations Practice (Math) - Due Nov 15
  2. To Kill a Mockingbird Essay (English) - Due Nov 20
  Your next class is Math on Monday at 9:00 AM."
```

## File Structure

```
eduassist/
├── README.md              # This file
├── DESIGN.md              # Full architecture design
├── _school.py             # ✅ School API with scope enforcement
├── school_mcp.py          # ✅ MCP server
├── eduassist_main.py      # TODO: Main multi-agent app
├── _chat_web.py           # TODO: Copy from labs
├── _mcp_client.py         # TODO: Copy from labs
├── _kit.py                # TODO: Copy from labs
├── Dockerfile             # TODO: Container config
├── .env.example           # TODO: Environment template
├── deploy.sh              # TODO: Deployment script
└── data/
    ├── students.json      # ✅ Student records
    ├── assignments.json   # ✅ Homework and assignments
    ├── resources.json     # ✅ Learning materials
    ├── courses.json       # ✅ Course information
    ├── identity.json      # ✅ Users and roles
    ├── state.json         # ✅ Runtime state
    └── audit.jsonl        # Auto-generated audit log
```

## Key Innovations

1. **Progressive Hints** - Multi-level hints that don't give away answers
2. **Teacher Gate** - All hints for graded work require teacher approval
3. **Scope Enforcement** - Students can't see other students' work (FERPA compliant)
4. **Fuzzy Matching** - Reuses lab 2b's fuzzy matching for assignment search
5. **Learning Analytics** - Audit log tracks which topics students struggle with

## Reused from Lab 2b

- ✅ Multi-agent router architecture (Router → Specialists → Answer)
- ✅ MCP server pattern (school_mcp.py based on estate_mcp.py)
- ✅ Scope enforcement at data layer (_school.py based on _estate.py)
- ✅ Human-in-the-loop gate (teacher approvals)
- ✅ Audit logging
- ✅ Chat web interface (_chat_web.py - copy as-is)
- ✅ Docker deployment pattern

## Would You Like Me To:

1. **Complete the implementation** - Create eduassist_main.py, copy files, build Dockerfile
2. **Deploy it locally** - Run it in web mode for testing
3. **Deploy to AWS** - Push to ECR and deploy to App Runner
4. **Add features** - Implement additional capabilities (parent dashboard, analytics, etc.)

Let me know which direction you'd like to go!
