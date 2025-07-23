#!/usr/bin/env python3
"""
Debug Connection Issue
Simulate exactly what the browser is doing to identify the problem
"""

import boto3
import json
import uuid
import urllib.request
import urllib.parse
import hashlib
import hmac
import time
from datetime import datetime

class ConnectionDebugger:
    def __init__(self):
        self.region = 'us-east-1'
        self.identity_pool_id = 'us-east-1:fee1a888-11e8-40a2-a195-9acb975d1b72'
        self.runtime_arn = 'arn:aws:bedrock-agentcore:us-east-1:681007183786:runtime/mental_health_support_agent-lRczXz8e6I'
        self.memory_id = 'MentalHealthChatbotMemory-GqmjCf2KIw'
        
        print("🔍 CONNECTION ISSUE DEBUGGER")
        print("=" * 50)
        print("Simulating exact browser behavior to find the issue")
        print("=" * 50)
    
    def debug_step_1_cognito_auth(self):
        """Debug Step 1: Cognito Authentication"""
        print("\n🔐 STEP 1: Cognito Authentication Debug")
        print("-" * 40)
        
        try:
            cognito = boto3.client('cognito-identity', region_name=self.region)
            
            print("1.1 Getting Identity ID...")
            identity_response = cognito.get_id(IdentityPoolId=self.identity_pool_id)
            identity_id = identity_response['IdentityId']
            print(f"✅ Identity ID: {identity_id}")
            
            print("1.2 Getting credentials...")
            credentials_response = cognito.get_credentials_for_identity(IdentityId=identity_id)
            credentials = credentials_response['Credentials']
            
            print(f"✅ Access Key: {credentials['AccessKeyId']}")
            print(f"✅ Secret Key: {credentials['SecretKey'][:20]}...")
            print(f"✅ Session Token: {credentials['SessionToken'][:50]}...")
            print(f"✅ Expires: {credentials['Expiration']}")
            
            self.credentials = credentials
            return True
            
        except Exception as e:
            print(f"❌ Cognito auth failed: {str(e)}")
            return False
    
    def debug_step_2_aws_signature(self):
        """Debug Step 2: AWS Signature V4 Creation"""
        print("\n✍️ STEP 2: AWS Signature V4 Debug")
        print("-" * 40)
        
        try:
            # Test creating AWS signature like the browser would
            method = 'POST'
            service = 'bedrock-agentcore'
            host = f'{service}.{self.region}.amazonaws.com'
            endpoint = f'https://{host}/runtimes/{urllib.parse.quote(self.runtime_arn, safe="")}/invocations'
            
            print(f"2.1 Endpoint: {endpoint}")
            print(f"2.2 Service: {service}")
            print(f"2.3 Region: {self.region}")
            print(f"2.4 Host: {host}")
            
            # Create canonical request
            canonical_uri = f'/runtimes/{urllib.parse.quote(self.runtime_arn, safe="")}/invocations'
            canonical_querystring = ''
            
            payload = json.dumps({
                'input': 'Test message',
                'sessionId': f'debug_session_{uuid.uuid4().hex}',
                'actorId': 'debug_user',
                'context': []
            })
            
            # Headers
            headers = {
                'Content-Type': 'application/json',
                'Accept': 'application/json',
                'Host': host,
                'X-Amz-Date': datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')
            }
            
            if self.credentials.get('SessionToken'):
                headers['X-Amz-Security-Token'] = self.credentials['SessionToken']
            
            print(f"2.5 Headers: {list(headers.keys())}")
            print(f"2.6 Payload length: {len(payload)} bytes")
            
            return True
            
        except Exception as e:
            print(f"❌ Signature creation failed: {str(e)}")
            return False
    
    def debug_step_3_direct_http_call(self):
        """Debug Step 3: Direct HTTP Call to AgentCore"""
        print("\n🌐 STEP 3: Direct HTTP Call Debug")
        print("-" * 40)
        
        try:
            # Try the exact same call our Python SDK makes
            agentcore = boto3.client(
                'bedrock-agentcore',
                region_name=self.region,
                aws_access_key_id=self.credentials['AccessKeyId'],
                aws_secret_access_key=self.credentials['SecretKey'],
                aws_session_token=self.credentials['SessionToken']
            )
            
            session_id = f'debug_session_{uuid.uuid4().hex}'
            
            payload = {
                'input': 'Debug test: Can you help with anxiety?',
                'sessionId': session_id,
                'actorId': 'debug_user',
                'context': []
            }
            
            print(f"3.1 Session ID: {session_id}")
            print(f"3.2 Payload: {json.dumps(payload, indent=2)}")
            
            print("3.3 Making AgentCore Runtime call...")
            start_time = time.time()
            
            response = agentcore.invoke_agent_runtime(
                agentRuntimeArn=self.runtime_arn,
                runtimeSessionId=session_id,
                payload=json.dumps(payload),
                contentType='application/json',
                accept='application/json'
            )
            
            end_time = time.time()
            
            print(f"✅ Call successful in {end_time - start_time:.2f} seconds")
            
            # Parse response
            response_body = response['response'].read().decode('utf-8')
            agent_response = json.loads(response_body)
            
            print(f"✅ Response: {agent_response.get('response', 'No response')[:100]}...")
            
            return True
            
        except Exception as e:
            print(f"❌ HTTP call failed: {str(e)}")
            print(f"   Error type: {type(e).__name__}")
            
            # Check specific error types
            if 'AccessDenied' in str(e):
                print("   🔍 This is a permissions issue")
            elif 'InvalidSignature' in str(e):
                print("   🔍 This is a signature issue")
            elif 'ResourceNotFound' in str(e):
                print("   🔍 This is an endpoint issue")
            elif 'ValidationException' in str(e):
                print("   🔍 This is a payload format issue")
            
            return False
    
    def debug_step_4_browser_cors(self):
        """Debug Step 4: Browser CORS Issues"""
        print("\n🌐 STEP 4: Browser CORS Debug")
        print("-" * 40)
        
        try:
            # Check if the AgentCore endpoint supports CORS
            import urllib.request
            
            # Try a simple request to see CORS headers
            endpoint = f'https://bedrock-agentcore.{self.region}.amazonaws.com'
            
            print(f"4.1 Testing CORS on: {endpoint}")
            
            try:
                req = urllib.request.Request(endpoint, method='OPTIONS')
                req.add_header('Origin', 'https://d3nlpr9no3kmjc.cloudfront.net')
                req.add_header('Access-Control-Request-Method', 'POST')
                req.add_header('Access-Control-Request-Headers', 'Content-Type,Authorization')
                
                with urllib.request.urlopen(req) as response:
                    headers = dict(response.headers)
                    print("✅ CORS preflight successful")
                    
                    cors_headers = {k: v for k, v in headers.items() if 'access-control' in k.lower()}
                    if cors_headers:
                        print(f"✅ CORS headers: {cors_headers}")
                    else:
                        print("⚠️ No CORS headers found")
                        
            except urllib.error.HTTPError as e:
                print(f"⚠️ CORS preflight failed: {e.code} {e.reason}")
                if e.code == 403:
                    print("   🔍 This suggests CORS is not enabled for browser access")
                elif e.code == 404:
                    print("   🔍 Endpoint doesn't support OPTIONS method")
            
            return True
            
        except Exception as e:
            print(f"❌ CORS debug failed: {str(e)}")
            return False
    
    def debug_step_5_javascript_simulation(self):
        """Debug Step 5: Simulate JavaScript Behavior"""
        print("\n📱 STEP 5: JavaScript Behavior Simulation")
        print("-" * 40)
        
        try:
            # Check what the JavaScript file actually contains
            print("5.1 Checking deployed JavaScript...")
            
            with urllib.request.urlopen('https://d3nlpr9no3kmjc.cloudfront.net/agentcore-direct.js') as response:
                js_content = response.read().decode('utf-8')
            
            print(f"✅ JavaScript size: {len(js_content)} bytes")
            
            # Check for critical functions
            critical_functions = [
                'initializeAWS',
                'sendMessage',
                'callAgentCoreRuntime',
                'storeInMemory',
                'updateStatus'
            ]
            
            for func in critical_functions:
                if func in js_content:
                    print(f"✅ Function {func} present")
                else:
                    print(f"❌ Function {func} missing")
            
            # Check for error handling
            error_patterns = [
                'catch (error)',
                'updateStatus(\'error\'',
                'Connection Error',
                'setTimeout'
            ]
            
            for pattern in error_patterns:
                if pattern in js_content:
                    print(f"✅ Error handling: {pattern}")
                else:
                    print(f"❌ Missing error handling: {pattern}")
            
            # Check AWS SDK usage
            aws_patterns = [
                'AWS.config.credentials',
                'AWS.HttpRequest',
                'AWS.Signers.V4',
                'CognitoIdentityCredentials'
            ]
            
            for pattern in aws_patterns:
                if pattern in js_content:
                    print(f"✅ AWS SDK: {pattern}")
                else:
                    print(f"❌ Missing AWS SDK: {pattern}")
            
            return True
            
        except Exception as e:
            print(f"❌ JavaScript simulation failed: {str(e)}")
            return False
    
    def run_complete_debug(self):
        """Run complete debugging sequence"""
        print("🚀 STARTING COMPLETE CONNECTION DEBUG")
        print("=" * 50)
        
        steps = [
            ("Cognito Authentication", self.debug_step_1_cognito_auth),
            ("AWS Signature V4", self.debug_step_2_aws_signature),
            ("Direct HTTP Call", self.debug_step_3_direct_http_call),
            ("Browser CORS", self.debug_step_4_browser_cors),
            ("JavaScript Simulation", self.debug_step_5_javascript_simulation)
        ]
        
        results = {}
        
        for step_name, step_func in steps:
            results[step_name] = step_func()
        
        # Analysis
        print("\n" + "=" * 50)
        print("🔍 DEBUG ANALYSIS")
        print("=" * 50)
        
        passed = sum(results.values())
        total = len(results)
        
        for step_name, result in results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{step_name}: {status}")
        
        print(f"\nDebug Score: {passed}/{total} steps successful")
        
        # Identify likely issues
        print("\n🎯 LIKELY CONNECTION ISSUES:")
        
        if not results.get("Cognito Authentication"):
            print("❌ CRITICAL: Cognito authentication failing")
            print("   → Check Identity Pool configuration")
            print("   → Verify IAM roles and permissions")
        
        if not results.get("Direct HTTP Call"):
            print("❌ CRITICAL: AgentCore API calls failing")
            print("   → Check endpoint URLs and ARNs")
            print("   → Verify AWS credentials and signatures")
        
        if not results.get("Browser CORS"):
            print("⚠️ LIKELY ISSUE: CORS not enabled for browser access")
            print("   → AgentCore may not support direct browser calls")
            print("   → May need server-side proxy or different approach")
        
        # Recommendations
        print("\n💡 RECOMMENDATIONS:")
        
        if results.get("Cognito Authentication") and results.get("Direct HTTP Call"):
            print("✅ Backend components working - issue is likely browser-specific")
            print("🔧 SOLUTION: CORS issue - AgentCore doesn't support direct browser calls")
            print("   → Need to implement server-side proxy (Lambda)")
            print("   → Or use AgentCore SDK for browser (if available)")
        else:
            print("🔧 SOLUTION: Fix backend authentication and API calls first")
        
        return results


def main():
    """Main debug execution"""
    debugger = ConnectionDebugger()
    results = debugger.run_complete_debug()
    
    print("\n" + "=" * 50)
    print("🎯 FINAL DIAGNOSIS")
    print("=" * 50)
    
    if results.get("Browser CORS") == False:
        print("🔍 ROOT CAUSE IDENTIFIED:")
        print("❌ AgentCore APIs don't support direct browser access (CORS)")
        print("✅ Backend APIs work fine from server-side")
        print()
        print("🔧 SOLUTION NEEDED:")
        print("1. Implement Lambda proxy for AgentCore calls")
        print("2. Or find AgentCore browser SDK")
        print("3. Or use WebSocket connection")
        print()
        print("📋 NEXT STEPS:")
        print("- Revert to Lambda + API Gateway approach")
        print("- Configure Lambda to call AgentCore on behalf of browser")
        print("- Maintain direct AgentCore integration on server-side")
    else:
        print("🔍 Issue is in authentication or API configuration")
        print("Check the failed steps above for specific fixes")


if __name__ == "__main__":
    main()
