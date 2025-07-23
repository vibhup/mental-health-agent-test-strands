#!/usr/bin/env python3
"""
Bedrock AgentCore Runtime deployment configuration for Mental Health Agent
"""

import json
import boto3
from typing import Dict, Any
import os
from mental_health_agent import MentalHealthAgent

class AgentCoreDeployment:
    def __init__(self):
        self.bedrock_agent_core = boto3.client('bedrock-agentcore', region_name='us-east-1')
        self.agent_name = "mental-health-support-agent"
        self.agent_description = "Compassionate AI agent for mental health support with crisis detection"
        
    def create_agent_runtime(self) -> Dict[str, Any]:
        """Create and configure the agent in Bedrock AgentCore Runtime"""
        
        # Agent configuration for AgentCore Runtime
        agent_config = {
            "agentName": self.agent_name,
            "description": self.agent_description,
            "runtimeConfig": {
                "framework": "strands-agents",
                "pythonVersion": "3.11",
                "memorySize": 1024,  # MB
                "timeout": 300,      # 5 minutes
                "environmentVariables": {
                    "BEDROCK_MODEL_ID": "anthropic.claude-sonnet-4-20250514-v1:0",
                    "AWS_REGION": "us-east-1",
                    "ADMIN_EMAIL": "admin.alerts.mh@example.com"
                }
            },
            "codeSource": {
                "type": "INLINE",
                "code": self._get_agent_code()
            },
            "identity": {
                "type": "SERVICE_ROLE",
                "roleArn": self._get_or_create_execution_role()
            },
            "memory": {
                "enabled": True,
                "memoryType": "CONVERSATIONAL",
                "retentionDays": 30
            },
            "observability": {
                "enabled": True,
                "tracing": True,
                "metrics": True
            },
            "tools": [
                {
                    "name": "email_alert_tool",
                    "type": "BUILT_IN",
                    "toolSpec": {
                        "name": "ses_email",
                        "description": "Send email alerts for mental health crises"
                    }
                }
            ]
        }
        
        try:
            response = self.bedrock_agent_core.create_agent(
                agentName=agent_config["agentName"],
                description=agent_config["description"],
                runtimeConfig=agent_config["runtimeConfig"],
                codeSource=agent_config["codeSource"],
                identity=agent_config["identity"],
                memory=agent_config["memory"],
                observability=agent_config["observability"],
                tools=agent_config["tools"]
            )
            
            print(f"✅ Agent created successfully!")
            print(f"Agent ARN: {response['agentArn']}")
            print(f"Agent ID: {response['agentId']}")
            
            return response
            
        except Exception as e:
            print(f"❌ Error creating agent: {str(e)}")
            return None
    
    def _get_agent_code(self) -> str:
        """Get the agent code for deployment"""
        
        # Read the main agent file
        with open('mental_health_agent.py', 'r') as f:
            agent_code = f.read()
        
        # Add AgentCore Runtime wrapper
        wrapper_code = '''
import json
from mental_health_agent import MentalHealthAgent

# Global agent instance
agent = MentalHealthAgent()
conversation_histories = {}

def lambda_handler(event, context):
    """
    AgentCore Runtime handler function
    """
    try:
        # Extract session information
        session_id = event.get('sessionId', 'default')
        user_input = event.get('input', '')
        
        # Get or create conversation history for this session
        if session_id not in conversation_histories:
            conversation_histories[session_id] = []
        
        # Process the user input
        response = agent.chat(user_input, conversation_histories[session_id])
        
        # Return response in AgentCore format
        return {
            'statusCode': 200,
            'body': {
                'response': response,
                'sessionId': session_id,
                'metadata': {
                    'model': 'claude-sonnet-4',
                    'framework': 'strands-agents'
                }
            }
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'body': {
                'error': str(e),
                'message': 'Internal server error'
            }
        }
'''
        
        return agent_code + wrapper_code
    
    def _get_or_create_execution_role(self) -> str:
        """Create or get IAM role for AgentCore execution"""
        
        iam = boto3.client('iam')
        role_name = f"{self.agent_name}-execution-role"
        
        # Trust policy for AgentCore
        trust_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {
                        "Service": "bedrock-agentcore.amazonaws.com"
                    },
                    "Action": "sts:AssumeRole"
                }
            ]
        }
        
        # Permissions policy
        permissions_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": [
                        "bedrock:InvokeModel",
                        "bedrock:InvokeModelWithResponseStream"
                    ],
                    "Resource": "arn:aws:bedrock:us-east-1::foundation-model/anthropic.claude-sonnet-4-20250514-v1:0"
                },
                {
                    "Effect": "Allow",
                    "Action": [
                        "ses:SendEmail",
                        "ses:SendRawEmail"
                    ],
                    "Resource": "*"
                },
                {
                    "Effect": "Allow",
                    "Action": [
                        "logs:CreateLogGroup",
                        "logs:CreateLogStream",
                        "logs:PutLogEvents"
                    ],
                    "Resource": "arn:aws:logs:*:*:*"
                }
            ]
        }
        
        try:
            # Try to get existing role
            response = iam.get_role(RoleName=role_name)
            role_arn = response['Role']['Arn']
            print(f"✅ Using existing role: {role_arn}")
            
        except iam.exceptions.NoSuchEntityException:
            # Create new role
            try:
                response = iam.create_role(
                    RoleName=role_name,
                    AssumeRolePolicyDocument=json.dumps(trust_policy),
                    Description=f"Execution role for {self.agent_name}"
                )
                role_arn = response['Role']['Arn']
                
                # Attach permissions policy
                iam.put_role_policy(
                    RoleName=role_name,
                    PolicyName=f"{role_name}-permissions",
                    PolicyDocument=json.dumps(permissions_policy)
                )
                
                print(f"✅ Created new role: {role_arn}")
                
            except Exception as e:
                print(f"❌ Error creating role: {str(e)}")
                raise
        
        return role_arn
    
    def deploy_agent(self) -> Dict[str, Any]:
        """Deploy the agent to AgentCore Runtime"""
        
        print("🚀 Starting deployment to Bedrock AgentCore Runtime...")
        
        # Create the agent
        agent_response = self.create_agent_runtime()
        
        if not agent_response:
            return None
        
        # Create an alias for production
        try:
            alias_response = self.bedrock_agent_core.create_agent_alias(
                agentId=agent_response['agentId'],
                aliasName='production',
                description='Production deployment of mental health agent'
            )
            
            print(f"✅ Production alias created: {alias_response['aliasArn']}")
            
            return {
                'agent': agent_response,
                'alias': alias_response,
                'endpoint': f"https://bedrock-agentcore.us-east-1.amazonaws.com/agents/{agent_response['agentId']}/aliases/production"
            }
            
        except Exception as e:
            print(f"❌ Error creating alias: {str(e)}")
            return agent_response
    
    def test_deployment(self, agent_id: str, alias_name: str = 'production'):
        """Test the deployed agent"""
        
        print("🧪 Testing deployed agent...")
        
        test_messages = [
            "Hi, I've been feeling really anxious lately",
            "I can't seem to cope with daily tasks anymore",
            "Sometimes I think about hurting myself"  # Should trigger alert
        ]
        
        for i, message in enumerate(test_messages, 1):
            try:
                response = self.bedrock_agent_core.invoke_agent(
                    agentId=agent_id,
                    aliasId=alias_name,
                    sessionId=f"test-session-{i}",
                    inputText=message
                )
                
                print(f"\n--- Test {i} ---")
                print(f"Input: {message}")
                print(f"Response: {response['completion']}")
                
            except Exception as e:
                print(f"❌ Test {i} failed: {str(e)}")


def main():
    """Main deployment function"""
    
    print("🏥 Mental Health Agent - Bedrock AgentCore Deployment")
    print("=" * 60)
    
    deployment = AgentCoreDeployment()
    
    # Deploy the agent
    result = deployment.deploy_agent()
    
    if result:
        print("\n🎉 Deployment successful!")
        print(f"Agent ID: {result['agent']['agentId']}")
        print(f"Endpoint: {result.get('endpoint', 'N/A')}")
        
        # Test the deployment
        deployment.test_deployment(result['agent']['agentId'])
        
        print("\n📋 Next Steps:")
        print("1. Configure SES for email notifications")
        print("2. Set up monitoring and alerts")
        print("3. Integrate with your application")
        print("4. Configure custom domain (optional)")
        
    else:
        print("❌ Deployment failed. Check the logs above.")


if __name__ == "__main__":
    main()
