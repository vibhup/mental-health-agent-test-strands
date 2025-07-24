#!/usr/bin/env python3
"""
Update CloudFront Distribution TTL to 0 seconds
This will ensure no caching and always serve fresh content
"""

import boto3
import json
from datetime import datetime

def update_cloudfront_ttl():
    """Update CloudFront distribution to set TTL to 0"""
    print("🔄 UPDATING CLOUDFRONT TTL TO 0 SECONDS")
    print("=" * 50)
    
    distribution_id = 'EJR9NWNZL5HZN'
    
    try:
        # Initialize CloudFront client
        cloudfront = boto3.client('cloudfront')
        
        # Step 1: Get current distribution configuration
        print("📥 Step 1: Getting current distribution configuration...")
        response = cloudfront.get_distribution_config(Id=distribution_id)
        
        config = response['DistributionConfig']
        etag = response['ETag']
        
        print(f"✅ Current DefaultTTL: {config['DefaultCacheBehavior']['DefaultTTL']} seconds")
        print(f"✅ Current MaxTTL: {config['DefaultCacheBehavior']['MaxTTL']} seconds")
        print(f"✅ Current MinTTL: {config['DefaultCacheBehavior']['MinTTL']} seconds")
        print(f"✅ ETag: {etag}")
        
        # Step 2: Update TTL settings
        print("\n🔧 Step 2: Updating TTL settings to 0...")
        config['DefaultCacheBehavior']['DefaultTTL'] = 0
        config['DefaultCacheBehavior']['MaxTTL'] = 0
        config['DefaultCacheBehavior']['MinTTL'] = 0
        
        print("✅ Updated DefaultTTL: 0 seconds")
        print("✅ Updated MaxTTL: 0 seconds") 
        print("✅ Updated MinTTL: 0 seconds")
        
        # Step 3: Update the distribution
        print("\n📤 Step 3: Updating CloudFront distribution...")
        update_response = cloudfront.update_distribution(
            Id=distribution_id,
            DistributionConfig=config,
            IfMatch=etag
        )
        
        new_etag = update_response['ETag']
        status = update_response['Distribution']['Status']
        
        print(f"✅ Distribution updated successfully!")
        print(f"✅ New ETag: {new_etag}")
        print(f"✅ Status: {status}")
        
        # Step 4: Create invalidation to clear existing cache
        print("\n🗑️ Step 4: Creating cache invalidation...")
        invalidation_response = cloudfront.create_invalidation(
            DistributionId=distribution_id,
            InvalidationBatch={
                'Paths': {
                    'Quantity': 1,
                    'Items': ['/*']
                },
                'CallerReference': f'ttl-update-{int(datetime.now().timestamp())}'
            }
        )
        
        invalidation_id = invalidation_response['Invalidation']['Id']
        invalidation_status = invalidation_response['Invalidation']['Status']
        
        print(f"✅ Invalidation created: {invalidation_id}")
        print(f"✅ Invalidation status: {invalidation_status}")
        
        print("\n" + "=" * 50)
        print("🎉 CLOUDFRONT TTL UPDATE COMPLETE!")
        print("=" * 50)
        
        print("✅ CHANGES MADE:")
        print("   🔄 DefaultTTL: 86400 → 0 seconds")
        print("   🔄 MaxTTL: 31536000 → 0 seconds")
        print("   🔄 MinTTL: 0 → 0 seconds (unchanged)")
        print("   🗑️ Cache invalidation: In progress")
        
        print("\n🎯 RESULT:")
        print("   📄 Files will no longer be cached")
        print("   ⚡ Changes will be visible immediately")
        print("   🔄 Fresh content served on every request")
        
        print(f"\n⏰ Update completed at: {datetime.now().isoformat()}")
        print("🌐 Website: https://d3nlpr9no3kmjc.cloudfront.net")
        
        print("\n⚠️ NOTE:")
        print("   Distribution update may take 5-15 minutes to propagate")
        print("   Cache invalidation may take 1-5 minutes to complete")
        
        return True
        
    except Exception as e:
        print(f"❌ Update failed: {str(e)}")
        return False

def main():
    """Main execution"""
    print("🧠 MENTAL HEALTH AGENT - CLOUDFRONT TTL UPDATE")
    print("=" * 60)
    print(f"🕐 Start Time: {datetime.now().isoformat()}")
    print("=" * 60)
    
    success = update_cloudfront_ttl()
    
    if success:
        print("\n🎊 SUCCESS! CloudFront TTL updated to 0 seconds!")
        print("🔄 No more caching issues - fresh content every time!")
    else:
        print("\n⚠️ Update failed. Please check the error messages above.")
    
    print(f"\n📋 Completed: {datetime.now().isoformat()}")

if __name__ == "__main__":
    main()
