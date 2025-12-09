# Copyright (c) 2025 FloodWatch Team
# SPDX-License-Identifier: MIT

FROM python:3.9-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Set environment variables with default values
ENV ORION_HOST=orion-ld
ENV WEATHER_ENTITY_ID=urn:ngsi-ld:WeatherObserved:HoChiMinh_District1
ENV FLOOD_ENTITY_ID=urn:ngsi-ld:FloodRiskRain:HoChiMinh_District1
ENV WEATHER_LON=106.70098
ENV WEATHER_LAT=10.77653

# Run the simulator
CMD ["python", "simulator.py", "--loop", "300"]
