#!/bin/bash
# EC2 Deployment Script for EduAssist
# Launches EC2 instance and deploys EduAssist container

set -e

echo "=== EduAssist EC2 Deployment ==="
echo ""

AWS_REGION="${AWS_REGION:-us-east-2}"
INSTANCE_TYPE="t3.small"
AMI_ID="ami-0c55b159cbfafe1f0"  # Amazon Linux 2 in us-east-2
KEY_NAME="eduassist-key"
SECURITY_GROUP_NAME="eduassist-sg"

ECR_URI="315768059047.dkr.ecr.us-east-2.amazonaws.com/eduassist"
CHAT_SECRET="d2a2258b669a448dad94ffd9c5603274adbc73d3812ae25d"

# Load API key from .env
if [ -f ../.env ]; then
    export $(cat ../.env | grep OPENAI_API_KEY | xargs)
fi

echo "Step 1: Creating Security Group..."
echo "------------------------------------------------------------"

# Create security group
SG_ID=$(aws ec2 create-security-group \
    --group-name "$SECURITY_GROUP_NAME" \
    --description "Security group for EduAssist" \
    --region "$AWS_REGION" \
    --query 'GroupId' \
    --output text 2>/dev/null || \
    aws ec2 describe-security-groups \
        --group-names "$SECURITY_GROUP_NAME" \
        --region "$AWS_REGION" \
        --query 'SecurityGroups[0].GroupId' \
        --output text)

echo "✓ Security Group: $SG_ID"

# Add inbound rules
aws ec2 authorize-security-group-ingress \
    --group-id "$SG_ID" \
    --protocol tcp \
    --port 7867 \
    --cidr 0.0.0.0/0 \
    --region "$AWS_REGION" 2>/dev/null || echo "  Port 7867 rule already exists"

aws ec2 authorize-security-group-ingress \
    --group-id "$SG_ID" \
    --protocol tcp \
    --port 22 \
    --cidr 0.0.0.0/0 \
    --region "$AWS_REGION" 2>/dev/null || echo "  SSH rule already exists"

echo "✓ Security rules configured (ports 22, 7867)"
echo ""

echo "Step 2: Creating EC2 Key Pair..."
echo "------------------------------------------------------------"

if [ ! -f ~/.ssh/eduassist-key.pem ]; then
    aws ec2 create-key-pair \
        --key-name "$KEY_NAME" \
        --region "$AWS_REGION" \
        --query 'KeyMaterial' \
        --output text > ~/.ssh/eduassist-key.pem
    chmod 400 ~/.ssh/eduassist-key.pem
    echo "✓ Key pair created: ~/.ssh/eduassist-key.pem"
else
    echo "✓ Using existing key: ~/.ssh/eduassist-key.pem"
fi
echo ""

echo "Step 3: Launching EC2 Instance..."
echo "------------------------------------------------------------"

# Get latest Amazon Linux 2 AMI
AMI_ID=$(aws ec2 describe-images \
    --owners amazon \
    --filters "Name=name,Values=amzn2-ami-hvm-*-x86_64-gp2" \
    --query 'Images | sort_by(@, &CreationDate) | [-1].ImageId' \
    --region "$AWS_REGION" \
    --output text)

echo "Using AMI: $AMI_ID"

# User data script to install Docker and run EduAssist
USER_DATA=$(cat <<'EOF'
#!/bin/bash
# Install Docker
yum update -y
yum install -y docker
service docker start
usermod -a -G docker ec2-user

# Install AWS CLI
yum install -y aws-cli

# Configure AWS region
mkdir -p /root/.aws
echo "[default]" > /root/.aws/config
echo "region = us-east-2" >> /root/.aws/config

# Authenticate to ECR
aws ecr get-login-password --region us-east-2 | \
    docker login --username AWS --password-stdin 315768059047.dkr.ecr.us-east-2.amazonaws.com

# Pull and run EduAssist
docker pull 315768059047.dkr.ecr.us-east-2.amazonaws.com/eduassist:latest

docker run -d --restart unless-stopped \
    -p 7867:7867 \
    -e OPENAI_API_KEY='OPENAI_API_KEY_PLACEHOLDER' \
    -e OPENAI_BASE_URL='https://learn.modernaipro.com/api/llm/v1' \
    -e CHAT_SECRET='d2a2258b669a448dad94ffd9c5603274adbc73d3812ae25d' \
    -e SCHOOL_USER='student.john' \
    --name eduassist \
    315768059047.dkr.ecr.us-east-2.amazonaws.com/eduassist:latest

echo "EduAssist deployed successfully!" > /home/ec2-user/deployment-status.txt
EOF
)

