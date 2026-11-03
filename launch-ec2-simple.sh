#!/bin/bash
set -e

echo "Launching EC2 instance..."

# Get latest Amazon Linux 2 AMI
AMI_ID=$(aws ec2 describe-images \
    --owners amazon \
    --filters "Name=name,Values=amzn2-ami-hvm-*-x86_64-gp2" \
    --query 'Images | sort_by(@, &CreationDate) | [-1].ImageId' \
    --region us-east-2 \
    --output text)

# Simple user data to install Docker
USER_DATA='#!/bin/bash
yum update -y
yum install -y docker
service docker start
usermod -a -G docker ec2-user
echo "Docker installed" > /home/ec2-user/status.txt'

# Launch instance
INSTANCE_ID=$(aws ec2 run-instances \
    --image-id "$AMI_ID" \
    --instance-type t3.small \
    --key-name eduassist-key \
    --security-group-ids sg-02cb4d25e3984899b \
    --user-data "$USER_DATA" \
    --region us-east-2 \
    --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=EduAssist}]' \
    --query 'Instances[0].InstanceId' \
    --output text)

echo "Instance ID: $INSTANCE_ID"

# Wait for it to start
aws ec2 wait instance-running --instance-ids "$INSTANCE_ID" --region us-east-2

# Get public IP
PUBLIC_IP=$(aws ec2 describe-instances \
    --instance-ids "$INSTANCE_ID" \
    --region us-east-2 \
    --query 'Reservations[0].Instances[0].PublicIpAddress' \
    --output text)

echo ""
echo "=== Instance Launched! ==="
echo "Instance ID: $INSTANCE_ID"
echo "Public IP: $PUBLIC_IP"
echo ""
echo "Next: SSH in and deploy EduAssist manually"
echo "  ssh -i ~/.ssh/eduassist-key.pem ec2-user@$PUBLIC_IP"
