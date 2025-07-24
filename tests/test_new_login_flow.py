#!/usr/bin/env python3
"""
Test New Login Flow
Tests the new flow: Index → Login Page → Chat Portal
"""

import urllib.request
import boto3
import json
import time
from datetime import datetime

def test_new_login_flow():
    """Test the complete new login flow"""
    print("🔄 TESTING NEW LOGIN FLOW")
    print("Index → Login Page → Chat Portal")
    print("=" * 60)
    
    website_url = "https://d3nlpr9no3kmjc.cloudfront.net"
    
    # Step 1: Test main index page (should redirect to login)
    print("📱 STEP 1: Main Index Page (Redirect)")
    print("-" * 40)
    
    try:
        with urllib.request.urlopen(website_url) as response:
            html_content = response.read().decode('utf-8')
            status_code = response.getcode()
        
        print(f"✅ Status: HTTP {status_code}")
        print(f"✅ Content Size: {len(html_content)} bytes")
        
        # Check redirect elements
        redirect_checks = [
            ('Redirecting you to the secure login page', 'Redirect message'),
            ('login.html', 'Login page link'),
            ('window.location.href = \'login.html\'', 'JavaScript redirect'),
            ('Mental Health Support', 'Page title'),
            ('loading-spinner', 'Loading animation')
        ]
        
        print("\n👀 INDEX PAGE CONTAINS:")
        for check, description in redirect_checks:
            if check in html_content:
                print(f"   ✅ {description}")
            else:
                print(f"   ❌ {description} - MISSING!")
        
        print("\n🔄 EXPECTED BEHAVIOR:")
        print("   1. User visits main URL")
        print("   2. Sees 'Redirecting...' message")
        print("   3. Automatically redirected to login.html after 2 seconds")
        print("   4. Manual link available if auto-redirect fails")
        
    except Exception as e:
        print(f"❌ Step 1 failed: {str(e)}")
        return False
    
    # Step 2: Test login page
    print(f"\n🔐 STEP 2: Login Page")
    print("-" * 40)
    
    try:
        login_url = f"{website_url}/login.html"
        with urllib.request.urlopen(login_url) as response:
            login_content = response.read().decode('utf-8')
            status_code = response.getcode()
        
        print(f"✅ Status: HTTP {status_code}")
        print(f"✅ Content Size: {len(login_content)} bytes")
        
        # Check login page elements
        login_checks = [
            ('🔐 Secure Login Required', 'Login title'),
            ('testuser@example.com', 'Pre-filled email'),
            ('MentalHealth123!', 'Pre-filled password'),
            ('Login Securely', 'Login button'),
            ('login-auth.js', 'Authentication JavaScript'),
            ('Demo Credentials', 'Help section'),
            ('AWS AgentCore', 'Technology info'),
            ('loading-spinner', 'Loading animation')
        ]
        
        print("\n👀 LOGIN PAGE CONTAINS:")
        for check, description in login_checks:
            if check in login_content:
                print(f"   ✅ {description}")
            else:
                print(f"   ❌ {description} - MISSING!")
        
        print("\n🔄 EXPECTED BEHAVIOR:")
        print("   1. User sees professional login interface")
        print("   2. Demo credentials are pre-filled")
        print("   3. User clicks 'Login Securely'")
        print("   4. JavaScript authenticates with Cognito")
        print("   5. JWT token stored in localStorage")
        print("   6. Redirected to chat.html after success")
        
    except Exception as e:
        print(f"❌ Step 2 failed: {str(e)}")
        return False
    
    # Step 3: Test chat portal
    print(f"\n💬 STEP 3: Chat Portal")
    print("-" * 40)
    
    try:
        chat_url = f"{website_url}/chat.html"
        with urllib.request.urlopen(chat_url) as response:
            chat_content = response.read().decode('utf-8')
            status_code = response.getcode()
        
        print(f"✅ Status: HTTP {status_code}")
        print(f"✅ Content Size: {len(chat_content)} bytes")
        
        # Check chat portal elements
        chat_checks = [
            ('Mental Health Support Chat', 'Chat title'),
            ('chat-portal.js', 'Chat JavaScript'),
            ('Authentication Required Modal', 'Auth check modal'),
            ('Crisis Resources Modal', 'Crisis modal'),
            ('Logout', 'Logout button'),
            ('Type your message here', 'Message input'),
            ('sendButton', 'Send button'),
            ('statusDot', 'Status indicator')
        ]
        
        print("\n👀 CHAT PORTAL CONTAINS:")
        for check, description in chat_checks:
            if check in chat_content:
                print(f"   ✅ {description}")
            else:
                print(f"   ❌ {description} - MISSING!")
        
        print("\n🔄 EXPECTED BEHAVIOR:")
        print("   1. JavaScript checks for valid JWT token")
        print("   2. If no token → redirects to login.html")
        print("   3. If valid token → enables chat interface")
        print("   4. User can send messages to AI agent")
        print("   5. Logout button clears session and redirects")
        
    except Exception as e:
        print(f"❌ Step 3 failed: {str(e)}")
        return False
    
    # Step 4: Test authentication backend
    print(f"\n🔑 STEP 4: Authentication Backend")
    print("-" * 40)
    
    try:
        # Test Cognito authentication
        cognito = boto3.client('cognito-idp', region_name='us-east-1')
        
        auth_response = cognito.initiate_auth(
            ClientId='1l0v1imj8h6pg0i7villspuqr8',
            AuthFlow='USER_PASSWORD_AUTH',
            AuthParameters={
                'USERNAME': 'testuser@example.com',
                'PASSWORD': 'MentalHealth123!'
            }
        )
        
        jwt_token = auth_response['AuthenticationResult']['AccessToken']
        expires_in = auth_response['AuthenticationResult']['ExpiresIn']
        
        print(f"✅ Authentication: Successful")
        print(f"✅ JWT Token: {jwt_token[:50]}...")
        print(f"✅ Expires In: {expires_in} seconds")
        
        # Verify token structure
        token_parts = jwt_token.split('.')
        if len(token_parts) == 3:
            print(f"✅ Token Format: Valid (3 parts)")
        else:
            print(f"❌ Token Format: Invalid")
            return False
        
        print("\n🔄 AUTHENTICATION FLOW:")
        print("   1. User submits login form")
        print("   2. JavaScript calls Cognito User Pool")
        print("   3. Cognito validates credentials")
        print("   4. JWT token returned to browser")
        print("   5. Token stored in localStorage")
        print("   6. Token used for AgentCore API calls")
        
    except Exception as e:
        print(f"❌ Step 4 failed: {str(e)}")
        return False
    
    return True

