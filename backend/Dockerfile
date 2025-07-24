FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y gcc && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install boto3 python-dotenv

# Copy application code
COPY simple_mental_health_agent.py .
COPY agentcore_server.py .

# Expose port
EXPOSE 8080

# Set environment
ENV PORT=8080

# Run the HTTP server
CMD ["python", "agentcore_server.py"]
