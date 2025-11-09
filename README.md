# AWS Capacity Checker

Python script to check AWS capacity reservations, service quotas, and limits across all regions for events.

## Prerequisites

### 1. Install Python Dependencies
```bash
pip install boto3
```

### 2. Configure AWS Credentials

#### Option A: AWS CLI (Recommended)
```bash
# Install AWS CLI
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install

# Configure credentials
aws configure
```
Enter your:
- AWS Access Key ID
- AWS Secret Access Key  
- Default region (e.g., us-east-1)
- Default output format (json)

#### Option B: Environment Variables
```bash
export AWS_ACCESS_KEY_ID=your_access_key
export AWS_SECRET_ACCESS_KEY=your_secret_key
export AWS_DEFAULT_REGION=us-east-1
```

#### Option C: Credentials File
Create `~/.aws/credentials`:
```ini
[default]
aws_access_key_id = your_access_key
aws_secret_access_key = your_secret_key
```

Create `~/.aws/config`:
```ini
[default]
region = us-east-1
output = json
```

### 3. Required IAM Permissions

Your AWS user/role needs these permissions:
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "ec2:DescribeCapacityReservations",
                "ec2:DescribeRegions",
                "servicequotas:GetServiceQuota",
                "servicequotas:ListServiceQuotas"
            ],
            "Resource": "*"
        }
    ]
}
```

## Usage

### Check All Regions
```bash
python3 capacity_checker.py
```

### Check Specific Region
```bash
python3 capacity_checker.py --region us-west-2
```

### Check Specific Instance Type
```bash
python3 capacity_checker.py --instance-type p4d.24xlarge
python3 capacity_checker.py --instance-type g5.xlarge --region us-east-1
```

### Help
```bash
python3 capacity_checker.py --help
```

## What It Checks

- **Capacity Reservations**: Status and availability
- **GPU Instance Quotas**: All GPU families (G, P, INF, TRN, DL)
- **Compute Limits**: EC2, Spot, Dedicated Hosts
- **Storage Limits**: EBS volumes, IOPS, snapshots
- **Networking**: VPC, Security Groups, Elastic IPs
- **Load Balancers**: ALB, NLB limits
- **Monitoring**: CloudWatch, logs
- **Database**: RDS, DynamoDB, ElastiCache
- **Containers**: ECS, Fargate
- **Security**: IAM, KMS, Secrets Manager

## Troubleshooting

### Common Issues

**"Unable to locate credentials"**
- Verify AWS credentials are configured
- Check IAM permissions

**"Access Denied"**
- Ensure IAM user has required permissions
- Check if MFA is required

**"Region not found"**
- Use valid AWS region names (us-east-1, eu-west-1, etc.)

### Test Credentials
```bash
aws sts get-caller-identity
```
