#!/usr/bin/env python3
"""
Example usage of the Mental Health Support Agent
"""

from mental_health_agent import MentalHealthAgent

def example_conversation():
    """Example conversation demonstrating the agent's capabilities"""
    
    print("🤗 Mental Health Agent Example")
    print("=" * 40)
    
    # Initialize the agent
    agent = MentalHealthAgent()
    conversation_history = []
    
    # Example conversation scenarios
    test_messages = [
        "Hi, I've been feeling really stressed lately with work",
        "I can't seem to sleep well and I'm always anxious",
        "Sometimes I feel like nothing I do matters",
        "I've been having thoughts about hurting myself",  # This should trigger an alert
        "Thank you for listening to me"
    ]
    
    for i, message in enumerate(test_messages, 1):
        print(f"\n--- Message {i} ---")
        print(f"User: {message}")
        
        try:
            response = agent.chat(message, conversation_history)
            print(f"Agent: {response}")
            
            # Check if this was a high-risk message
            risk_analysis = agent.analyze_risk_level(" ".join(conversation_history + [message]))
            if risk_analysis["requires_alert"]:
                print(f"⚠️  ALERT TRIGGERED - Risk Level: {risk_analysis['risk_level']}")
                
        except Exception as e:
            print(f"Error: {str(e)}")
        
        print("-" * 40)

def test_risk_analysis():
    """Test the risk analysis functionality"""
    
    print("\n🔍 Risk Analysis Testing")
    print("=" * 40)
    
    agent = MentalHealthAgent()
    
    test_cases = [
        ("I'm feeling a bit sad today", "Should be low/no risk"),
        ("I can't cope with anything anymore", "Should be medium risk"),
        ("I want to kill myself", "Should be high risk"),
        ("I'm having panic attacks daily and can't function", "Should be medium risk"),
        ("Life is good, just checking in", "Should be no risk")
    ]
    
    for message, expected in test_cases:
        risk_analysis = agent.analyze_risk_level(message)
        print(f"\nMessage: '{message}'")
        print(f"Expected: {expected}")
        print(f"Result: Risk Level = {risk_analysis['risk_level']}")
        print(f"Alert Required: {risk_analysis['requires_alert']}")
        print("-" * 40)

if __name__ == "__main__":
    print("Mental Health Agent - Example Usage\n")
    
    try:
        # Run example conversation
        example_conversation()
        
        # Test risk analysis
        test_risk_analysis()
        
    except KeyboardInterrupt:
        print("\n\nExample terminated by user.")
    except Exception as e:
        print(f"\nError running example: {str(e)}")
        print("Make sure you have configured your AWS credentials and environment variables.")
