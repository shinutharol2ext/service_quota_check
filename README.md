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
python3 service_quota_check.py
```

### Check Specific Region
```bash
python3 service_quota_check.py --region us-west-2
```

### Check Specific Instance Type
```bash
python3 service_quota_check.py --instance-type p4d.24xlarge
python3 service_quota_check.py --instance-type g5.xlarge --region us-east-1
```

### Help
```bash
python3 service_quota_check.py --help
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

Sample Output
```
command : python service_quota_check.py --region us-east-1
output:

Checking region: us-east-1

=== AWS Service Limits Report for g5.2xlarge ===
Region: us-east-1
Generated: 2025-11-09 10:46:44

1. CAPACITY RESERVATIONS:
  ID: cr-0e264a51e2c21db33 | Type: g5.xlarge | Total: 1 | Available: 1 | State: active

2. COMPUTE & CAPACITY:
  Running On-Demand G and VT instances: 64.0 None
  All Standard (A, C, D, H, I, M, R, T, Z) Spot Inst...: 640.0 None
  Dedicated Hosts: Unable to fetch 

3. GPU INSTANCE QUOTAS:
  Running On-Demand G and VT instances: 64.0 None
  Running On-Demand G and VT instances: 64.0 None
  Running On-Demand G and VT instances: 64.0 None
  Running On-Demand G and VT instances: 64.0 None
  Running On-Demand P instances: 384.0 None
  Running On-Demand P instances: 384.0 None
  Running On-Demand P instances: 384.0 None
  Running On-Demand P instances: 384.0 None
  Running On-Demand P instances: 384.0 None
  Running On-Demand G and VT instances: 64.0 None
  Running On-Demand G and VT instances: 64.0 None
  Running On-Demand Trn instances: 256.0 None
  Running On-Demand Trn instances: 256.0 None
  Running On-Demand DL instances: 96.0 None

4. STORAGE LIMITS:
  Snapshots per Region: 100000.0 None
  IOPS for Provisioned IOPS SSD (io1) volumes: 300000.0 None
  Snapshots per Region: 100000.0 None

5. NETWORKING LIMITS:
  VPCs per Region: 5.0 None
  VPC security groups per Region: 2500.0 None
  EC2-VPC Elastic IPs: 5.0 None
  NAT gateways per Availability Zone: 5.0 None
  Network interfaces per Region: 5000.0 None

6. LOAD BALANCER LIMITS:
  Unknown: Unable to fetch 
  Network Load Balancers per Region: 50.0 None
  Targets per Application Load Balancer: 1000.0 None

7. DNS & TRAFFIC LIMITS:
  Unknown: Unable to fetch 
  Unknown: Unable to fetch 

8. MONITORING LIMITS:
  Rate of GetMetricData requests: 500.0 None
  Unknown: Unable to fetch 
  Unknown: Unable to fetch 

9. DATABASE LIMITS:
  DB instances: 40.0 None
  Read replicas per primary: 15.0 None
  Unknown: Unable to fetch 
  Unknown: Unable to fetch 

10. CONTAINER LIMITS:
  Unknown: Unable to fetch 
  Unknown: Unable to fetch 
  Unknown: Unable to fetch 

11. SECURITY LIMITS:
  Roles per account: 1000.0 None
  Unknown: Unable to fetch 
  Unknown: Unable to fetch 

=== CRITICAL PRE-EVENT ACTIONS ===
1. Request quota increases 2-3 weeks in advance
2. Test scaling scenarios in non-production
3. Set up monitoring dashboards for real-time tracking
4. Configure CloudWatch alarms for quota thresholds
5. Prepare rollback procedures for capacity issues
6. Coordinate with AWS TAM/Support for large events
7. Use AWS Trusted Advisor for limit monitoring
8. Consider multi-region deployment for redundancy

=== EVENT DAY MONITORING ===
- Monitor service health dashboards
- Track quota utilization in real-time
- Have escalation procedures ready
- Monitor application performance metrics

=== IMPORTANT NOTE ===
Review all quotas above and submit quota increase requests if necessary
to address your upcoming event. Allow 24-48 hours for quota increases.
Use AWS Service Quotas console or AWS CLI to request increases.

CSV report saved as: service_quota_check_20251109_104644.csv
```
