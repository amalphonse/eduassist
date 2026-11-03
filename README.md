# EduAssist 🎓

**An intelligent multi-agent AI tutoring system that helps students learn while maintaining academic integrity.**

Built during the [Modern AI Pro](https://modernaipro.com) Forward Deployed Engineer (FDE) course, EduAssist demonstrates production-grade AI agent architecture for educational applications.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![Docker](https://img.shields.io/badge/docker-enabled-blue.svg)](https://www.docker.com/)
[![AWS](https://img.shields.io/badge/AWS-deployed-orange.svg)](https://aws.amazon.com/)

![EduAssist Architecture](https://via.placeholder.com/800x400/1a1713/f6f4ef?text=EduAssist+Multi-Agent+Architecture)

## 🌟 Features

- **Multi-Agent Architecture**: Specialized agents for homework, course materials, and learning resources
- **Progressive Hint System**: Guides student thinking without giving away answers
- **Teacher Approval Gates**: All hints for graded work require teacher review
- **Role-Based Access**: Students, teachers, parents, and administrators each see appropriate data
- **FERPA Compliant**: Scope enforcement ensures students can't access other students' data
- **Academic Integrity**: Fuzzy matching helps students find assignments, hints never provide complete answers
- **Audit Logging**: Every action logged for compliance and analytics
- **Auto-Scaling Ready**: Containerized for deployment on AWS, Azure, or GCP

## 🚀 Quick Start

### Local Development

```bash
# Install dependencies
pip install -r requirements-graph.txt

# Configure environment
cp .env.example .env
# Edit .env with your OpenAI API key

# Run as a student
python eduassist_main.py --as student.john

# Or run web interface
python eduassist_main.py --as student.john --web
# Access at: http://127.0.0.1:7867
```

### Docker Deployment

```bash
# Build
docker build -t eduassist .

# Run
docker run -d -p 7867:7867 \
  -e OPENAI_API_KEY=your-key \
  -e CHAT_SECRET=$(openssl rand -hex 24) \
  eduassist
```

### AWS Deployment

```bash
# One-command deployment to AWS ECR + EC2
./deploy-ec2.sh

# Or use provided scripts for App Runner
# See AWS_DEPLOYMENT.md for details
```

## 🏗️ Architecture

EduAssist uses a **multi-agent router architecture** where each specialist handles a specific domain:

```
                  ┌──────────┐
   Student    ──→ │  Router  │──→ Homework Specialist (hints, assignments)
   /Teacher       │          │──→ Course Specialist (syllabus, schedule)
   /Parent        │          │──→ Library Specialist (videos, articles)
                  │          │──→ Answer Synthesizer
                  └──────────┘
```

**Key Components:**
- **MCP Server**: School data API with scope enforcement
- **LangGraph Agents**: Specialized agents with domain-specific tools
- **Teacher Gate**: Human-in-the-loop approval for sensitive operations
- **Scope Enforcement**: Data access controlled at the API layer (not prompts)

See [ARCHITECTURE.md](./ARCHITECTURE.md) for detailed technical documentation.

## 🎯 Use Cases

### For Students
```
"What homework do I have this week?"
"I'm stuck on problem 5 in my quadratic equations"
"Find me videos about photosynthesis"
"When is my next Math class?"
```

### For Teachers
- Review and approve AI-generated hints before students see them
- Monitor student questions and identify knowledge gaps
- Access class-wide assignment analytics

### For Parents
- View child's homework and upcoming assignments (read-only)
- Monitor academic progress
- Stay informed about class schedules

## 📊 Sample Data

Includes realistic sample data for demonstration:
- **3 students** across grade 10-11
- **5 assignments** (Math, English, Science)
- **3 courses** with syllabi and schedules
- **6 learning resources** (videos, articles, practice problems)
- **8 user roles** (students, teachers, parents, admin)

## 🔐 Security & Privacy

- **FERPA Compliant**: Students can only access their own data
- **Role-Based Access Control**: Teachers, parents, and admins have appropriate scopes
- **Audit Logging**: All actions logged to `data/audit.jsonl`
- **Secret Management**: API keys and secrets via environment variables only
- **HTTPS Ready**: Deploy with SSL via AWS ALB or CloudFlare

## 🛠️ Technology Stack

- **Python 3.12+**: Core application
- **LangGraph**: Multi-agent orchestration
- **LangChain**: Agent framework and tool integration
- **MCP Protocol**: Tool communication standard
- **Docker**: Containerization
- **AWS ECR + EC2**: Production deployment
- **Rich**: Terminal UI

## 📚 Documentation

- [ARCHITECTURE.md](./ARCHITECTURE.md) - Technical architecture and design decisions
- [DESIGN.md](./DESIGN.md) - System design, data models, and features
- [QUICKSTART.md](./QUICKSTART.md) - 5-minute getting started guide
- [AWS_DEPLOYMENT.md](./AWS_DEPLOYMENT.md) - AWS deployment guide
- [DEPLOYMENT.md](../DEPLOYMENT.md) - General deployment guide

## 🧪 Testing

```bash
# Run test suite
python test_eduassist.py

# Expected output:
# ✓ MCP server started successfully
# ✓ Found 9 tools
# ✓ Scope enforcement working
# All tests passed!
```

## 💰 Cost Estimates

**Development/Testing:**
- Local: Free (uses your OpenAI API key)
- Docker: Free (run on your machine)

**Production (AWS):**
- EC2 t3.small: ~$17-20/month (if running 24/7)
- Stop when not in use: ~$1/month (storage only)
- App Runner: ~$5-15/month (auto-scaling)

See cost calculator in `DESIGN.md`

## 🎓 About Modern AI Pro FDE

This project was built during the **Forward Deployed Engineer** course at [Modern AI Pro](https://modernaipro.com), which teaches production-grade AI system design and deployment **inside real customer environments**.

### The FDE Methodology Demonstrated

**1. Customer Discovery & Pain Point Analysis**

Before writing any code, we conducted discovery interviews with our simulated customer (Calder & Rowe service desk):

**Pain Points Identified:**
- Service desk receives 600 tickets/quarter with 19-hour first response time
- Agents spend hours looking up orders, policies, and ticket history
- Manual copy-paste between systems leads to errors
- No way to ensure consistent policy application
- Junior agents need senior approval but seniors are bottlenecked

**Customer Requirements:**
- Must integrate with existing ticketing system (via MCP)
- Cannot compromise security or data access controls
- Must respect organizational scope (regions, roles, PII)
- Needs human approval for anything that moves money
- Should reduce response time while maintaining quality

EduAssist adapted this **exact same methodology** for education:

**Education Pain Points:**
- Students stuck on homework wait hours/days for teacher help
- Teachers overwhelmed answering the same questions repeatedly
- Risk of AI giving complete answers (academic integrity)
- Parents want visibility but shouldn't access other students' data
- Need to track what students struggle with for intervention

**2. The Wedge - Smallest Valuable Deployment**

Rather than building everything, we focused on the **wedge**: the smallest deployment that proves value.

For EduAssist:
- ✅ Read ticket/assignment → Find context → Draft hint/response
- ✅ Teacher approval gate for sensitive operations
- ✅ Scope enforcement (students can't see others' work)
- ❌ NOT building: grading system, full LMS, mobile app (yet)

**3. Eval Contract - Testing as the Agreement**

We don't ship without evals. The eval contract defines "done":

**Eval Layers Implemented:**
```python
# Layer 1: Tool Access (Scope Enforcement)
✓ Student.john can access A-5001 (his assignment)
✗ Student.john cannot access A-5005 (Jane's assignment)

# Layer 2: Retrieval Quality
✓ "quadratic equations homework" → finds A-5001
✓ Fuzzy matching: "homework 3775" → suggests "A-5075"

# Layer 3: Hint Quality (Academic Integrity)
✓ Hint guides thinking without giving answer
✗ Never provides complete solution to graded work
✓ Progressive hints (level 1→2→3) increase detail

# Layer 4: Routing Accuracy
✓ "What homework do I have?" → homework specialist
✓ "Find videos about photosynthesis" → library specialist
✓ "When is my next class?" → course specialist

# Layer 5: Safety & Compliance
✓ Teacher approval required for graded work hints
✓ Audit log captures all student interactions
✓ FERPA: scope enforced at data layer, not prompts
```

**Frozen Golden Set:**
- 50 test cases covering all user roles and edge cases
- Documented in `test_eduassist.py`
- Must pass before any deployment

**4. Memory & State Management**

EduAssist implements **stateful conversations** with proper memory:

**Conversation State (LangGraph MemorySaver):**
```python
# Each student gets isolated conversation thread
thread_id = "student-john-session-123"

# State persists across turns:
- Previous questions asked
- Hints already provided
- Which assignments discussed
- Teacher approval history
```

**Application State:**
```json
// data/state.json - Runtime modifications
{
  "assignments": {
    "A-5001": {
      "status": "submitted",  // Student submitted
      "submitted_date": "2026-11-03"
    }
  },
  "hints_given": [
    {
      "student": "S-1001",
      "assignment": "A-5001",
      "problem": 5,
      "level": 2,  // Remember: already gave level 1 & 2
      "approved_by": "teacher.smith"
    }
  ]
}
```

**Memory Challenges Solved:**
- ✅ Students can't game system by re-asking same question
- ✅ Teachers see history of hints already provided
- ✅ System remembers context across multi-turn conversations
- ✅ Checkpointing allows conversation resume after interruptions

**5. Course Topics Demonstrated:**
- ✅ **Discovery**: Customer interviews → Pain points → Requirements
- ✅ **Wedge Strategy**: Smallest valuable deployment first
- ✅ **Multi-agent architecture**: Router + Specialists pattern
- ✅ **MCP Integration**: Customer's data stays in their system
- ✅ **Eval Contract**: Testing defines "done", not demos
- ✅ **Human-in-the-loop**: Teacher approval gates
- ✅ **Scope enforcement**: Security at data layer
- ✅ **Memory management**: Stateful conversations with LangGraph
- ✅ **Production deployment**: AWS EC2 with monitoring
- ✅ **Audit logging**: Compliance and analytics
- ✅ **Cost optimization**: Right-sized instances, stop when idle

### Real FDE Workflow Applied

```
Week 1: Discovery
├─ Interview stakeholders (teachers, students, parents)
├─ Map current workflow and pain points
├─ Identify wedge (hint system + teacher approval)
└─ Write engagement brief with ROI

Week 2: Build & Eval
├─ Implement wedge (multi-agent hint system)
├─ Write eval contract (50 test cases)
├─ Iterate until evals pass
└─ Integration map showing MCP architecture

Week 3: Deploy & Operate
├─ Deploy to AWS (EC2 with Docker)
├─ Teacher pilots with approval gate
├─ Monitor audit logs and fix edge cases
└─ Handover documentation

Week 4: Expand
├─ Based on usage data, add library specialist
├─ Improve hint quality based on teacher feedback
└─ Scale to more classes
```

This is **exactly how FDEs work** - embedded with customers, iterating based on real usage, with evals as the contract.

## 🤝 Contributing

Contributions welcome! This is an educational project demonstrating real-world AI agent patterns.

**Ideas for contributions:**
- Additional subjects/courses beyond Math, English, Science
- Grading system integration
- Learning analytics dashboard
- Mobile app interface
- Speech-to-text for accessibility
- Multi-language support

## 📄 License

MIT License - feel free to use this as a learning resource or foundation for your own projects.

## 🙏 Acknowledgments

- **Modern AI Pro** - For the excellent FDE course curriculum
- **Anthropic** - For Claude API and MCP protocol
- **LangChain/LangGraph** - For agent orchestration framework

## 📞 Contact

Built by **Anju Chinniah** ([anju.chinniah@gmail.com](mailto:anju.chinniah@gmail.com))

---

⭐ If you found this helpful, please star this repo!

**Live Demo**: [http://77.114.12.252:7867/?k=d2a2258b669a448dad94ffd9c5603274adbc73d3812ae25d](http://77.114.12.252:7867/?k=d2a2258b669a448dad94ffd9c5603274adbc73d3812ae25d)

*Part of the Modern AI Pro FDE Field Kit - demonstrating production AI agent deployment*
