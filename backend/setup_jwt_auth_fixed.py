#!/usr/bin/env python3
"""
Setup JWT Authentication for Direct Browser Access
Creates Cognito User Pool and configures AgentCore Runtime for JWT authentication
"""

import boto3
import json
import time

class JWTAuthSetup:
    def __init__(self):
        self.region = 'us-east-1'
        self.runtime_id = 'mental_health_support_agent-lRczXz8e6I'
        self.runtime_arn = 'arn:aws:bedrock-agentcore:us-east-1:681007183786:runtime/mental_health_support_agent-lRczXz8e6I'
        
        print("🔐 SETTING UP JWT AUTHENTICATION FOR DIRECT BROWSER ACCESS")
        print("=" * 70)
        print("This will enable direct browser access to AgentCore Runtime")
        print("=" * 70)
    
    def step_1_create_cognito_user_pool(self):
        """Step 1: Create Cognito User Pool for JWT tokens"""
        print("\n🏗️ STEP 1: Creating Cognito User Pool")
        print("-" * 50)
        
        try:
            cognito_idp = boto3.client('cognito-idp', region_name=self.region)
            
            # Create User Pool
            print("1.1 Creating User Pool...")
            user_pool_response = cognito_idp.create_user_pool(
                PoolName='MentalHealthChatbotUserPool',
                Policies={
                    'PasswordPolicy': {
                        'MinimumLength': 8,
                        'RequireUppercase': False,
                        'RequireLowercase': False,
                        'RequireNumbers': False,
                        'RequireSymbols': False
                    }
                },
                AutoVerifiedAttributes=['email'],
                UsernameAttributes=['email']
            )
            
            user_pool_id = user_pool_response['UserPool']['Id']
            print(f"✅ User Pool created: {user_pool_id}")
            
            # Create User Pool Client
            print("1.2 Creating User Pool Client...")
            client_response = cognito_idp.create_user_pool_client(
                UserPoolId=user_pool_id,
                ClientName='MentalHealthChatbotClient',
                GenerateSecret=False,  # No secret for browser clients
                ExplicitAuthFlows=[
                    'ALLOW_USER_PASSWORD_AUTH',
                    'ALLOW_REFRESH_TOKEN_AUTH',
                    'ALLOW_USER_SRP_AUTH'
                ]
            )
            
            client_id = client_response['UserPoolClient']['ClientId']
            print(f"✅ User Pool Client created: {client_id}")
            
            # Create discovery URL
            discovery_url = f"https://cognito-idp.{self.region}.amazonaws.com/{user_pool_id}/.well-known/openid-configuration"
            print(f"✅ Discovery URL: {discovery_url}")
            
            # Create a test user
            print("1.3 Creating test user...")
            try:
                cognito_idp.admin_create_user(
                    UserPoolId=user_pool_id,
                    Username='testuser@example.com',
                    TemporaryPassword='TempPass123!',
                    MessageAction='SUPPRESS'
                )
                
                # Set permanent password
                cognito_idp.admin_set_user_password(
                    UserPoolId=user_pool_id,
                    Username='testuser@example.com',
                    Password='MentalHealth123!',
                    Permanent=True
                )
                
                print("✅ Test user created: testuser@example.com / MentalHealth123!")
                
            except Exception as e:
                if 'UsernameExistsException' in str(e):
                    print("✅ Test user already exists")
                else:
                    print(f"⚠️ Test user creation failed: {str(e)}")
            
            self.user_pool_id = user_pool_id
            self.client_id = client_id
            self.discovery_url = discovery_url
            
            return True
            
        except Exception as e:
            print(f"❌ Cognito User Pool creation failed: {str(e)}")
            return False
    
    def step_2_update_agentcore_runtime(self):
        """Step 2: Update AgentCore Runtime for JWT authentication"""
        print("\n🤖 STEP 2: Updating AgentCore Runtime for JWT Authentication")
        print("-" * 50)
        
        try:
            agentcore_control = boto3.client('bedrock-agentcore-control', region_name=self.region)
            
            print("2.1 Getting current runtime configuration...")
            current_runtime = agentcore_control.get_agent_runtime(
                agentRuntimeId=self.runtime_id
            )
            
            print(f"✅ Current runtime status: {current_runtime['status']}")
            
            print("2.2 Updating runtime with JWT authorizer...")
            
            # Update the runtime with JWT authorizer configuration
            # Include all required parameters from current configuration
            update_response = agentcore_control.update_agent_runtime(
                agentRuntimeId=self.runtime_id,
                agentRuntimeArtifact=current_runtime['agentRuntimeArtifact'],
                roleArn=current_runtime['roleArn'],
                networkConfiguration=current_runtime['networkConfiguration'],
                authorizerConfiguration={
                    'customJWTAuthorizer': {
                        'discoveryUrl': self.discovery_url,
                        'allowedClients': [self.client_id]
                    }
                },
                # Include optional parameters if they exist
                **({
                    'description': current_runtime['description']
                } if 'description' in current_runtime else {}),
                **({
                    'protocolConfiguration': current_runtime['protocolConfiguration']
                } if 'protocolConfiguration' in current_runtime else {}),
                **({
                    'environmentVariables': current_runtime['environmentVariables']
                } if 'environmentVariables' in current_runtime else {})
            )
            
            print("✅ AgentCore Runtime updated with JWT authorizer")
            print(f"   Discovery URL: {self.discovery_url}")
            print(f"   Allowed Client: {self.client_id}")
            
            # Wait for update to complete
            print("2.3 Waiting for runtime update to complete...")
            for i in range(30):  # Wait up to 5 minutes
                time.sleep(10)
                runtime_status = agentcore_control.get_agent_runtime(
                    agentRuntimeId=self.runtime_id
                )
                
                status = runtime_status['status']
                print(f"   Status: {status} ({i+1}/30)")
                
                if status == 'READY':
                    print("✅ Runtime update completed successfully")
                    break
                elif status == 'FAILED':
                    print("❌ Runtime update failed")
                    return False
            else:
                print("⚠️ Runtime update taking longer than expected, but continuing...")
            
            return True
            
        except Exception as e:
            print(f"❌ AgentCore Runtime update failed: {str(e)}")
            return False
    
    def step_3_test_jwt_authentication(self):
        """Step 3: Test JWT authentication"""
        print("\n🧪 STEP 3: Testing JWT Authentication")
        print("-" * 50)
        
        try:
            cognito_idp = boto3.client('cognito-idp', region_name=self.region)
            
            print("3.1 Getting JWT token for test user...")
            
            # Authenticate and get JWT token
            auth_response = cognito_idp.initiate_auth(
                ClientId=self.client_id,
                AuthFlow='USER_PASSWORD_AUTH',
                AuthParameters={
                    'USERNAME': 'testuser@example.com',
                    'PASSWORD': 'MentalHealth123!'
                }
            )
            
            access_token = auth_response['AuthenticationResult']['AccessToken']
            print(f"✅ JWT Access Token obtained: {access_token[:50]}...")
            
            print("3.2 Testing AgentCore Runtime call with JWT token...")
            
            import requests
            import urllib.parse
            
            # URL encode the agent ARN
            escaped_agent_arn = urllib.parse.quote(self.runtime_arn, safe='')
            
            # Construct the URL
            url = f"https://bedrock-agentcore.{self.region}.amazonaws.com/runtimes/{escaped_agent_arn}/invocations"
            
            # Set up headers
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
                "X-Amzn-Bedrock-AgentCore-Runtime-Session-Id": "jwt_test_session_123"
            }
            
            # Test payload
            payload = {
                "input": "Hello, I need help with anxiety. Can you support me?",
                "sessionId": "jwt_test_session_123",
                "actorId": "jwt_test_user",
                "context": []
            }
            
            print(f"   URL: {url}")
            print(f"   Payload: {payload['input']}")
            
            # Make the request
            response = requests.post(
                url,
                headers=headers,
                json=payload,
                timeout=30
            )
            
            print(f"✅ Response Status: {response.status_code}")
            
            if response.status_code == 200:
                response_data = response.json()
                agent_response = response_data.get('response', 'No response')
                print(f"✅ Agent Response: {agent_response[:100]}...")
                print("🎉 JWT Authentication working successfully!")
                
                self.jwt_token = access_token
                return True
            else:
                print(f"❌ Request failed: {response.status_code}")
                print(f"   Error: {response.text}")
                return False
            
        except Exception as e:
            print(f"❌ JWT authentication test failed: {str(e)}")
            return False
    
    def run_setup(self):
        """Run the JWT authentication setup"""
        print("🚀 STARTING JWT AUTHENTICATION SETUP")
        print("=" * 70)
        
        steps = [
            ("Create Cognito User Pool", self.step_1_create_cognito_user_pool),
            ("Update AgentCore Runtime", self.step_2_update_agentcore_runtime),
            ("Test JWT Authentication", self.step_3_test_jwt_authentication)
        ]
        
        results = {}
        
        for step_name, step_func in steps:
            results[step_name] = step_func()
            if not results[step_name]:
                print(f"\n❌ Setup failed at: {step_name}")
                break
        
        # Final summary
        print("\n" + "=" * 70)
        print("🏆 JWT AUTHENTICATION SETUP RESULTS")
        print("=" * 70)
        
        passed = sum(results.values())
        total = len(results)
        
        for step_name, result in results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{step_name}: {status}")
        
        if passed == total:
            print("\n🎉 JWT AUTHENTICATION SETUP COMPLETE!")
            print("✅ AgentCore Runtime now supports direct browser access")
            print("✅ Users can authenticate with JWT tokens")
            print("✅ No Lambda proxy needed")
            print("\n📋 CONFIGURATION:")
            print(f"   User Pool ID: {self.user_pool_id}")
            print(f"   Client ID: {self.client_id}")
            print(f"   Discovery URL: {self.discovery_url}")
            print(f"   Test User: testuser@example.com / MentalHealth123!")
            print("\n🔐 CONNECTION ERROR SHOULD BE RESOLVED!")
        else:
            print("\n⚠️ SETUP INCOMPLETE")
            print("Some steps failed - check the logs above")
        
        return results


def main():
    """Main setup execution"""
    setup = JWTAuthSetup()
    results = setup.run_setup()
    
    if sum(results.values()) == len(results):
        print("\n" + "=" * 70)
        print("🎯 NEXT STEPS TO FIX CONNECTION ERROR:")
        print("=" * 70)
        print("1. Update your browser JavaScript to use JWT authentication")
        print("2. Replace Cognito Identity Pool with Cognito User Pool")
        print("3. Use Bearer tokens instead of AWS SigV4")
        print("4. Test the direct browser access")
        print("\nThe AgentCore Runtime is now configured for direct browser access!")


if __name__ == "__main__":
    main()
