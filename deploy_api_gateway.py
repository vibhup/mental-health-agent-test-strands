#!/usr/bin/env python3
"""
Deploy API Gateway and Lambda function for AgentCore proxy
"""

import boto3
import json
import time

class APIGatewayDeployer:
    def __init__(self):
        self.lambda_client = boto3.client('lambda', region_name='us-east-1')
        self.apigateway = boto3.client('apigateway', region_name='us-east-1')
        self.iam = boto3.client('iam', region_name='us-east-1')
        
        self.function_name = 'mental-health-agentcore-proxy'
        self.api_name = 'mental-health-chatbot-api'
        
    def create_lambda_execution_role(self):
        """Create IAM role for Lambda execution"""
        
        role_name = f"{self.function_name}-role"
        
        trust_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {
                        "Service": "lambda.amazonaws.com"
                    },
                    "Action": "sts:AssumeRole"
                }
            ]
        }
        
        permissions_policy = {
            "Version": "2012-10-17",
            "Statement": [
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
                        "bedrock-agentcore:InvokeAgentRuntime"
                    ],
                    "Resource": "arn:aws:bedrock-agentcore:us-east-1:681007183786:runtime/mental_health_support_agent-lRczXz8e6I"
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
                    Description=f"Execution role for {self.function_name}"
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
                time.sleep(10)
                
            except Exception as e:
                print(f"❌ Error creating role: {str(e)}")
                raise
        
        return role_arn
    
    def create_lambda_function(self, role_arn):
        """Create Lambda function"""
        
        print(f"⚡ Creating Lambda function: {self.function_name}")
        
        try:
            # Check if function exists
            try:
                response = self.lambda_client.get_function(FunctionName=self.function_name)
                function_arn = response['Configuration']['FunctionArn']
                print(f"✅ Using existing Lambda function: {function_arn}")
                return function_arn
                
            except self.lambda_client.exceptions.ResourceNotFoundException:
                pass
            
            # Read the ZIP file
            with open('agentcore_proxy_lambda.zip', 'rb') as zip_file:
                zip_content = zip_file.read()
            
            # Create Lambda function
            response = self.lambda_client.create_function(
                FunctionName=self.function_name,
                Runtime='python3.11',
                Role=role_arn,
                Handler='agentcore_proxy_lambda.lambda_handler',
                Code={'ZipFile': zip_content},
                Description='Proxy function for Mental Health AgentCore',
                Timeout=30,
                Environment={
                    'Variables': {
                        'AGENTCORE_RUNTIME_ARN': 'arn:aws:bedrock-agentcore:us-east-1:681007183786:runtime/mental_health_support_agent-lRczXz8e6I'
                    }
                }
            )
            
            function_arn = response['FunctionArn']
            print(f"✅ Created Lambda function: {function_arn}")
            
            return function_arn
            
        except Exception as e:
            print(f"❌ Error creating Lambda function: {str(e)}")
            return None
    
    def create_api_gateway(self, lambda_arn):
        """Create API Gateway"""
        
        print(f"🌐 Creating API Gateway: {self.api_name}")
        
        try:
            # Create REST API
            api_response = self.apigateway.create_rest_api(
                name=self.api_name,
                description='API for Mental Health Chatbot',
                endpointConfiguration={
                    'types': ['REGIONAL']
                }
            )
            
            api_id = api_response['id']
            print(f"✅ Created API Gateway: {api_id}")
            
            # Get root resource
            resources = self.apigateway.get_resources(restApiId=api_id)
            root_resource_id = None
            
            for resource in resources['items']:
                if resource['path'] == '/':
                    root_resource_id = resource['id']
                    break
            
            # Create /chat resource
            chat_resource = self.apigateway.create_resource(
                restApiId=api_id,
                parentId=root_resource_id,
                pathPart='chat'
            )
            
            chat_resource_id = chat_resource['id']
            print(f"✅ Created /chat resource: {chat_resource_id}")
            
            # Create POST method
            self.apigateway.put_method(
                restApiId=api_id,
                resourceId=chat_resource_id,
                httpMethod='POST',
                authorizationType='NONE'
            )
            
            # Create OPTIONS method for CORS
            self.apigateway.put_method(
                restApiId=api_id,
                resourceId=chat_resource_id,
                httpMethod='OPTIONS',
                authorizationType='NONE'
            )
            
            # Set up Lambda integration for POST
            lambda_uri = f"arn:aws:apigateway:us-east-1:lambda:path/2015-03-31/functions/{lambda_arn}/invocations"
            
            self.apigateway.put_integration(
                restApiId=api_id,
                resourceId=chat_resource_id,
                httpMethod='POST',
                type='AWS_PROXY',
                integrationHttpMethod='POST',
                uri=lambda_uri
            )
            
            # Set up OPTIONS integration for CORS
            self.apigateway.put_integration(
                restApiId=api_id,
                resourceId=chat_resource_id,
                httpMethod='OPTIONS',
                type='MOCK',
                requestTemplates={
                    'application/json': '{"statusCode": 200}'
                }
            )
            
            # Set up OPTIONS method response
            self.apigateway.put_method_response(
                restApiId=api_id,
                resourceId=chat_resource_id,
                httpMethod='OPTIONS',
                statusCode='200',
                responseParameters={
                    'method.response.header.Access-Control-Allow-Headers': False,
                    'method.response.header.Access-Control-Allow-Methods': False,
                    'method.response.header.Access-Control-Allow-Origin': False
                }
            )
            
            # Set up OPTIONS integration response
            self.apigateway.put_integration_response(
                restApiId=api_id,
                resourceId=chat_resource_id,
                httpMethod='OPTIONS',
                statusCode='200',
                responseParameters={
                    'method.response.header.Access-Control-Allow-Headers': "'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'",
                    'method.response.header.Access-Control-Allow-Methods': "'POST,OPTIONS'",
                    'method.response.header.Access-Control-Allow-Origin': "'*'"
                }
            )
            
            # Give API Gateway permission to invoke Lambda
            try:
                self.lambda_client.add_permission(
                    FunctionName=self.function_name,
                    StatementId='api-gateway-invoke',
                    Action='lambda:InvokeFunction',
                    Principal='apigateway.amazonaws.com',
                    SourceArn=f"arn:aws:execute-api:us-east-1:681007183786:{api_id}/*/*"
                )
            except Exception as e:
                if 'ResourceConflictException' not in str(e):
                    print(f"⚠️ Warning: Could not add Lambda permission: {str(e)}")
            
            # Deploy API
            deployment = self.apigateway.create_deployment(
                restApiId=api_id,
                stageName='prod',
                description='Production deployment'
            )
            
            api_url = f"https://{api_id}.execute-api.us-east-1.amazonaws.com/prod"
            
            print(f"✅ API Gateway deployed!")
            print(f"API URL: {api_url}")
            
            return {
                'api_id': api_id,
                'url': api_url,
                'chat_endpoint': f"{api_url}/chat"
            }
            
        except Exception as e:
            print(f"❌ Error creating API Gateway: {str(e)}")
            return None
    
    def deploy(self):
        """Main deployment function"""
        
        print("🌐 Mental Health Chatbot - API Gateway Deployment")
        print("=" * 55)
        
        try:
            # Step 1: Create Lambda execution role
            print("\n📋 Step 1: Creating Lambda execution role...")
            role_arn = self.create_lambda_execution_role()
            
            # Step 2: Create Lambda function
            print("\n⚡ Step 2: Creating Lambda function...")
            lambda_arn = self.create_lambda_function(role_arn)
            
            if not lambda_arn:
                print("❌ Deployment failed at Lambda creation")
                return None
            
            # Step 3: Create API Gateway
            print("\n🌐 Step 3: Creating API Gateway...")
            api_info = self.create_api_gateway(lambda_arn)
            
            if not api_info:
                print("❌ Deployment failed at API Gateway creation")
                return None
            
            print("\n🎉 API Gateway deployment completed successfully!")
            print(f"Chat API Endpoint: {api_info['chat_endpoint']}")
            
            print("\n📋 Next Steps:")
            print("1. Update your chatbot UI script.js with the API endpoint")
            print("2. Test the API endpoint")
            print("3. Your chatbot is ready to use!")
            
            return api_info
            
        except Exception as e:
            print(f"❌ Deployment failed: {str(e)}")
            return None


def main():
    """Main function"""
    deployer = APIGatewayDeployer()
    result = deployer.deploy()
    
    if result:
        print(f"\n✅ API Gateway deployment successful!")
        print(f"Chat Endpoint: {result['chat_endpoint']}")
    else:
        print("\n❌ Deployment failed. Check the logs above.")


if __name__ == "__main__":
    main()
