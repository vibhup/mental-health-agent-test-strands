#!/usr/bin/env python3
"""
Deploy Mental Health Agent to Amazon Bedrock Agents (not AgentCore)
"""

import boto3
import json
import time
import uuid
from datetime import datetime

class MentalHealthBedrockAgentDeployer:
    def __init__(self):
        self.bedrock_agent = boto3.client('bedrock-agent', region_name='us-east-1')
        self.iam = boto3.client('iam', region_name='us-east-1')
        self.lambda_client = boto3.client('lambda', region_name='us-east-1')
        self.agent_name = "mental-health-support-agent"
        
    def create_execution_role(self):
        """Create IAM role for Bedrock Agent execution"""
        
        role_name = f"{self.agent_name}-execution-role"
        
        # Trust policy for Bedrock Agent
        trust_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {
                        "Service": "bedrock.amazonaws.com"
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
                    "Resource": [
                        "arn:aws:bedrock:us-east-1::foundation-model/anthropic.claude-sonnet-4-20250514-v1:0",
                        "arn:aws:bedrock:us-east-1::foundation-model/anthropic.claude-3-5-sonnet-20241022-v2:0"
                    ]
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
                        "lambda:InvokeFunction"
                    ],
                    "Resource": "*"
                }
            ]
        }
        
        try:
            # Try to get existing role
            response = self.iam.get_role(RoleName=role_name)
            role_arn = response['Role']['Arn']
            print(f"✅ Using existing role: {role_arn}")
            
        except self.iam.exceptions.NoSuchEntityException:
            # Create new role
            try:
                response = self.iam.create_role(
                    RoleName=role_name,
                    AssumeRolePolicyDocument=json.dumps(trust_policy),
                    Description=f"Execution role for {self.agent_name}"
                )
                role_arn = response['Role']['Arn']
                
                # Attach permissions policy
                self.iam.put_role_policy(
                    RoleName=role_name,
                    PolicyName=f"{role_name}-permissions",
                    PolicyDocument=json.dumps(permissions_policy)
                )
                
                print(f"✅ Created new role: {role_arn}")
                
                # Wait for role to be available
                print("⏳ Waiting for role to be available...")
                time.sleep(10)
                
            except Exception as e:
                print(f"❌ Error creating role: {str(e)}")
                raise
        
        return role_arn
    
    def create_lambda_function(self, role_arn):
        """Create Lambda function for email alerts"""
        
        function_name = f"{self.agent_name}-email-alert"
        
        try:
            # Check if function already exists
            try:
                response = self.lambda_client.get_function(FunctionName=function_name)
                function_arn = response['Configuration']['FunctionArn']
                print(f"✅ Using existing Lambda function: {function_arn}")
                return function_arn
                
            except self.lambda_client.exceptions.ResourceNotFoundException:
                pass
            
            # Read the ZIP file
            with open('lambda_function.zip', 'rb') as zip_file:
                zip_content = zip_file.read()
            
            # Create Lambda function
            response = self.lambda_client.create_function(
                FunctionName=function_name,
                Runtime='python3.11',
                Role=role_arn,
                Handler='lambda_alert_function.lambda_handler',
                Code={'ZipFile': zip_content},
                Description='Email alert function for mental health agent',
                Timeout=30,
                Environment={
                    'Variables': {
                        'ADMIN_EMAIL': 'admin.alerts.mh@example.com'
                    }
                }
            )
            
            function_arn = response['FunctionArn']
            print(f"✅ Created Lambda function: {function_arn}")
            
            # Wait for function to be available
            time.sleep(5)
            
            return function_arn
            
        except Exception as e:
            print(f"❌ Error creating Lambda function: {str(e)}")
            return None
    
    def create_bedrock_agent(self, role_arn, lambda_arn):
        """Create Bedrock Agent"""
        
        # Agent instruction
        instruction = """You are a compassionate mental health support agent. Your role is to:

1. Engage users in supportive conversation about their mental health
2. Listen actively and respond with empathy
3. Ask thoughtful follow-up questions to understand their situation
4. Provide general emotional support and coping strategies
5. Encourage professional help when appropriate

IMPORTANT GUIDELINES:
- You are NOT a replacement for professional mental health care
- Always encourage users to seek professional help for serious concerns
- Be warm, non-judgmental, and supportive
- Ask open-ended questions to encourage sharing
- Validate their feelings and experiences

CRISIS INDICATORS to watch for:
- Mentions of suicide, self-harm, or wanting to die
- Expressions of hopelessness or feeling trapped
- Severe depression or anxiety that's impacting daily function
- Substance abuse as coping mechanism
- Complete social isolation
- Inability to cope with daily activities

If you detect crisis indicators, use the email_alert action to notify the admin immediately.

Remember: Your goal is to provide support while ensuring user safety."""

        try:
            response = self.bedrock_agent.create_agent(
                agentName=self.agent_name,
                description="Compassionate AI agent for mental health support with crisis detection",
                agentResourceRoleArn=role_arn,
                foundationModel="anthropic.claude-sonnet-4-20250514-v1:0",
                instruction=instruction,
                idleSessionTTLInSeconds=1800,  # 30 minutes
                memoryConfiguration={
                    'enabledMemoryTypes': ['SESSION_SUMMARY'],
                    'sessionSummaryConfiguration': {
                        'maxRecentSessions': 5,
                        'storageDays': 30
                    }
                }
            )
            
            agent_id = response['agent']['agentId']
            agent_arn = response['agent']['agentArn']
            
            print(f"✅ Bedrock Agent created successfully!")
            print(f"Agent ID: {agent_id}")
            print(f"Agent ARN: {agent_arn}")
            
            return response['agent']
            
        except Exception as e:
            print(f"❌ Error creating Bedrock Agent: {str(e)}")
            return None
    
    def create_action_group(self, agent_id, lambda_arn):
        """Create action group for email alerts"""
        
        # Action group schema
        action_schema = {
            "openapi": "3.0.0",
            "info": {
                "title": "Mental Health Alert API",
                "version": "1.0.0",
                "description": "API for sending mental health crisis alerts"
            },
            "paths": {
                "/send_alert": {
                    "post": {
                        "summary": "Send crisis alert email",
                        "description": "Send an email alert when mental health crisis indicators are detected",
                        "operationId": "send_crisis_alert",
                        "requestBody": {
                            "required": True,
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "user_message": {
                                                "type": "string",
                                                "description": "The user's message that triggered the alert"
                                            },
                                            "risk_level": {
                                                "type": "string",
                                                "description": "The assessed risk level (HIGH, MEDIUM, LOW)"
                                            },
                                            "risk_indicators": {
                                                "type": "array",
                                                "items": {"type": "string"},
                                                "description": "List of detected risk indicators"
                                            }
                                        },
                                        "required": ["user_message", "risk_level"]
                                    }
                                }
                            }
                        },
                        "responses": {
                            "200": {
                                "description": "Alert sent successfully",
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "type": "object",
                                            "properties": {
                                                "message": {"type": "string"},
                                                "messageId": {"type": "string"}
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
        
        try:
            response = self.bedrock_agent.create_agent_action_group(
                agentId=agent_id,
                agentVersion='DRAFT',
                actionGroupName='email_alert_actions',
                description='Actions for sending mental health crisis alerts',
                actionGroupExecutor={
                    'lambda': lambda_arn
                },
                apiSchema={
                    'payload': json.dumps(action_schema)
                }
            )
            
            print(f"✅ Action group created successfully!")
            print(f"Action Group ID: {response['agentActionGroup']['actionGroupId']}")
            
            return response['agentActionGroup']
            
        except Exception as e:
            print(f"❌ Error creating action group: {str(e)}")
            return None
    
    def prepare_agent(self, agent_id):
        """Prepare the agent for use"""
        
        try:
            response = self.bedrock_agent.prepare_agent(agentId=agent_id)
            
            print(f"✅ Agent prepared successfully!")
            print(f"Preparation ID: {response['agentId']}")
            
            # Wait for preparation to complete
            print("⏳ Waiting for agent preparation to complete...")
            
            max_attempts = 30
            for attempt in range(max_attempts):
                try:
                    status_response = self.bedrock_agent.get_agent(agentId=agent_id)
                    status = status_response['agent']['agentStatus']
                    
                    if status == 'PREPARED':
                        print("✅ Agent preparation completed!")
                        break
                    elif status == 'FAILED':
                        print("❌ Agent preparation failed!")
                        return False
                    else:
                        print(f"⏳ Agent status: {status}, waiting...")
                        time.sleep(10)
                        
                except Exception as e:
                    print(f"⏳ Checking status... (attempt {attempt + 1})")
                    time.sleep(10)
            else:
                print("⚠️ Agent preparation timeout, but continuing...")
            
            return True
            
        except Exception as e:
            print(f"❌ Error preparing agent: {str(e)}")
            return False
    
    def create_agent_alias(self, agent_id):
        """Create an alias for the agent"""
        
        try:
            response = self.bedrock_agent.create_agent_alias(
                agentId=agent_id,
                aliasName='production',
                description='Production alias for mental health support agent'
            )
            
            alias_id = response['agentAlias']['agentAliasId']
            alias_arn = response['agentAlias']['agentAliasArn']
            
            print(f"✅ Agent alias created successfully!")
            print(f"Alias ID: {alias_id}")
            print(f"Alias ARN: {alias_arn}")
            
            return response['agentAlias']
            
        except Exception as e:
            print(f"❌ Error creating agent alias: {str(e)}")
            return None
    
    def test_agent(self, agent_id, alias_id):
        """Test the deployed agent"""
        
        print("🧪 Testing deployed agent...")
        
        bedrock_agent_runtime = boto3.client('bedrock-agent-runtime', region_name='us-east-1')
        
        test_messages = [
            "Hi, I've been feeling really anxious lately",
            "I can't seem to cope with daily tasks anymore"
        ]
        
        for i, message in enumerate(test_messages, 1):
            try:
                response = bedrock_agent_runtime.invoke_agent(
                    agentId=agent_id,
                    agentAliasId=alias_id,
                    sessionId=f"test-session-{i}",
                    inputText=message
                )
                
                # Process streaming response
                completion = ""
                for event in response['completion']:
                    if 'chunk' in event:
                        chunk = event['chunk']
                        if 'bytes' in chunk:
                            completion += chunk['bytes'].decode('utf-8')
                
                print(f"\n--- Test {i} ---")
                print(f"Input: {message}")
                print(f"Response: {completion}")
                
            except Exception as e:
                print(f"❌ Test {i} failed: {str(e)}")
    
    def deploy(self):
        """Main deployment function"""
        
        print("🏥 Mental Health Agent - Bedrock Agents Deployment")
        print("=" * 60)
        
        try:
            # Step 1: Create execution role
            print("\n📋 Step 1: Creating execution role...")
            role_arn = self.create_execution_role()
            
            # Step 2: Create Lambda function for alerts
            print("\n⚡ Step 2: Creating Lambda function for alerts...")
            lambda_arn = self.create_lambda_function(role_arn)
            
            if not lambda_arn:
                print("❌ Deployment failed at Lambda creation")
                return None
            
            # Step 3: Create Bedrock Agent
            print("\n🤖 Step 3: Creating Bedrock Agent...")
            agent = self.create_bedrock_agent(role_arn, lambda_arn)
            
            if not agent:
                print("❌ Deployment failed at agent creation")
                return None
            
            agent_id = agent['agentId']
            
            # Step 4: Create action group
            print("\n🔧 Step 4: Creating action group...")
            action_group = self.create_action_group(agent_id, lambda_arn)
            
            # Step 5: Prepare agent
            print("\n🚀 Step 5: Preparing agent...")
            if not self.prepare_agent(agent_id):
                print("❌ Deployment failed at agent preparation")
                return None
            
            # Step 6: Create alias
            print("\n🏷️ Step 6: Creating agent alias...")
            alias = self.create_agent_alias(agent_id)
            
            if alias:
                alias_id = alias['agentAliasId']
                
                # Step 7: Test deployment
                print("\n🧪 Step 7: Testing deployment...")
                self.test_agent(agent_id, alias_id)
            
            print("\n🎉 Deployment completed successfully!")
            print(f"Agent ID: {agent_id}")
            print(f"Agent ARN: {agent['agentArn']}")
            
            if alias:
                print(f"Alias ID: {alias_id}")
                print(f"Alias ARN: {alias['agentAliasArn']}")
            
            print("\n📋 Next Steps:")
            print("1. Configure SES for email notifications")
            print("2. Test with real conversations")
            print("3. Set up monitoring and alerts")
            print("4. Integrate with your application")
            
            return {
                'agent_id': agent_id,
                'agent_arn': agent['agentArn'],
                'alias': alias,
                'lambda_arn': lambda_arn
            }
            
        except Exception as e:
            print(f"❌ Deployment failed: {str(e)}")
            return None


def main():
    """Main function"""
    deployer = MentalHealthBedrockAgentDeployer()
    result = deployer.deploy()
    
    if result:
        print(f"\n✅ Deployment successful! Agent ID: {result['agent_id']}")
    else:
        print("\n❌ Deployment failed. Check the logs above.")


if __name__ == "__main__":
    main()
