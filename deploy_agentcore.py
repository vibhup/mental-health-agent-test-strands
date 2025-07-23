#!/usr/bin/env python3
"""
Deploy Mental Health Agent to Bedrock AgentCore Runtime
"""

import boto3
import json
import time
import uuid
from datetime import datetime

class MentalHealthAgentDeployer:
    def __init__(self):
        self.bedrock_agentcore = boto3.client('bedrock-agentcore-control', region_name='us-east-1')
        self.iam = boto3.client('iam', region_name='us-east-1')
        self.agent_name = "mental-health-support-agent"
        
    def create_execution_role(self):
        """Create IAM role for AgentCore execution"""
        
        role_name = f"{self.agent_name}-execution-role"
        
        # Trust policy for AgentCore
        trust_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {
                        "Service": [
                            "bedrock-agentcore.amazonaws.com",
                            "bedrock.amazonaws.com"
                        ]
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
    
    def create_agent_runtime(self, role_arn):
        """Create agent runtime in AgentCore"""
        
        # Agent runtime configuration
        runtime_config = {
            "name": self.agent_name,
            "description": "Compassionate AI agent for mental health support with crisis detection",
            "runtimeType": "PYTHON",
            "pythonVersion": "3.11",
            "memorySize": 1024,
            "timeout": 300,
            "environmentVariables": {
                "BEDROCK_MODEL_ID": "anthropic.claude-sonnet-4-20250514-v1:0",
                "AWS_REGION": "us-east-1",
                "ADMIN_EMAIL": "admin.alerts.mh@example.com"
            },
            "executionRoleArn": role_arn
        }
        
        try:
            response = self.bedrock_agentcore.create_agent_runtime(
                name=runtime_config["name"],
                description=runtime_config["description"],
                runtimeType=runtime_config["runtimeType"],
                pythonVersion=runtime_config["pythonVersion"],
                memorySize=runtime_config["memorySize"],
                timeout=runtime_config["timeout"],
                environmentVariables=runtime_config["environmentVariables"],
                executionRoleArn=runtime_config["executionRoleArn"]
            )
            
            print(f"✅ Agent runtime created successfully!")
            print(f"Runtime ID: {response['agentRuntimeId']}")
            print(f"Runtime ARN: {response['agentRuntimeArn']}")
            
            return response
            
        except Exception as e:
            print(f"❌ Error creating agent runtime: {str(e)}")
            return None
    
    def deploy_agent_code(self, runtime_id):
        """Deploy the agent code to the runtime"""
        
        # Read the agent code
        try:
            with open('mental_health_agent.py', 'r') as f:
                agent_code = f.read()
        except FileNotFoundError:
            print("❌ mental_health_agent.py not found. Make sure you're in the correct directory.")
            return False
        
        # Create deployment package
        deployment_package = {
            "main.py": agent_code,
            "requirements.txt": """
strands-agents>=1.0.0
boto3>=1.34.0
python-dotenv>=1.0.0
botocore>=1.34.0
"""
        }
        
        try:
            response = self.bedrock_agentcore.update_agent_runtime_code(
                agentRuntimeId=runtime_id,
                codeSource={
                    "type": "INLINE",
                    "code": json.dumps(deployment_package)
                }
            )
            
            print(f"✅ Agent code deployed successfully!")
            return True
            
        except Exception as e:
            print(f"❌ Error deploying agent code: {str(e)}")
            return False
    
    def create_runtime_endpoint(self, runtime_id):
        """Create an endpoint for the agent runtime"""
        
        endpoint_name = f"{self.agent_name}-endpoint"
        
        try:
            response = self.bedrock_agentcore.create_agent_runtime_endpoint(
                agentRuntimeId=runtime_id,
                endpointName=endpoint_name,
                description="Production endpoint for mental health support agent"
            )
            
            print(f"✅ Runtime endpoint created successfully!")
            print(f"Endpoint Name: {response['endpointName']}")
            print(f"Endpoint ARN: {response['endpointArn']}")
            
            return response
            
        except Exception as e:
            print(f"❌ Error creating runtime endpoint: {str(e)}")
            return None
    
    def test_deployment(self, runtime_arn):
        """Test the deployed agent"""
        
        print("🧪 Testing deployed agent...")
        
        bedrock_agentcore_runtime = boto3.client('bedrock-agentcore', region_name='us-east-1')
        
        test_messages = [
            "Hi, I've been feeling really anxious lately",
            "I can't seem to cope with daily tasks anymore"
        ]
        
        for i, message in enumerate(test_messages, 1):
            try:
                response = bedrock_agentcore_runtime.invoke_agent_runtime(
                    agentRuntimeArn=runtime_arn,
                    runtimeSessionId=str(uuid.uuid4()),
                    payload=json.dumps({
                        "input": message,
                        "sessionId": f"test-session-{i}"
                    }),
                    contentType="application/json",
                    accept="application/json"
                )
                
                print(f"\n--- Test {i} ---")
                print(f"Input: {message}")
                print(f"Response: {response.get('payload', 'No response')}")
                
            except Exception as e:
                print(f"❌ Test {i} failed: {str(e)}")
    
    def deploy(self):
        """Main deployment function"""
        
        print("🏥 Mental Health Agent - Bedrock AgentCore Deployment")
        print("=" * 60)
        
        try:
            # Step 1: Create execution role
            print("\n📋 Step 1: Creating execution role...")
            role_arn = self.create_execution_role()
            
            # Step 2: Create agent runtime
            print("\n🚀 Step 2: Creating agent runtime...")
            runtime_response = self.create_agent_runtime(role_arn)
            
            if not runtime_response:
                print("❌ Deployment failed at runtime creation")
                return None
            
            runtime_id = runtime_response['agentRuntimeId']
            runtime_arn = runtime_response['agentRuntimeArn']
            
            # Step 3: Deploy agent code
            print("\n📦 Step 3: Deploying agent code...")
            if not self.deploy_agent_code(runtime_id):
                print("❌ Deployment failed at code deployment")
                return None
            
            # Step 4: Create runtime endpoint
            print("\n🌐 Step 4: Creating runtime endpoint...")
            endpoint_response = self.create_runtime_endpoint(runtime_id)
            
            # Step 5: Test deployment
            print("\n🧪 Step 5: Testing deployment...")
            self.test_deployment(runtime_arn)
            
            print("\n🎉 Deployment completed successfully!")
            print(f"Runtime ID: {runtime_id}")
            print(f"Runtime ARN: {runtime_arn}")
            
            if endpoint_response:
                print(f"Endpoint: {endpoint_response['endpointArn']}")
            
            print("\n📋 Next Steps:")
            print("1. Configure SES for email notifications")
            print("2. Set up monitoring and alerts")
            print("3. Test with real conversations")
            print("4. Integrate with your application")
            
            return {
                'runtime_id': runtime_id,
                'runtime_arn': runtime_arn,
                'endpoint': endpoint_response
            }
            
        except Exception as e:
            print(f"❌ Deployment failed: {str(e)}")
            return None


def main():
    """Main function"""
    deployer = MentalHealthAgentDeployer()
    result = deployer.deploy()
    
    if result:
        print(f"\n✅ Deployment successful! Runtime ID: {result['runtime_id']}")
    else:
        print("\n❌ Deployment failed. Check the logs above.")


if __name__ == "__main__":
    main()
