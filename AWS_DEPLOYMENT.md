# EduAssist - AWS Deployment Guide

Complete guide to deploying EduAssist on AWS using ECR and App Runner.

## Quick Start

```bash
cd eduassist
./deploy-aws.sh
```

This script will:
1. ✓ Check prerequisites (AWS CLI, Docker, credentials)
2. ✓ Create ECR repository
3. ✓ Build Docker image
4. ✓ Push to Amazon ECR
5. → Provide deployment instructions for App Runner or EC2

## Prerequisites

### 1. AWS CLI Installed and Configured

```bash
# Check if installed
aws --version

# Configure credentials
aws configure
# Enter: Access Key ID, Secret Access Key, Region (us-east-2), Output format (json)

# Verify
aws sts get-caller-identity
```

### 2. Docker Running

```bash
docker --version
docker ps  # Should not error
```

### 3. Environment Variables

Your `../.env` file must have:
```bash
OPENAI_API_KEY=your-mai-key-here
OPENAI_BASE_URL=https://learn.modernaipro.com/api/llm/v1
CHAT_SECRET=  # Will be auto-generated if empty
```

## Deployment Options

### Option 1: AWS App Runner (Recommended)

**Best for:** Fully managed, auto-scaling, zero server management

**Steps:**

1. **Run the deployment script:**
   ```bash
   cd eduassist
   ./deploy-aws.sh
   ```

