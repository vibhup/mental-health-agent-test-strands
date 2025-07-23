FROM public.ecr.aws/lambda/python:3.11

# Install system dependencies
RUN yum update -y && yum install -y gcc

# Copy requirements and install Python dependencies
COPY requirements.txt ${LAMBDA_TASK_ROOT}
RUN pip install -r requirements.txt

# Copy application code
COPY mental_health_agent.py ${LAMBDA_TASK_ROOT}
COPY agentcore_handler.py ${LAMBDA_TASK_ROOT}

# Set the CMD to your handler
CMD ["agentcore_handler.handler"]
