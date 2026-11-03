#!/bin/bash
# Local deployment script for EduAssist
# Builds and runs EduAssist as a Docker container

set -e

echo "=== EduAssist Local Deployment ==="
echo ""

# Check if .env exists (use parent directory's .env)
if [ ! -f ../.env ]; then
    echo "Error: ../.env file not found. Please copy .env.example to ../.env and configure."
    exit 1
fi

# Load environment variables
export $(cat ../.env | grep -v '^#' | xargs)

# Check API key
if [ -z "$OPENAI_API_KEY" ] || [ "$OPENAI_API_KEY" = "paste-your-mai-key-here" ]; then
    echo "Error: OPENAI_API_KEY not configured in ../.env"
    exit 1
fi

# Generate CHAT_SECRET if not set
if [ -z "$CHAT_SECRET" ]; then
    CHAT_SECRET=$(openssl rand -hex 24)
    echo "Generated CHAT_SECRET: $CHAT_SECRET"
fi

# Set default user if not specified
SCHOOL_USER=${SCHOOL_USER:-student.john}

echo ""
echo "Building Docker image..."
cd ..
docker build -t eduassist -f eduassist/Dockerfile .

echo ""
echo "Starting EduAssist container..."
docker run --rm -d \
  --name eduassist \
  -p 7867:7867 \
  -e OPENAI_API_KEY="$OPENAI_API_KEY" \
  -e OPENAI_BASE_URL="${OPENAI_BASE_URL:-https://learn.modernaipro.com/api/llm/v1}" \
  -e CHAT_SECRET="$CHAT_SECRET" \
  -e SCHOOL_USER="$SCHOOL_USER" \
  eduassist

# Wait for startup
echo "Waiting for server to start..."
sleep 5

echo ""
echo "=== EduAssist is Running! ==="
echo ""
echo "Access URL:"
echo "  http://127.0.0.1:7867/?k=$CHAT_SECRET"
echo ""
echo "Running as: $SCHOOL_USER"
echo ""
echo "Commands:"
echo "  View logs:  docker logs -f eduassist"
echo "  Stop:       docker stop eduassist"
echo ""
