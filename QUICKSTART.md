# EduAssist - Quick Start Guide

Get EduAssist running in 5 minutes!

## Prerequisites

- Python 3.12+ installed
- Docker installed (for containerized deployment)
- OpenAI API key configured in parent `.env` file

## Option 1: Run Directly (Fastest)

```bash
# Install dependencies (if not already installed)
pip install -r requirements-graph.txt

# Run in terminal mode as a student
python eduassist/eduassist_main.py --as student.john

# Or run in web mode
python eduassist/eduassist_main.py --as student.john --web
# Access at: http://127.0.0.1:7867
```

### Try Different Users:

```bash
# As a teacher (can approve hints)
python eduassist/eduassist_main.py --as teacher.smith --web

# As a parent (read-only access to their child)
python eduassist/eduassist_main.py --as parent.doe --web

# As admin (full access)
python eduassist/eduassist_main.py --as admin.principal --web
```

## Option 2: Docker Deployment

```bash
# Make sure Docker is running, then:
cd eduassist
./deploy-local.sh

# This will:
# - Build the Docker image
# - Start the container
# - Show you the access URL with CHAT_SECRET
```

## Sample Questions to Try

### As a Student:

1. **Homework Help:**
   ```
   What homework do I have this week?
   I'm stuck on problem 5 in my quadratic equations homework
   Can you give me a hint for problem 3?
   ```

2. **Course Information:**
   ```
   What's my class schedule?
   What topics are we covering in Biology?
   When is my next Math class?
   ```

3. **Learning Resources:**
   ```
   Can you find me videos about quadratic equations?
   I need practice problems for factoring
   Show me resources about photosynthesis
   ```

### As a Teacher:

1. **Review Student Work:**
   ```
   What assignments are due this week?
   Show me assignments for MATH-101
   ```

2. **Approve Hints:**
   - When running as a teacher, you'll see hint approval requests
   - You can approve, modify, or reject hints before students see them

### As a Parent:

```
What is my child's homework this week?
What classes is John taking?
How is my child doing in Math?
```

## Understanding the Multi-Agent System

When you ask a question, watch the routing:

```
You: "I'm stuck on problem 5 in my quadratic equations homework"

Router → homework specialist
  homework → list_assignments()
  homework → get_assignment(A-5001)
  homework → get_hint(problem=5)
  [TEACHER APPROVAL GATE]
  Teacher approves → hint shown
Router → answer
  EduAssist → "Here's a hint for problem 5..."
```

## The Three Blanks (Already Configured)

1. **ROUTING_RULES** - Routes homework questions to homework specialist, course questions to course specialist, resource requests to library specialist

2. **needs_teacher()** - All hints require teacher approval (protecting academic integrity)

3. **MAX_HOPS** - Set to 3 (students often need homework + course + resources)

## Data Files

All sample data is in `eduassist/data/`:
- 3 students (John, Jane, Bob)
- 5 assignments (Math, English, Science)
- 6 learning resources (videos, articles, practice)
- 3 courses (Algebra II, American Lit, Biology)
- 8 users with different roles

## Modifying the System

### Add More Students:
Edit `eduassist/data/students.json` and `identity.json`

### Add More Assignments:
Edit `eduassist/data/assignments.json`

### Add Learning Resources:
Edit `eduassist/data/resources.json`

### Change Routing Rules:
Edit `ROUTING_RULES` in `eduassist/eduassist_main.py`

### Change Approval Requirements:
Edit `needs_teacher()` function in `eduassist/eduassist_main.py`

## Troubleshooting

### "missing package" error:
```bash
pip install -r requirements-graph.txt
```

### "school server did not start":
- Check that all data files exist in `eduassist/data/`
- Verify Python path is correct
- Check stderr output for errors

### Can't access web interface:
- Make sure port 7867 is not in use
- Check that CHAT_SECRET is set for non-localhost hosts
- Try: `curl http://127.0.0.1:7867` to verify server is running

### Permission denied errors:
- Make sure deployment script is executable: `chmod +x deploy-local.sh`

## Next Steps

1. **Try all user roles** - See how scope enforcement works
2. **Add your own data** - Create realistic students and assignments
3. **Customize prompts** - Adjust specialist prompts for your needs
4. **Deploy to AWS** - Follow DEPLOYMENT.md for cloud deployment
5. **Add features** - Implement grading, analytics, study plans, etc.

## Architecture Overview

```
eduassist_main.py         → Multi-agent graph (router + specialists)
_school.py                → API with scope enforcement
school_mcp.py             → MCP server exposing tools
data/*.json               → Student/assignment/resource data
_chat_web.py              → Web interface (from lab 2b)
_mcp_client.py            → MCP client (from lab 2b)
```

## Support

For issues or questions, refer to:
- `DESIGN.md` - Full architecture documentation
- `README.md` - Project overview and status
- Original lab 2b code in `../labs/lab_2b_multiagent.py`

---

**Ready to try it?**

```bash
python eduassist/eduassist_main.py --as student.john --web
```

Then visit http://127.0.0.1:7867 and start asking questions!