2. **Create App Runner service via AWS Console:**

   a. Go to [AWS App Runner Console](https://console.aws.amazon.com/apprunner/)

   b. Click **"Create service"**

   c. **Source configuration:**
      - Repository type: **Container registry**
      - Provider: **Amazon ECR**
      - Container image URI: Copy from script output
      - Deployment trigger: **Automatic**
      - ECR access role: **Create new service role**

   d. **Service settings:**
      - Service name: `eduassist`
      - Port: `7867`
      - CPU: `1 vCPU`
      - Memory: `2 GB`

   e. **Environment variables** (Click "Add environment variable" for each):
      ```
      OPENAI_API_KEY=<from your .env>
      OPENAI_BASE_URL=https://learn.modernaipro.com/api/llm/v1
      CHAT_SECRET=<from script output - SAVE THIS!>
      SCHOOL_USER=student.john
      ```

   f. **Auto scaling:**
      - Min instances: 1
      - Max instances: 3

   g. **Health check:**
      - Protocol: HTTP
      - Path: `/`
      - Interval: 10 seconds

   h. Click **"Create & deploy"**

3. **Wait 5-10 minutes** for deployment

4. **Access your app:**
   ```
   https://<your-service>.awsapprunner.com/?k=<CHAT_SECRET>
   ```

**Costs:** ~$0.007/hour (~$5/month) + $0.025/GB data transfer

### Option 2: AWS App Runner via CLI

```bash
# 1. Create IAM role for ECR access (one-time)
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

# Wait for role propagation
sleep 15

# 2. Get role ARN
ROLE_ARN=$(aws iam get-role --role-name AppRunnerECRAccessRole --query 'Role.Arn' --output text)

# 3. Get values from deploy-aws.sh output
ECR_URI="<from script output>"
CHAT_SECRET="<from script output>"
OPENAI_API_KEY="<from .env>"

# 4. Create App Runner service
aws apprunner create-service \
  --service-name eduassist \
  --region us-east-2 \
  --source-configuration "{
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
      \"AccessRoleArn\": \"$ROLE_ARN\"
    }
  }" \
  --instance-configuration '{
    "Cpu": "1024",
    "Memory": "2048"
  }'

# 5. Get service URL
aws apprunner describe-service \
  --service-arn <service-arn-from-output> \
  --query 'Service.ServiceUrl' \
  --output text
```

### Option 3: AWS EC2

**Best for:** Full control, custom networking, cost optimization

**Steps:**

1. **Launch EC2 instance:**
   ```bash
   # t3.small or larger
   # Amazon Linux 2 or Ubuntu 22.04
   # Open port 7867 in security group
   ```

2. **SSH into instance and install Docker:**
   ```bash
   # Amazon Linux 2
   sudo yum update -y
   sudo yum install -y docker
   sudo service docker start
   sudo usermod -a -G docker ec2-user

   # Ubuntu
   sudo apt update
   sudo apt install -y docker.io
   sudo systemctl start docker
   sudo usermod -a -G docker ubuntu

   # Log out and back in for group changes
   ```

3. **Install AWS CLI (if not present):**
   ```bash
   curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
   unzip awscliv2.zip
   sudo ./aws/install
   ```

4. **Configure AWS credentials:**
   ```bash
   aws configure
   # Or use IAM instance role (recommended)
   ```

5. **Authenticate Docker to ECR:**
   ```bash
   AWS_REGION=us-east-2
   AWS_ACCOUNT_ID=<your-account-id>

   aws ecr get-login-password --region $AWS_REGION | \
     docker login --username AWS --password-stdin \
     $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com
   ```

6. **Pull and run container:**
   ```bash
   ECR_URI="<from deploy script>"
   CHAT_SECRET="<from deploy script>"
   OPENAI_API_KEY="<from .env>"

   docker pull $ECR_URI:latest

   docker run -d --restart unless-stopped \
     -p 7867:7867 \
     -e OPENAI_API_KEY="$OPENAI_API_KEY" \
     -e OPENAI_BASE_URL="https://learn.modernaipro.com/api/llm/v1" \
     -e CHAT_SECRET="$CHAT_SECRET" \
     -e SCHOOL_USER="student.john" \
     --name eduassist \
     $ECR_URI:latest
   ```

7. **Access:**
   ```
   http://<EC2-PUBLIC-IP>:7867/?k=<CHAT_SECRET>
   ```

**Costs:** ~$0.023/hour (~$17/month) for t3.small

## Updating Your Deployment

### Push New Image to ECR

```bash
cd eduassist
./deploy-aws.sh
```

### Update App Runner

App Runner with auto-deployment will automatically pull new images.

Or manually trigger:
```bash
aws apprunner start-deployment \
  --service-arn <your-service-arn> \
  --region us-east-2
```

### Update EC2

```bash
# SSH into EC2
docker pull $ECR_URI:latest
docker stop eduassist
docker rm eduassist
# Run docker run command again (from step 6 above)
```

## Monitoring & Logs

### App Runner Logs

```bash
# Via Console
# Go to App Runner → Your Service → Logs tab

# Via CLI
aws logs tail /aws/apprunner/eduassist/application --follow
```

### EC2 Logs

```bash
# SSH into EC2
docker logs -f eduassist
```

## Cost Estimation

### App Runner (Recommended for POC)
- **Compute:** $0.007/hour per instance
- **Memory:** Included (up to 2GB)
- **Data transfer:** $0.025/GB
- **Monthly:** ~$5-15 depending on usage

### EC2 (t3.small)
- **Instance:** $0.023/hour (~$17/month)
- **Storage:** $0.10/GB-month
- **Data transfer:** $0.09/GB
- **Monthly:** ~$20-30

### ECR Storage
- **First 50GB:** $0.10/GB-month
- **Monthly:** ~$0.10-1.00 (image is ~500MB)

## Security Best Practices

1. **Never commit secrets:**
   - ✓ CHAT_SECRET in environment only
   - ✓ API keys in environment only
   - ✓ .env in .gitignore

2. **Use HTTPS:**
   - ✓ App Runner provides HTTPS automatically
   - ⚠ EC2 requires ALB or reverse proxy

3. **Least privilege IAM:**
   - Use IAM roles instead of access keys when possible
   - Grant minimum permissions needed

4. **Regular updates:**
   - Rebuild images monthly for security patches
   - Monitor AWS security bulletins

## Troubleshooting

### "No basic auth credentials" when pushing to ECR

```bash
aws ecr get-login-password --region us-east-2 | \
  docker login --username AWS --password-stdin \
  <account-id>.dkr.ecr.us-east-2.amazonaws.com
```

### App Runner service failed to start

Check environment variables are set correctly:
- OPENAI_API_KEY (not empty, starts with "sk-" or "mai_")
- CHAT_SECRET (not empty)
- Port is 7867

### Container exits immediately

Check logs for errors:
```bash
aws logs tail /aws/apprunner/eduassist/application --since 10m
```

Common issues:
- Missing environment variables
- Invalid API key
- Port mismatch

### Can't access the web page

1. Check CHAT_SECRET in URL matches environment variable
2. Verify security group allows inbound port 7867 (EC2 only)
3. Try accessing without secret first (should refuse)

## Cleanup

### Delete App Runner Service

```bash
aws apprunner delete-service \
  --service-arn <your-service-arn> \
  --region us-east-2
```

### Delete ECR Repository

```bash
aws ecr delete-repository \
  --repository-name eduassist \
  --region us-east-2 \
  --force
```

### Terminate EC2 Instance

Via AWS Console or:
```bash
aws ec2 terminate-instances --instance-ids <instance-id>
```

## Support

- AWS App Runner Docs: https://docs.aws.amazon.com/apprunner/
- AWS ECR Docs: https://docs.aws.amazon.com/ecr/
- EduAssist Issues: Check eduassist/README.md

---

**Ready to deploy?**

```bash
cd eduassist
./deploy-aws.sh
```

Follow the on-screen instructions for your preferred deployment option!
