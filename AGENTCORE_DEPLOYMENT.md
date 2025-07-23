# Bedrock AgentCore Runtime Deployment Guide

This guide walks you through deploying your Mental Health Support Agent using Amazon Bedrock AgentCore Runtime for production-ready, scalable deployment.

## 🏗️ Architecture Overview

```
User Request → AgentCore Runtime → Strands Agent → Claude Sonnet 4 → Response
                     ↓
            Memory + Observability + Identity + Tools
                     ↓
            Admin Alert (SES) if crisis detected
```

## 📋 Prerequisites

### 1. AWS Permissions
Ensure your AWS credentials have permissions for:
- Amazon Bedrock AgentCore (full access)
- Amazon Bedrock (model access)
- Amazon SES (send email)
- IAM (create/manage roles)
- CloudWatch Logs

### 2. Model Access
Request access to Claude Sonnet 4 in Bedrock:
```bash
aws bedrock put-model-invocation-logging-configuration \
  --region us-east-1 \
  --logging-config '{"textDataDeliveryEnabled":true,"imageDataDeliveryEnabled":true,"embeddingDataDeliveryEnabled":true}'
```

### 3. SES Setup
Configure Amazon SES for email notifications:
```bash
# Verify your domain/email
aws ses verify-email-identity --email-address admin.alerts.mh@example.com --region us-east-1
```

## 🚀 Deployment Steps

### Step 1: Install Dependencies
```bash
pip install boto3 botocore
```

### Step 2: Deploy to AgentCore Runtime
```bash
python agentcore_deployment.py
```

This will:
- Create IAM execution role
- Deploy agent to AgentCore Runtime
- Configure memory, observability, and tools
- Create production alias
- Run basic tests

### Step 3: Get Agent Details
After deployment, note the:
- **Agent ID**: Used for API calls
- **Agent ARN**: Full resource identifier
- **Endpoint**: Runtime endpoint URL

## 🧪 Testing the Deployment

### Interactive Testing
```bash
python agentcore_client.py <AGENT_ID>
```

### Programmatic Testing
```python
from agentcore_client import AgentCoreClient

client = AgentCoreClient(agent_id="YOUR_AGENT_ID")
response = client.chat("I've been feeling really anxious lately")
print(response['response'])
```

## 🔧 Configuration Options

### Runtime Configuration
- **Memory**: 1024 MB (adjustable)
- **Timeout**: 5 minutes (max 8 hours available)
- **Framework**: Strands Agents
- **Python Version**: 3.11

### Memory Settings
- **Type**: Conversational memory
- **Retention**: 30 days
- **Shared**: Across sessions

### Observability
- **Tracing**: Enabled (OpenTelemetry compatible)
- **Metrics**: Enabled
- **Logs**: CloudWatch integration

## 📊 Monitoring & Observability

### CloudWatch Metrics
Monitor these key metrics:
- Invocation count
- Duration
- Error rate
- Memory usage
- Token consumption

### Tracing
View detailed traces in:
- AWS X-Ray
- AgentCore Observability dashboard
- Custom OpenTelemetry collectors

### Alerts
Set up CloudWatch alarms for:
- High error rates
- Long response times
- Memory issues
- Crisis detection frequency

## 🔐 Security Features

### Identity & Access
- **Service Role**: Dedicated IAM role
- **Least Privilege**: Minimal required permissions
- **Session Isolation**: Each conversation isolated
- **Encryption**: Data encrypted in transit and at rest

### Privacy Protection
- **Memory Isolation**: User sessions completely separated
- **Data Retention**: Configurable retention periods
- **Audit Logs**: Full audit trail available

## 🛠️ Advanced Configuration

### Custom Tools Integration
```python
# Add custom tools to the agent
tools = [
    {
        "name": "crisis_hotline_lookup",
        "type": "LAMBDA",
        "lambdaArn": "arn:aws:lambda:us-east-1:123456789012:function:crisis-hotline"
    }
]
```

### Multi-Region Deployment
```python
# Deploy to multiple regions for high availability
regions = ['us-east-1', 'us-west-2', 'eu-west-1']
for region in regions:
    deployment = AgentCoreDeployment(region=region)
    deployment.deploy_agent()
```

### Custom Memory Configuration
```python
memory_config = {
    "enabled": True,
    "memoryType": "EPISODIC",  # or CONVERSATIONAL
    "retentionDays": 90,
    "maxMemorySize": "10MB"
}
```

## 🔄 CI/CD Integration

### GitHub Actions Example
```yaml
name: Deploy Mental Health Agent

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v1
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: us-east-1
      - name: Deploy to AgentCore
        run: python agentcore_deployment.py
```

## 💰 Cost Optimization

### Pricing Factors
- **Runtime Usage**: Pay per invocation and duration
- **Memory**: Charged for allocated memory
- **Model Usage**: Claude Sonnet 4 token costs
- **Storage**: Memory and logs storage

### Optimization Tips
- Use appropriate memory allocation
- Implement efficient conversation handling
- Monitor and optimize token usage
- Set up cost alerts

## 🚨 Crisis Response Integration

### Automatic Escalation
```python
# Configure crisis response
crisis_config = {
    "high_risk_threshold": 0.8,
    "escalation_channels": [
        "email:admin.alerts.mh@example.com",
        "sns:arn:aws:sns:us-east-1:123456789012:crisis-alerts",
        "lambda:arn:aws:lambda:us-east-1:123456789012:function:crisis-response"
    ]
}
```

## 📞 Support & Troubleshooting

### Common Issues
1. **Permission Errors**: Check IAM roles and policies
2. **Model Access**: Ensure Bedrock model access is granted
3. **Memory Issues**: Adjust memory allocation
4. **Timeout Errors**: Increase timeout settings

### Debug Commands
```bash
# Check agent status
aws bedrock-agentcore describe-agent --agent-id <AGENT_ID>

# View logs
aws logs describe-log-groups --log-group-name-prefix "/aws/bedrock-agentcore"

# Test connectivity
python -c "import boto3; print(boto3.client('bedrock-agentcore').list_agents())"
```

## 🔄 Updates & Maintenance

### Updating the Agent
```bash
# Update agent code
python agentcore_deployment.py --update --agent-id <AGENT_ID>

# Create new version
python agentcore_deployment.py --create-version --agent-id <AGENT_ID>
```

### Rollback Strategy
```bash
# Rollback to previous version
aws bedrock-agentcore update-agent-alias \
  --agent-id <AGENT_ID> \
  --alias-id production \
  --agent-version <PREVIOUS_VERSION>
```

---

## 🎯 Production Checklist

- [ ] AWS permissions configured
- [ ] SES email verified
- [ ] Agent deployed successfully
- [ ] Production alias created
- [ ] Monitoring set up
- [ ] Crisis response tested
- [ ] Security review completed
- [ ] Documentation updated
- [ ] Team training completed

Your Mental Health Support Agent is now ready for production use with enterprise-grade security, scalability, and observability! 🚀
