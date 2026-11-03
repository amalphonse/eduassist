# Contributing to EduAssist

Thank you for your interest in contributing to EduAssist! This project was created as part of the Modern AI Pro FDE course to demonstrate production-grade AI agent architecture.

## 🎯 Project Goals

EduAssist aims to:
1. Demonstrate multi-agent AI architecture in education
2. Show best practices for scope enforcement and security
3. Provide a learning resource for AI agent development
4. Maintain academic integrity while helping students learn

## 🤝 How to Contribute

### Reporting Issues

- Check existing issues first to avoid duplicates
- Provide clear steps to reproduce bugs
- Include your environment (Python version, OS, etc.)
- Share relevant logs or error messages

### Suggesting Features

We welcome ideas that align with educational best practices:
- ✅ New subject areas (History, Languages, etc.)
- ✅ Accessibility improvements (speech-to-text, screen readers)
- ✅ Analytics and insights for teachers
- ✅ Integration with existing LMS platforms
- ❌ Features that compromise academic integrity
- ❌ Complete answer generators for graded work

### Code Contributions

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/your-feature-name`
3. **Make your changes**:
   - Follow existing code style
   - Add tests if applicable
   - Update documentation
4. **Test thoroughly**:
   ```bash
   python test_eduassist.py
   ```
5. **Commit with clear messages**:
   ```bash
   git commit -m "feat: add Spanish language support"
   ```
6. **Push and create a Pull Request**

### Coding Standards

- **Python Style**: Follow PEP 8
- **Type Hints**: Use type annotations where helpful
- **Documentation**: Add docstrings for new functions
- **Security**: Never commit API keys or secrets
- **Testing**: Ensure existing tests pass

### Project Structure

```
eduassist/
├── eduassist_main.py      # Main multi-agent application
├── _school.py             # School API with scope enforcement
├── school_mcp.py          # MCP server
├── data/                  # Sample data (JSON files)
├── tests/                 # Test files
└── docs/                  # Documentation
```

## 📚 Development Setup

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/eduassist.git
cd eduassist

# Install dependencies
pip install -r requirements-graph.txt

# Copy environment template
cp .env.example .env
# Add your OpenAI API key

# Run tests
python test_eduassist.py

# Run locally
python eduassist_main.py --as student.john --web
```

## 🎓 Learning Resources

Understanding the architecture:
- Read [ARCHITECTURE.md](./ARCHITECTURE.md) for technical details
- Read [DESIGN.md](./DESIGN.md) for system design
- Check the Modern AI Pro FDE course materials
- Review existing code and comments

## 🔐 Security Guidelines

- **Never** commit `.env` files or API keys
- **Always** validate user input
- **Always** enforce scope at the data layer
- **Never** trust data from external sources
- **Always** log security-relevant events

## 🧪 Testing Guidelines

- Write tests for new features
- Ensure tests cover edge cases
- Test with different user roles (student, teacher, parent)
- Verify scope enforcement works correctly

## 📝 Documentation

When adding features:
- Update relevant markdown files
- Add inline code comments for complex logic
- Include usage examples
- Update the main README.md if needed

## 💡 Ideas for Contributions

**Beginner-Friendly:**
- Add more sample data (students, courses, assignments)
- Improve error messages
- Add more learning resources
- Write additional tests

**Intermediate:**
- Add new subjects (History, Languages, etc.)
- Implement grading system
- Add analytics dashboard
- Mobile-friendly UI improvements

**Advanced:**
- LMS integration (Canvas, Blackboard, Moodle)
- Multi-tenant support
- Advanced analytics with ML insights
- Performance optimizations

## ✅ Pull Request Checklist

Before submitting:
- [ ] Code follows project style
- [ ] Tests pass (`python test_eduassist.py`)
- [ ] Documentation updated
- [ ] No API keys or secrets committed
- [ ] Commit messages are clear
- [ ] PR description explains the change

## 🙏 Questions?

- Open an issue for discussion
- Email: anju.chinniah@gmail.com
- Reference Modern AI Pro FDE course materials

## 📜 Code of Conduct

- Be respectful and professional
- Focus on constructive feedback
- Assume good intentions
- Help maintain a welcoming community

## 🎉 Recognition

Contributors will be acknowledged in:
- This CONTRIBUTING.md file
- The main README.md
- Project releases

Thank you for helping make EduAssist better! 🚀

---

*This project demonstrates production AI practices learned in the Modern AI Pro FDE course.*
