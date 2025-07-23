#!/usr/bin/env python3
"""
Deploy Mental Health Chatbot UI to S3 with CloudFront
"""

import boto3
import json
import time
import os
from datetime import datetime

class WebsiteDeployer:
    def __init__(self):
        self.s3 = boto3.client('s3', region_name='us-east-1')
        self.cloudfront = boto3.client('cloudfront', region_name='us-east-1')
        self.iam = boto3.client('iam', region_name='us-east-1')
        
        # Configuration
        self.bucket_name = f"mental-health-chatbot-{int(time.time())}"
        self.website_files = [
            'index.html',
            'styles.css', 
            'script.js',
            'sw.js',
            'error.html'
        ]
        
    def create_s3_bucket(self):
        """Create S3 bucket for static website hosting"""
        
        print(f"📦 Creating S3 bucket: {self.bucket_name}")
        
        try:
            # Create bucket
            self.s3.create_bucket(Bucket=self.bucket_name)
            
            # Configure for static website hosting
            website_config = {
                'IndexDocument': {'Suffix': 'index.html'},
                'ErrorDocument': {'Key': 'error.html'}
            }
            
            self.s3.put_bucket_website(
                Bucket=self.bucket_name,
                WebsiteConfiguration=website_config
            )
            
            # Block public access (we'll use OAI)
            self.s3.put_public_access_block(
                Bucket=self.bucket_name,
                PublicAccessBlockConfiguration={
                    'BlockPublicAcls': True,
                    'IgnorePublicAcls': True,
                    'BlockPublicPolicy': False,  # Allow CloudFront OAI
                    'RestrictPublicBuckets': False
                }
            )
            
            print(f"✅ S3 bucket created: {self.bucket_name}")
            return self.bucket_name
            
        except Exception as e:
            print(f"❌ Error creating S3 bucket: {str(e)}")
            return None
    
    def create_oai(self):
        """Create Origin Access Identity for CloudFront"""
        
        print("🔐 Creating CloudFront Origin Access Identity...")
        
        try:
            response = self.cloudfront.create_cloud_front_origin_access_identity(
                CloudFrontOriginAccessIdentityConfig={
                    'CallerReference': f'mental-health-chatbot-{int(time.time())}',
                    'Comment': 'OAI for Mental Health Chatbot'
                }
            )
            
            oai_id = response['CloudFrontOriginAccessIdentity']['Id']
            print(f"✅ OAI created: {oai_id}")
            return oai_id
            
        except Exception as e:
            print(f"❌ Error creating OAI: {str(e)}")
            return None
    
    def set_bucket_policy(self, oai_id):
        """Set S3 bucket policy to allow CloudFront OAI access"""
        
        print("📋 Setting S3 bucket policy for OAI access...")
        
        bucket_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Sid": "AllowCloudFrontAccess",
                    "Effect": "Allow",
                    "Principal": {
                        "AWS": f"arn:aws:iam::cloudfront:user/CloudFront Origin Access Identity {oai_id}"
                    },
                    "Action": "s3:GetObject",
                    "Resource": f"arn:aws:s3:::{self.bucket_name}/*"
                }
            ]
        }
        
        try:
            self.s3.put_bucket_policy(
                Bucket=self.bucket_name,
                Policy=json.dumps(bucket_policy)
            )
            print("✅ Bucket policy set successfully")
            
        except Exception as e:
            print(f"❌ Error setting bucket policy: {str(e)}")
    
    def upload_website_files(self):
        """Upload website files to S3"""
        
        print("📤 Uploading website files to S3...")
        
        content_types = {
            '.html': 'text/html',
            '.css': 'text/css',
            '.js': 'application/javascript',
            '.json': 'application/json'
        }
        
        for filename in self.website_files:
            file_path = f"chatbot-ui/{filename}"
            
            if not os.path.exists(file_path):
                print(f"⚠️ File not found: {file_path}")
                continue
            
            # Determine content type
            ext = os.path.splitext(filename)[1]
            content_type = content_types.get(ext, 'text/plain')
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                self.s3.put_object(
                    Bucket=self.bucket_name,
                    Key=filename,
                    Body=content,
                    ContentType=content_type,
                    CacheControl='max-age=86400'  # 24 hours
                )
                
                print(f"✅ Uploaded: {filename}")
                
            except Exception as e:
                print(f"❌ Error uploading {filename}: {str(e)}")
    
    def create_cloudfront_distribution(self, oai_id):
        """Create CloudFront distribution"""
        
        print("☁️ Creating CloudFront distribution...")
        
        distribution_config = {
            'CallerReference': f'mental-health-chatbot-{int(time.time())}',
            'Comment': 'Mental Health Chatbot UI Distribution',
            'DefaultRootObject': 'index.html',
            'Origins': {
                'Quantity': 1,
                'Items': [
                    {
                        'Id': f'{self.bucket_name}-origin',
                        'DomainName': f'{self.bucket_name}.s3.amazonaws.com',
                        'S3OriginConfig': {
                            'OriginAccessIdentity': f'origin-access-identity/cloudfront/{oai_id}'
                        }
                    }
                ]
            },
            'DefaultCacheBehavior': {
                'TargetOriginId': f'{self.bucket_name}-origin',
                'ViewerProtocolPolicy': 'redirect-to-https',
                'TrustedSigners': {
                    'Enabled': False,
                    'Quantity': 0
                },
                'ForwardedValues': {
                    'QueryString': False,
                    'Cookies': {'Forward': 'none'}
                },
                'MinTTL': 0,
                'DefaultTTL': 86400,
                'MaxTTL': 31536000
            },
            'CustomErrorResponses': {
                'Quantity': 1,
                'Items': [
                    {
                        'ErrorCode': 404,
                        'ResponsePagePath': '/error.html',
                        'ResponseCode': '200',
                        'ErrorCachingMinTTL': 300
                    }
                ]
            },
            'Enabled': True,
            'PriceClass': 'PriceClass_100'  # Use only US, Canada, Europe
        }
        
        try:
            response = self.cloudfront.create_distribution(
                DistributionConfig=distribution_config
            )
            
            distribution_id = response['Distribution']['Id']
            domain_name = response['Distribution']['DomainName']
            
            print(f"✅ CloudFront distribution created!")
            print(f"Distribution ID: {distribution_id}")
            print(f"Domain Name: {domain_name}")
            
            return {
                'id': distribution_id,
                'domain': domain_name
            }
            
        except Exception as e:
            print(f"❌ Error creating CloudFront distribution: {str(e)}")
            return None
    
    def wait_for_distribution(self, distribution_id):
        """Wait for CloudFront distribution to be deployed"""
        
        print("⏳ Waiting for CloudFront distribution to deploy...")
        print("This may take 10-15 minutes...")
        
        max_attempts = 60  # 30 minutes max
        attempt = 0
        
        while attempt < max_attempts:
            try:
                response = self.cloudfront.get_distribution(Id=distribution_id)
                status = response['Distribution']['Status']
                
                if status == 'Deployed':
                    print("✅ CloudFront distribution is deployed!")
                    return True
                else:
                    print(f"⏳ Status: {status} (attempt {attempt + 1}/{max_attempts})")
                    time.sleep(30)
                    attempt += 1
                    
            except Exception as e:
                print(f"❌ Error checking distribution status: {str(e)}")
                time.sleep(30)
                attempt += 1
        
        print("⚠️ Distribution deployment timeout, but it may still be deploying...")
        return False
    
    def create_api_gateway_proxy(self):
        """Create API Gateway to proxy requests to AgentCore"""
        
        print("🌐 Creating API Gateway for AgentCore proxy...")
        
        # This would create an API Gateway that proxies to AgentCore
        # For now, we'll just print the configuration needed
        
        print("""
📋 API Gateway Configuration Needed:

1. Create REST API in API Gateway
2. Create resource: /chat
3. Create POST method with Lambda proxy integration
4. Lambda function should:
   - Accept chat messages from frontend
   - Call AgentCore runtime
   - Return formatted response
   
5. Enable CORS for your CloudFront domain
6. Deploy API to stage (e.g., 'prod')

AgentCore Runtime ARN:
arn:aws:bedrock-agentcore:us-east-1:681007183786:runtime/mental_health_support_agent-lRczXz8e6I
""")
    
    def deploy(self):
        """Main deployment function"""
        
        print("🏥 Mental Health Chatbot UI - S3 + CloudFront Deployment")
        print("=" * 65)
        
        try:
            # Step 1: Create S3 bucket
            bucket_name = self.create_s3_bucket()
            if not bucket_name:
                return None
            
            # Step 2: Create OAI
            oai_id = self.create_oai()
            if not oai_id:
                return None
            
            # Step 3: Set bucket policy
            self.set_bucket_policy(oai_id)
            
            # Step 4: Upload files
            self.upload_website_files()
            
            # Step 5: Create CloudFront distribution
            distribution = self.create_cloudfront_distribution(oai_id)
            if not distribution:
                return None
            
            # Step 6: Wait for deployment (optional)
            # self.wait_for_distribution(distribution['id'])
            
            # Step 7: API Gateway info
            self.create_api_gateway_proxy()
            
            print("\n🎉 Deployment completed successfully!")
            print(f"S3 Bucket: {bucket_name}")
            print(f"CloudFront Distribution ID: {distribution['id']}")
            print(f"Website URL: https://{distribution['domain']}")
            
            print("\n📋 Next Steps:")
            print("1. Wait 10-15 minutes for CloudFront to deploy")
            print("2. Set up API Gateway to proxy AgentCore requests")
            print("3. Update script.js with your API Gateway endpoint")
            print("4. Test the chatbot interface")
            
            return {
                'bucket': bucket_name,
                'distribution_id': distribution['id'],
                'domain': distribution['domain'],
                'url': f"https://{distribution['domain']}"
            }
            
        except Exception as e:
            print(f"❌ Deployment failed: {str(e)}")
            return None


def main():
    """Main function"""
    deployer = WebsiteDeployer()
    result = deployer.deploy()
    
    if result:
        print(f"\n✅ Deployment successful!")
        print(f"Website URL: {result['url']}")
    else:
        print("\n❌ Deployment failed. Check the logs above.")


if __name__ == "__main__":
    main()
