#!/usr/bin/env python3
"""
Deploy Mental Health Agent to Amazon Bedrock AgentCore Runtime
Proper implementation with container configuration
"""

import boto3
import json
import time
import uuid
from datetime import datetime

class AgentCoreDeployer:
    def __init__(self):
        self.agentcore_control = boto3.client('bedrock-agentcore-control', region_name='us-east-1')
        self.agentcore_runtime = boto3.client('bedrock-agentcore', region_name='us-east-1')
        self.iam = boto3.client('iam', region_name='us-east-1')
        self.ecr = boto3.client('ecr', region_name='us-east-1')
        self.agent_name = "mental_health_support_agent"  # No hyphens allowed
        
    def create_execution_role(self):
        """Create IAM role for AgentCore execution"""
        
        role_name = f"{self.agent_name}-agentcore-role"
        
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
                    "Resource": [
                        "arn:aws:bedrock:us-east-1::foundation-model/anthropic.claude-sonnet-4-20250514-v1:0"
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
                },
                {
                    "Effect": "Allow",
                    "Action": [
                        "ecr:GetAuthorizationToken",
                        "ecr:BatchCheckLayerAvailability",
                        "ecr:GetDownloadUrlForLayer",
                        "ecr:BatchGetImage"
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
                    Description=f"AgentCore execution role for {self.agent_name}"
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
    
    def create_ecr_repository(self):
        """Create ECR repository for the agent container"""
        
        repo_name = f"{self.agent_name}-repo"
        
        try:
            # Check if repository exists
            try:
                response = self.ecr.describe_repositories(repositoryNames=[repo_name])
                repo_uri = response['repositories'][0]['repositoryUri']
                print(f"✅ Using existing ECR repository: {repo_uri}")
                return repo_uri
                
            except self.ecr.exceptions.RepositoryNotFoundException:
                pass
            
            # Create repository
            response = self.ecr.create_repository(
                repositoryName=repo_name,
                imageTagMutability='MUTABLE',
                imageScanningConfiguration={
                    'scanOnPush': True
                }
            )
            
            repo_uri = response['repository']['repositoryUri']
            print(f"✅ Created ECR repository: {repo_uri}")
            
            # Set repository policy separately
            try:
                self.ecr.set_repository_policy(
                    repositoryName=repo_name,
                    policyText=json.dumps({
                        "Version": "2012-10-17",
                        "Statement": [
                            {
                                "Sid": "AllowAgentCorePull",
                                "Effect": "Allow",
                                "Principal": {
                                    "Service": "bedrock-agentcore.amazonaws.com"
                                },
                                "Action": [
                                    "ecr:GetDownloadUrlForLayer",
                                    "ecr:BatchGetImage",
                                    "ecr:BatchCheckLayerAvailability"
                                ]
                            }
                        ]
                    })
                )
                print("✅ Set ECR repository policy")
            except Exception as e:
                print(f"⚠️  Warning: Could not set repository policy: {str(e)}")
            
            return repo_uri
            
        except Exception as e:
            print(f"❌ Error creating ECR repository: {str(e)}")
            return None
    
    def create_dockerfile(self):
        """Create Dockerfile for the mental health agent"""
        
        dockerfile_content = '''FROM public.ecr.aws/lambda/python:3.11

# Install system dependencies
RUN yum update -y && yum install -y gcc

# Copy requirements and install Python dependencies
COPY requirements.txt ${LAMBDA_TASK_ROOT}
RUN pip install -r requirements.txt

# Copy application code
COPY mental_health_agent.py ${LAMBDA_TASK_ROOT}
COPY agentcore_handler.py ${LAMBDA_TASK_ROOT}

# Set the CMD to your handler
CMD ["agentcore_handler.handler"]
'''
        
        with open('Dockerfile', 'w') as f:
            f.write(dockerfile_content)
        
        print("✅ Created Dockerfile")
    
    def create_agentcore_handler(self):
        """Create AgentCore handler wrapper"""
        
        handler_content = '''
import json
import os
from mental_health_agent import MentalHealthAgent

# Initialize the agent
agent = MentalHealthAgent()
conversation_histories = {}

def handler(event, context):
    """
    AgentCore Runtime handler for mental health agent
    """
    try:
        # Extract session information
        session_id = event.get('sessionId', 'default')
        user_input = event.get('input', '')
        
        print(f"Processing request for session: {session_id}")
        print(f"User input: {user_input}")
        
        # Get or create conversation history for this session
        if session_id not in conversation_histories:
            conversation_histories[session_id] = []
        
        # Process the user input through the mental health agent
        response = agent.chat(user_input, conversation_histories[session_id])
        
        # Return response in AgentCore format
        return {
            'statusCode': 200,
            'body': {
                'response': response,
                'sessionId': session_id,
                'timestamp': context.aws_request_id if context else None,
                'metadata': {
                    'model': 'claude-sonnet-4',
                    'framework': 'strands-agents',
                    'agent': 'mental-health-support'
                }
            }
        }
        
    except Exception as e:
        print(f"Error processing request: {str(e)}")
        return {
            'statusCode': 500,
            'body': {
                'error': str(e),
                'message': 'Internal server error in mental health agent'
            }
        }
'''
        
        with open('agentcore_handler.py', 'w') as f:
            f.write(handler_content)
        
        print("✅ Created AgentCore handler")
    
    def build_and_push_container(self, repo_uri):
        """Build and push container to ECR"""
        
        print("🐳 Building and pushing container...")
        
        # Create necessary files
        self.create_dockerfile()
        self.create_agentcore_handler()
        
        # Note: In a real deployment, you would run Docker commands here
        # For this demo, we'll simulate the container URI
        container_uri = f"{repo_uri}:latest"
        
        print("📝 To complete the container deployment, run these commands:")
        print(f"1. aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin {repo_uri.split('/')[0]}")
        print(f"2. docker build -t {self.agent_name} .")
        print(f"3. docker tag {self.agent_name}:latest {container_uri}")
        print(f"4. docker push {container_uri}")
        print()
        print("⚠️  For now, we'll proceed with the deployment configuration...")
        
        return container_uri
    
    def create_agent_runtime(self, role_arn, container_uri):
        """Create AgentCore Runtime"""
        
        try:
            response = self.agentcore_control.create_agent_runtime(
                agentRuntimeName=self.agent_name,
                description="Mental Health Support Agent with Claude Sonnet 4 and crisis detection",
                agentRuntimeArtifact={
                    'containerConfiguration': {
                        'containerUri': container_uri
                    }
                },
                roleArn=role_arn,
                networkConfiguration={
                    'networkMode': 'PUBLIC'  # Must be PUBLIC
                },
                protocolConfiguration={
                    'serverProtocol': 'HTTP'
                },
                environmentVariables={
                    'BEDROCK_MODEL_ID': 'anthropic.claude-sonnet-4-20250514-v1:0',
                    'AWS_REGION': 'us-east-1',
                    'ADMIN_EMAIL': 'admin.alerts.mh@example.com'
                }
            )
            
            runtime_id = response['agentRuntimeId']
            runtime_arn = response['agentRuntimeArn']
            
            print(f"✅ AgentCore Runtime created successfully!")
            print(f"Runtime ID: {runtime_id}")
            print(f"Runtime ARN: {runtime_arn}")
            
            return response
            
        except Exception as e:
            print(f"❌ Error creating AgentCore Runtime: {str(e)}")
            return None
    
    def create_runtime_endpoint(self, runtime_id):
        """Create endpoint for the AgentCore Runtime"""
        
        endpoint_name = "production"
        
        try:
            response = self.agentcore_control.create_agent_runtime_endpoint(
                agentRuntimeId=runtime_id,
                name=endpoint_name,
                description="Production endpoint for mental health support agent"
            )
            
            endpoint_arn = response['agentRuntimeEndpointArn']
            
            print(f"✅ Runtime endpoint created successfully!")
            print(f"Endpoint Name: {endpoint_name}")
            print(f"Endpoint ARN: {endpoint_arn}")
            
            return response
            
        except Exception as e:
            print(f"❌ Error creating runtime endpoint: {str(e)}")
            return None
    
    def test_deployment(self, runtime_arn):
        """Test the deployed AgentCore Runtime"""
        
        print("🧪 Testing AgentCore deployment...")
        
        test_messages = [
            "Hi, I've been feeling really anxious lately",
            "I can't seem to cope with daily tasks anymore"
        ]
        
        for i, message in enumerate(test_messages, 1):
            try:
                response = self.agentcore_runtime.invoke_agent_runtime(
                    agentRuntimeArn=runtime_arn,
                    runtimeSessionId=str(uuid.uuid4()),
                    payload=json.dumps({
                        'input': message,
                        'sessionId': f'test-session-{i}'
                    }),
                    contentType='application/json',
                    accept='application/json'
                )
                
                print(f"\n--- Test {i} ---")
                print(f"Input: {message}")
                print(f"Response: {response.get('payload', 'No response')}")
                
            except Exception as e:
                print(f"❌ Test {i} failed: {str(e)}")
    
    def deploy(self):
        """Main deployment function"""
        
        print("🏥 Mental Health Agent - Amazon Bedrock AgentCore Deployment")
        print("=" * 65)
        
        try:
            # Step 1: Create execution role
            print("\n📋 Step 1: Creating execution role...")
            role_arn = self.create_execution_role()
            
            # Step 2: Create ECR repository
            print("\n📦 Step 2: Creating ECR repository...")
            repo_uri = self.create_ecr_repository()
            
            if not repo_uri:
                print("❌ Deployment failed at ECR repository creation")
                return None
            
            # Step 3: Build and push container
            print("\n🐳 Step 3: Preparing container...")
            container_uri = self.build_and_push_container(repo_uri)
            
            # Step 4: Create AgentCore Runtime
            print("\n🚀 Step 4: Creating AgentCore Runtime...")
            runtime_response = self.create_agent_runtime(role_arn, container_uri)
            
            if not runtime_response:
                print("❌ Deployment failed at runtime creation")
                return None
            
            runtime_id = runtime_response['agentRuntimeId']
            runtime_arn = runtime_response['agentRuntimeArn']
            
            # Step 5: Create runtime endpoint
            print("\n🌐 Step 5: Creating runtime endpoint...")
            endpoint_response = self.create_runtime_endpoint(runtime_id)
            
            # Step 6: Test deployment (after container is pushed)
            print("\n🧪 Step 6: Testing deployment...")
            print("⚠️  Testing will work after you push the container image")
            
            print("\n🎉 AgentCore deployment configuration completed!")
            print(f"Runtime ID: {runtime_id}")
            print(f"Runtime ARN: {runtime_arn}")
            
            if endpoint_response:
                print(f"Endpoint ARN: {endpoint_response['agentRuntimeEndpointArn']}")
            
            print(f"Container URI: {container_uri}")
            
            print("\n📋 Next Steps:")
            print("1. Build and push the Docker container using the commands above")
            print("2. Configure SES for email notifications")
            print("3. Test the agent with real conversations")
            print("4. Set up monitoring and observability")
            print("5. Integrate with your application")
            
            return {
                'runtime_id': runtime_id,
                'runtime_arn': runtime_arn,
                'endpoint': endpoint_response,
                'container_uri': container_uri
            }
            
        except Exception as e:
            print(f"❌ Deployment failed: {str(e)}")
            return None


def main():
    """Main function"""
    deployer = AgentCoreDeployer()
    result = deployer.deploy()
    
    if result:
        print(f"\n✅ AgentCore deployment successful!")
        print(f"Runtime ID: {result['runtime_id']}")
    else:
        print("\n❌ Deployment failed. Check the logs above.")


if __name__ == "__main__":
    main()
