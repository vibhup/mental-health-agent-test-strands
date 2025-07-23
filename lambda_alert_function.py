import json
import boto3
from datetime import datetime

def lambda_handler(event, context):
    """
    Lambda function to send email alerts for mental health crises
    """
    
    ses = boto3.client('ses')
    
    try:
        # Extract information from the event
        user_message = event.get('user_message', '')
        risk_level = event.get('risk_level', 'UNKNOWN')
        risk_indicators = event.get('risk_indicators', [])
        
        # Prepare email content
        subject = f"MENTAL HEALTH ALERT - Risk Level: {risk_level}"
        
        body = f"""
MENTAL HEALTH SUPPORT AGENT ALERT

Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}
Risk Level: {risk_level}

RISK INDICATORS DETECTED:
{', '.join(risk_indicators) if risk_indicators else 'None specified'}

USER MESSAGE:
{user_message}

RECOMMENDED ACTIONS:
- Review full conversation for context
- Consider immediate outreach if high risk
- Provide appropriate mental health resources
- Document incident per protocol

This is an automated alert from the Mental Health Support Agent system.
"""

        # Send email via SES
        response = ses.send_email(
            Source='noreply@example.com',  # Replace with verified SES email
            Destination={'ToAddresses': ['admin.alerts.mh@example.com']},
            Message={
                'Subject': {'Data': subject},
                'Body': {'Text': {'Data': body}}
            }
        )
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Alert sent successfully',
                'messageId': response['MessageId']
            })
        }
        
    except Exception as e:
        print(f"Error sending alert: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e)
            })
        }
