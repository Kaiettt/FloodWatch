# Copyright (c) 2025 FloodWatch Team
# SPDX-License-Identifier: MIT

FROM python:3.10-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the subscription script
COPY subscription_main.py .

# Command to run the script
CMD ["python", "subscription_main.py"]
