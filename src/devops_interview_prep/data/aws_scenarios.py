"""
AWS scenario-based interview questions.
"""
from typing import Dict, List

AWS_SCENARIO_QUESTIONS: List[Dict[str, object]] = [
    {
        "id": "aws-ec2-troubleshooting-001",
        "topic": "troubleshooting",
        "difficulty": "medium",
        "scenario": (
            "An EC2 instance running a production application suddenly becomes unreachable. "
            "Users report the service is down. How would you troubleshoot the issue?"
        ),
        "reference_answer": (
            "First I would check the EC2 instance status checks in the AWS console to confirm whether the issue "
            "is related to the instance itself or the underlying infrastructure. I would then verify the security groups "
            "to ensure the correct inbound and outbound rules are configured. I would also check network ACLs and route tables "
            "to confirm traffic is allowed through the subnet. Next, I would review CloudWatch metrics such as CPU usage and "
            "network traffic, and check CloudWatch logs for any errors. I would then SSH into the instance if possible to check "
            "application logs, disk space usage, and whether the service is running correctly. If the instance is behind a load balancer, "
            "I would check the target group health checks. Finally, I would restart the application or instance if necessary after "
            "identifying the root cause."
        ),
        "rubric": [
            "checks EC2 instance status checks",
            "checks security groups",
            "checks network ACLs or routing",
            "checks CloudWatch metrics or logs",
            "checks application logs on the instance",
            "checks disk space or resource usage",
            "checks load balancer health checks if applicable",
            "restarts service or instance after investigation"
        ],
    },
    {
        "id": "aws-network-002",
        "topic": "networking",
        "difficulty": "medium",
        "scenario": "You need to build a VPC in AWS so that your application services can run in private subnets but still work correctly. What core components would you include and why?",
        "reference_answer": "Create a VPC with public and private subnets across availability zones. Attach an Internet Gateway for the public subnets, and place a NAT Gateway in a public subnet so resources in private subnets can reach the internet outbound for updates or package downloads. Configure route tables correctly so public subnets route to the IGW and private subnets route through the NAT Gateway. Use security groups to allow only the required traffic such as HTTP and HTTPS, and keep application services in the private subnets.",
        "rubric": [
            "Use a VPC",
            "Use public and private subnets",
            "Attach an Internet Gateway",
            "Place NAT Gateway in a public subnet",
            "Configure route tables correctly",
            "Use security groups for required traffic",
        ],
    },
    {
        "id": "aws-architecture-001",
        "topic": "architecture",
        "difficulty": "medium",
        "scenario": "Design a basic three-tier architecture in AWS for a web application. What layers and AWS services would you include?",
        "reference_answer": "Use a presentation layer, application layer, and database layer. Put a load balancer such as an ALB in public subnets for the web tier, run application servers or ECS tasks in private subnets for the app tier, and place the database such as RDS in private subnets for the data tier. Use security groups between tiers, spread resources across multiple availability zones for resilience, and use Auto Scaling where needed.",
        "rubric": [
            "Describe web, app, and database tiers",
            "Use ALB for the front end",
            "Place app tier in private subnets",
            "Place database in private subnets",
            "Use security groups between tiers",
            "Use multi-AZ or scaling for resilience",
        ],
    },
    {
        "id": "aws-iam-002",
        "topic": "iam",
        "difficulty": "easy",
        "scenario": "Your EC2 instance needs to access data in an S3 bucket securely. How would you set this up?",
        "reference_answer": "Attach an IAM role to the EC2 instance with only the required S3 permissions instead of using hard-coded credentials. If the instance is in a private subnet, add a VPC endpoint for S3 so traffic can stay within the AWS network instead of going over the public internet. Restrict the IAM policy and bucket access to least privilege.",
        "rubric": [
            "Use an IAM role for EC2",
            "Do not use hard-coded credentials",
            "Use a VPC endpoint for S3",
            "Apply least privilege permissions",
        ],
    },
    {
        "id": "aws-network-003",
        "topic": "networking",
        "difficulty": "easy",
        "scenario": "Explain how a user accesses your service in AWS, starting from the domain name and ending at the backend application.",
        "reference_answer": "The user requests the domain name, which is resolved in DNS such as Route 53 to the load balancer. The load balancer receives the traffic and distributes it to the backend application, such as ECS tasks or EC2 instances. The backend processes the request and returns the response through the load balancer back to the user. Security groups and routing need to allow the traffic flow correctly.",
        "rubric": [
            "Domain resolves through DNS or Route 53",
            "Traffic goes to the load balancer",
            "Load balancer distributes traffic",
            "Backend runs on ECS or EC2",
            "Response returns back to the user",
        ],
    },
    {
        "id": "aws-iam-001",
        "topic": "iam",
        "difficulty": "medium",
        "scenario": "Your company has one AWS account and developers often use long-lived access keys. Security wants to remove these keys and enforce least privilege quickly. What would you do in the next 2 weeks and then in the next quarter?",
        "reference_answer": "Immediately federate identities via IAM Identity Center, disable creation of new long-lived keys by policy/SCP, rotate and remove existing keys, and enforce MFA. Move teams to role-based access with permission sets and short-lived credentials. Add CloudTrail + Access Analyzer + IAM last accessed data to tighten policies over time.",
        "rubric": [
            "Use IAM Identity Center or federation",
            "Eliminate long-lived access keys",
            "Apply least privilege with roles/permission sets",
            "Require MFA",
            "Use audit/analysis tools like CloudTrail and Access Analyzer",
        ],
    },
    {
        "id": "aws-network-001",
        "topic": "networking",
        "difficulty": "hard",
        "scenario": "A public web app in one region suffers from periodic DDoS-like traffic spikes and latency for global users. Design an AWS approach to improve resilience and performance.",
        "reference_answer": "Use CloudFront in front of ALB, enable AWS WAF rules and Shield protections, implement rate limiting and bot controls, and use Auto Scaling for backend tiers. For multi-region resilience, consider Route 53 latency/health-based routing with active-active or active-passive failover and replicated data strategy.",
        "rubric": [
            "Use CloudFront for edge caching and global performance",
            "Use AWS WAF and Shield for protection",
            "Use autoscaling and resilient load balancing",
            "Use Route 53 routing/failover strategy",
            "Address multi-region data and failover considerations",
        ],
    },
    {
        "id": "aws-cost-001",
        "topic": "cost-optimization",
        "difficulty": "medium",
        "scenario": "A startup's AWS bill doubled in two months. They want a practical cost optimization plan without hurting reliability. What steps do you take?",
        "reference_answer": "Start with Cost Explorer/CUR and tagging hygiene to identify top cost drivers. Right-size compute and storage, schedule non-prod shutdowns, move suitable workloads to Graviton or serverless, and purchase Savings Plans for steady usage. Add budgets/anomaly detection and weekly cost reviews tied to service owners.",
        "rubric": [
            "Use Cost Explorer/CUR and tagging",
            "Right-size resources and remove waste",
            "Use commitment discounts (Savings Plans/RI) where appropriate",
            "Add budget controls and anomaly detection",
            "Maintain reliability while optimizing",
        ],
    },
]