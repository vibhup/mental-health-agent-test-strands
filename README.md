# Mental Health Support Agent

A compassionate AI agent built with AWS Strands Agents SDK that provides mental health support and automatically alerts administrators when users show signs of distress.

## 🌟 Features

- **Empathetic Conversations**: Uses Claude Sonnet 4 on Amazon Bedrock for natural, supportive interactions
- **Crisis Detection**: Automatically identifies mental health risk indicators in conversations
- **Admin Alerts**: Sends email notifications to administrators when users need immediate attention
- **Privacy-Focused**: Secure handling of sensitive mental health conversations
- **AWS Integration**: Built on enterprise-grade AWS infrastructure

## 🏗️ Architecture

```
User Input → Strands Agent (Claude Sonnet 4) → Risk Analysis → Admin Alert (SES)
                    ↓
            Supportive Response
```

## 🚀 Quick Start

### Prerequisites

- AWS Account with appropriate permissions
- Python 3.8+
- AWS CLI configured
- Amazon SES verified email address

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/mental-health-agent.git
   cd mental-health-agent
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your AWS configuration
   ```

4. **Set up AWS permissions**
   
   Ensure your AWS credentials have permissions for:
   - Amazon Bedrock (Claude Sonnet 4 access)
   - Amazon SES (send email)

## 🚀 Deployment Options

### Local Development
```bash
python mental_health_agent.py
```

### Production Deployment with Bedrock AgentCore Runtime

For production-ready deployment with enterprise-grade security and scalability:

```bash
# Deploy to AgentCore Runtime
python agentcore_deployment.py

# Test the deployed agent
python agentcore_client.py <AGENT_ID>
```

**AgentCore Benefits:**
- **Serverless Runtime**: No infrastructure management
- **Auto-scaling**: Handles traffic spikes automatically  
- **Session Isolation**: Each conversation runs in isolated microVM
- **Built-in Memory**: Conversational memory across sessions
- **Observability**: Full tracing and monitoring
- **Security**: Enterprise-grade identity and access management

See [AGENTCORE_DEPLOYMENT.md](AGENTCORE_DEPLOYMENT.md) for detailed deployment guide.

## 🔧 Configuration

### Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `AWS_REGION` | AWS region for services | `us-east-1` |
| `ADMIN_EMAIL` | Email for crisis alerts | `admin@company.com` |
| `BEDROCK_MODEL_ID` | Claude model identifier | `anthropic.claude-sonnet-4-20250514-v1:0` |
| `SES_FROM_EMAIL` | Verified SES sender email | `noreply@yourdomain.com` |

### Risk Indicators

The agent monitors for various mental health risk indicators:

**High Risk:**
- Suicide ideation
- Self-harm mentions
- Expressions of wanting to die

**Medium Risk:**
- Severe depression
- Overwhelming anxiety
- Inability to cope

## 🛡️ Security & Privacy

- **Data Protection**: Conversations are processed securely through AWS
- **Access Control**: Admin alerts only sent to authorized personnel
- **Compliance**: Built with healthcare privacy considerations
- **Encryption**: All data encrypted in transit and at rest

## 📊 Monitoring

The agent provides:
- Real-time risk assessment
- Conversation logging
- Alert tracking
- Usage analytics

## 🚨 Crisis Response

When the agent detects high-risk indicators:

1. **Immediate Alert**: Email sent to admin with risk level
2. **Context Provided**: Recent conversation history included
3. **Recommended Actions**: Guidance for follow-up
4. **Documentation**: Incident logged for review

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## ⚠️ Important Disclaimers

- **Not a Replacement**: This agent is NOT a replacement for professional mental health care
- **Emergency Situations**: In crisis situations, users should contact emergency services immediately
- **Professional Help**: Always encourage users to seek professional mental health support
- **Limitations**: AI agents have limitations and should be used as a supportive tool only

## 🆘 Crisis Resources

If you or someone you know is in crisis:

- **National Suicide Prevention Lifeline**: 988 (US)
- **Crisis Text Line**: Text HOME to 741741
- **International**: Visit [findahelpline.com](https://findahelpline.com)

## 📞 Support

For technical support or questions:
- Create an issue in this repository
- Contact: admin.alerts.mh@example.com

## 🙏 Acknowledgments

- AWS Strands Agents SDK team
- Anthropic for Claude models
- Mental health professionals who provided guidance
- Open source community

---

**Remember: Seeking help is a sign of strength, not weakness. You are not alone.** 💙
