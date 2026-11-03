#!/bin/bash
# AWS Deployment Script for EduAssist
# Deploys EduAssist to Amazon ECR and AWS App Runner

set -e

echo "=== EduAssist AWS Deployment ==="
echo ""

# Configuration
AWS_REGION="${AWS_REGION:-us-east-2}"
ECR_REPO_NAME="eduassist"
APP_NAME="eduassist"

# Check prerequisites
echo "Checking prerequisites..."

if ! command -v aws &> /dev/null; then
    echo "Error: AWS CLI not installed. Install it first:"
    echo "  https://docs.aws.amazon.com/cli/latest/userguide/install-cliv2.html"
    exit 1
fi

if ! command -v docker &> /dev/null; then
    echo "Error: Docker not installed or not running"
    exit 1
fi

# Check AWS credentials
if ! aws sts get-caller-identity &> /dev/null; then
    echo "Error: AWS credentials not configured or invalid"
    echo "Run: aws configure"
    exit 1
fi

echo "✓ AWS CLI installed and configured"
echo "✓ Docker available"

# Get AWS account ID
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
echo "✓ AWS Account: $AWS_ACCOUNT_ID"
echo "✓ Region: $AWS_REGION"
echo ""

# Load environment variables
if [ ! -f ../.env ]; then
    echo "Error: ../.env file not found. Please configure it first."
    exit 1
fi

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
    echo "IMPORTANT: Save this secret! You'll need it to access the web interface."
    echo ""
fi

echo "Step 1: Creating ECR Repository (if needed)..."
echo "------------------------------------------------------------"

# Create ECR repository if it doesn't exist
if aws ecr describe-repositories --repository-names "$ECR_REPO_NAME" --region "$AWS_REGION" &> /dev/null; then
    echo "✓ ECR repository '$ECR_REPO_NAME' already exists"
else
    echo "Creating ECR repository '$ECR_REPO_NAME'..."
    aws ecr create-repository \
        --repository-name "$ECR_REPO_NAME" \
        --region "$AWS_REGION" \
        --image-scanning-configuration scanOnPush=true
    echo "✓ ECR repository created"
fi

ECR_URI="$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPO_NAME"
echo "✓ ECR URI: $ECR_URI"
echo ""

echo "Step 2: Building Docker Image..."
echo "------------------------------------------------------------"

cd ..
docker build -t "$APP_NAME:latest" -f eduassist/Dockerfile .
echo "✓ Docker image built successfully"
echo ""

echo "Step 3: Pushing to Amazon ECR..."
echo "------------------------------------------------------------"

# Authenticate Docker to ECR
echo "Authenticating Docker to ECR..."
aws ecr get-login-password --region "$AWS_REGION" | \
    docker login --username AWS --password-stdin "$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com"
echo "✓ Docker authenticated to ECR"

# Tag and push image
echo "Tagging image..."
docker tag "$APP_NAME:latest" "$ECR_URI:latest"
docker tag "$APP_NAME:latest" "$ECR_URI:$(date +%Y%m%d-%H%M%S)"

echo "Pushing to ECR..."
docker push "$ECR_URI:latest"
echo "✓ Image pushed to ECR"
echo ""

echo "Step 4: Deployment Options"
echo "------------------------------------------------------------"
echo ""
echo "Your Docker image is now in ECR at:"
echo "  $ECR_URI:latest"
echo ""
echo "Choose a deployment option:"
echo ""
echo "OPTION 1: AWS App Runner (Recommended - Fully Managed)"
echo "------------------------------------------------------------"
echo "Deploy using the AWS Console or CLI:"
echo ""
echo "1. Go to AWS App Runner console:"
echo "   https://console.aws.amazon.com/apprunner/home?region=$AWS_REGION"
echo ""
echo "2. Click 'Create service'"
echo ""
echo "3. Configure:"
echo "   - Source: Container registry → Amazon ECR"
echo "   - Container image URI: $ECR_URI:latest"
echo "   - Deployment: Automatic"
echo "   - ECR access role: Create new service role"
echo ""
echo "4. Set environment variables:"
echo "   OPENAI_API_KEY=$OPENAI_API_KEY"
echo "   OPENAI_BASE_URL=https://learn.modernaipro.com/api/llm/v1"
echo "   CHAT_SECRET=$CHAT_SECRET"
echo "   SCHOOL_USER=student.john"
echo ""
echo "5. Configure service:"
echo "   - Port: 7867"
echo "   - CPU: 1 vCPU"
echo "   - Memory: 2 GB"
echo "   - Auto scaling: 1-3 instances"
echo ""
echo "6. Deploy!"
echo ""
echo "Or use AWS CLI:"
cat << 'EOFCLI'

