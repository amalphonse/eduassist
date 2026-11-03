# EduAssist container - Multi-agent student support system
#
# Build and run:
#   docker build -t eduassist -f eduassist/Dockerfile .
#   docker run --rm -p 7867:7867 \
#     -e OPENAI_API_KEY=<your key> \
#     -e OPENAI_BASE_URL=https://learn.modernaipro.com/api/llm/v1 \
#     -e CHAT_SECRET=<random string> \
#     -e SCHOOL_USER=student.john \
#     eduassist
#
# Open http://127.0.0.1:7867/?k=<CHAT_SECRET>

FROM python:3.12-slim
WORKDIR /app

# Install dependencies
COPY requirements.txt requirements-graph.txt ./
RUN pip install --no-cache-dir -r requirements-graph.txt

# Copy EduAssist application
COPY eduassist/ eduassist/

# Environment defaults
ENV SCHOOL_USER=student.john
ENV MAI_CLASSIFY=0
ENV MAI_TRACE=0

# Expose port
EXPOSE 7867

# Run the application
CMD ["python", "eduassist/eduassist_main.py", "--web", "--host", "0.0.0.0", "--port", "7867"]
