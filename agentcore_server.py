#!/usr/bin/env python3
"""
HTTP server for AgentCore Runtime
"""

import json
import os
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
from simple_mental_health_agent import SimpleMentalHealthAgent

# Initialize the agent
print("🏥 Starting Mental Health Agent Server...")
agent = SimpleMentalHealthAgent()
conversation_histories = {}
print("✅ Agent initialized")

class AgentHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            # Read request body
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            
            # Parse JSON
            event = json.loads(post_data.decode('utf-8'))
            print(f"📥 Received: {event}")
            
            # Extract data
            session_id = event.get('sessionId', 'default')
            user_input = event.get('input', '')
            
            if not user_input:
                self.send_error(400, "No input provided")
                return
            
            # Get conversation history
            if session_id not in conversation_histories:
                conversation_histories[session_id] = []
            
            # Process with agent
            response = agent.chat(user_input, conversation_histories[session_id])
            
            # Send response
            result = {
                'response': response,
                'sessionId': session_id,
                'status': 'success'
            }
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(result).encode('utf-8'))
            
            print(f"✅ Sent response: {response[:100]}...")
            
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            self.send_error(500, str(e))
    
    def do_GET(self):
        # Health check
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps({'status': 'healthy', 'agent': 'mental-health'}).encode('utf-8'))

def run_server():
    port = int(os.environ.get('PORT', 8080))
    server = HTTPServer(('0.0.0.0', port), AgentHandler)
    print(f"🚀 Server running on port {port}")
    server.serve_forever()

if __name__ == "__main__":
    run_server()