# First, create IAM role for ECR access (one-time setup)
aws iam create-role \
  --role-name AppRunnerECRAccessRole \
  --assume-role-policy-document '{
    "Version": "2012-10-17",
    "Statement": [{
      "Effect": "Allow",
      "Principal": {"Service": "build.apprunner.amazonaws.com"},
      "Action": "sts:AssumeRole"
    }]
  }'

aws iam attach-role-policy \
  --role-name AppRunnerECRAccessRole \
  --policy-arn arn:aws:iam::aws:policy/service-role/AWSAppRunnerServicePolicyForECRAccess

# Wait a moment for role to be ready
sleep 10

# Get the role ARN
ROLE_ARN=$(aws iam get-role --role-name AppRunnerECRAccessRole --query 'Role.Arn' --output text)

# Create App Runner service
EOFCLI

echo "aws apprunner create-service \\"
echo "  --service-name $APP_NAME \\"
echo "  --region $AWS_REGION \\"
echo "  --source-configuration '{
    \"ImageRepository\": {
      \"ImageIdentifier\": \"$ECR_URI:latest\",
      \"ImageRepositoryType\": \"ECR\",
      \"ImageConfiguration\": {
        \"Port\": \"7867\",
        \"RuntimeEnvironmentVariables\": {
          \"OPENAI_API_KEY\": \"$OPENAI_API_KEY\",
          \"OPENAI_BASE_URL\": \"https://learn.modernaipro.com/api/llm/v1\",
          \"CHAT_SECRET\": \"$CHAT_SECRET\",
          \"SCHOOL_USER\": \"student.john\"
        }
      }
    },
    \"AutoDeploymentsEnabled\": true,
    \"AuthenticationConfiguration\": {
      \"AccessRoleArn\": \"'$ROLE_ARN'\"
    }
  }' \\"
echo "  --instance-configuration '{
    \"Cpu\": \"1024\",
    \"Memory\": \"2048\"
  }'"

echo ""
echo ""
echo "OPTION 2: AWS EC2 (More Control)"
echo "------------------------------------------------------------"
echo "1. Launch an EC2 instance (Amazon Linux 2 or Ubuntu)"
echo "2. Install Docker on the instance"
echo "3. Authenticate Docker to ECR:"
echo "   aws ecr get-login-password --region $AWS_REGION | \\"
echo "     docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com"
echo ""
echo "4. Pull and run the image:"
echo "   docker pull $ECR_URI:latest"
echo "   docker run -d --restart unless-stopped \\"
echo "     -p 7867:7867 \\"
echo "     -e OPENAI_API_KEY='$OPENAI_API_KEY' \\"
echo "     -e OPENAI_BASE_URL='https://learn.modernaipro.com/api/llm/v1' \\"
echo "     -e CHAT_SECRET='$CHAT_SECRET' \\"
echo "     -e SCHOOL_USER='student.john' \\"
echo "     --name eduassist \\"
echo "     $ECR_URI:latest"
echo ""
echo "5. Access at: http://<EC2-PUBLIC-IP>:7867/?k=$CHAT_SECRET"
echo ""
echo ""
echo "=== Deployment Information ==="
echo ""
echo "IMPORTANT - Save these details:"
echo "  ECR Repository: $ECR_URI"
echo "  Region: $AWS_REGION"
echo "  CHAT_SECRET: $CHAT_SECRET"
echo ""
echo "Access URL format: https://<your-service-url>/?k=$CHAT_SECRET"
echo ""
echo "Next steps:"
echo "1. Choose a deployment option above"
echo "2. Complete the deployment"
echo "3. Access your EduAssist instance with the CHAT_SECRET"
echo ""
echo "=== Deployment Complete ==="