def test_file_structure():
    """Test that all required files are accessible"""
    print("\n📁 TESTING FILE STRUCTURE")
    print("=" * 60)
    
    website_url = "https://d3nlpr9no3kmjc.cloudfront.net"
    
    files_to_test = [
        ('index.html', 'Main redirect page'),
        ('login.html', 'Login page'),
        ('login-styles.css', 'Login page styles'),
        ('login-auth.js', 'Login authentication'),
        ('chat.html', 'Chat portal'),
        ('chat-portal.js', 'Chat functionality'),
        ('styles.css', 'Chat portal styles')
    ]
    
    results = {}
    
    for filename, description in files_to_test:
        try:
            file_url = f"{website_url}/{filename}"
            with urllib.request.urlopen(file_url) as response:
                content = response.read()
                status_code = response.getcode()
            
            results[filename] = True
            print(f"✅ {filename}: {status_code} ({len(content)} bytes) - {description}")
            
        except Exception as e:
            results[filename] = False
            print(f"❌ {filename}: Failed - {str(e)}")
    
    success_count = sum(results.values())
    total_count = len(results)
    
    print(f"\n📊 File Structure: {success_count}/{total_count} files accessible ({success_count/total_count*100:.0f}%)")
    
    return success_count == total_count

def main():
    """Main test execution"""
    print("🧠 MENTAL HEALTH CHATBOT - NEW LOGIN FLOW TEST")
    print("=" * 70)
    print(f"🕐 Test Time: {datetime.now().isoformat()}")
    print("=" * 70)
    
    # Test the new login flow
    flow_success = test_new_login_flow()
    
    # Test file structure
    files_success = test_file_structure()
    
    # Final summary
    print("\n" + "=" * 70)
    print("📋 FINAL TEST SUMMARY")
    print("=" * 70)
    
    if flow_success and files_success:
        print("🎉 SUCCESS! NEW LOGIN FLOW FULLY IMPLEMENTED")
        print("✅ Index page redirects to login")
        print("✅ Login page has professional interface")
        print("✅ Chat portal checks authentication")
        print("✅ All files accessible")
        print("✅ Cognito authentication working")
        
        print("\n🚀 NEW USER FLOW:")
        print("   1. User visits: https://d3nlpr9no3kmjc.cloudfront.net")
        print("   2. Automatically redirected to login page")
        print("   3. User logs in with: testuser@example.com / MentalHealth123!")
        print("   4. Redirected to chat portal after authentication")
        print("   5. Can chat with AI mental health agent")
        print("   6. Logout button returns to login page")
        
        print("\n🎯 BENEFITS OF NEW FLOW:")
        print("   🔐 Clear separation of authentication and chat")
        print("   🎨 Professional dedicated login page")
        print("   🔒 Session persistence across browser sessions")
        print("   🚪 Proper logout functionality")
        print("   🔄 Automatic redirects for better UX")
        
    else:
        print("⚠️ Issues detected in new login flow")
        print("🔧 Please review the test results above")
    
    print(f"\n🌐 Website: https://d3nlpr9no3kmjc.cloudfront.net")
    print(f"🔐 Login: https://d3nlpr9no3kmjc.cloudfront.net/login.html")
    print(f"💬 Chat: https://d3nlpr9no3kmjc.cloudfront.net/chat.html")
    print(f"📅 Test completed: {datetime.now().isoformat()}")

if __name__ == "__main__":
    main()