# Replace placeholder with actual API key
USER_DATA="${USER_DATA//OPENAI_API_KEY_PLACEHOLDER/$OPENAI_API_KEY}"

# Launch instance
INSTANCE_ID=$(aws ec2 run-instances \
    --image-id "$AMI_ID" \
    --instance-type "$INSTANCE_TYPE" \
    --key-name "$KEY_NAME" \
    --security-group-ids "$SG_ID" \
    --user-data "$USER_DATA" \
    --region "$AWS_REGION" \
    --iam-instance-profile Name=ecsInstanceRole \
    --tag-specifications "ResourceType=instance,Tags=[{Key=Name,Value=EduAssist}]" \
    --query 'Instances[0].InstanceId' \
    --output text 2>&1)

if [[ $INSTANCE_ID == i-* ]]; then
    echo "✓ Instance launching: $INSTANCE_ID"
else
    # Try without IAM role if it fails
    INSTANCE_ID=$(aws ec2 run-instances \
        --image-id "$AMI_ID" \
        --instance-type "$INSTANCE_TYPE" \
        --key-name "$KEY_NAME" \
        --security-group-ids "$SG_ID" \
        --user-data "$USER_DATA" \
        --region "$AWS_REGION" \
        --tag-specifications "ResourceType=instance,Tags=[{Key=Name,Value=EduAssist}]" \
        --query 'Instances[0].InstanceId' \
        --output text)
    echo "✓ Instance launching: $INSTANCE_ID"
fi

echo ""
echo "Step 4: Waiting for instance to start..."
echo "------------------------------------------------------------"

aws ec2 wait instance-running \
    --instance-ids "$INSTANCE_ID" \
    --region "$AWS_REGION"

PUBLIC_IP=$(aws ec2 describe-instances \
    --instance-ids "$INSTANCE_ID" \
    --region "$AWS_REGION" \
    --query 'Reservations[0].Instances[0].PublicIpAddress' \
    --output text)

echo "✓ Instance running!"
echo "✓ Public IP: $PUBLIC_IP"
echo ""

echo "Step 5: Waiting for EduAssist to deploy (2-3 minutes)..."
echo "------------------------------------------------------------"
echo "Docker is being installed and EduAssist is being pulled from ECR..."
echo ""

sleep 120  # Wait for user data script to complete

echo ""
echo "=== Deployment Complete! ==="
echo ""
echo "EduAssist is now live at:"
echo "  http://$PUBLIC_IP:7867/?k=$CHAT_SECRET"
echo ""
echo "Save these details:"
echo "  Instance ID: $INSTANCE_ID"
echo "  Public IP: $PUBLIC_IP"
echo "  SSH Key: ~/.ssh/eduassist-key.pem"
echo "  CHAT_SECRET: $CHAT_SECRET"
echo ""
echo "To SSH into the instance:"
echo "  ssh -i ~/.ssh/eduassist-key.pem ec2-user@$PUBLIC_IP"
echo ""
echo "To view logs:"
echo "  ssh -i ~/.ssh/eduassist-key.pem ec2-user@$PUBLIC_IP 'docker logs eduassist'"
echo ""
echo "To stop the instance (saves money when not in use):"
echo "  aws ec2 stop-instances --instance-ids $INSTANCE_ID --region $AWS_REGION"
echo ""
echo "To start it again:"
echo "  aws ec2 start-instances --instance-ids $INSTANCE_ID --region $AWS_REGION"
echo ""
echo "To terminate (delete) the instance:"
echo "  aws ec2 terminate-instances --instance-ids $INSTANCE_ID --region $AWS_REGION"
echo ""
