# Base image
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Copy requirements
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy simulator code
COPY . .

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV ORION_URL=http://orion-ld:1026/ngsi-ld/v1/
ENV UPDATE_INTERVAL=10

# Run simulator
CMD ["python", "simulator.py"]