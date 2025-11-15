# FloodWatchX

A real-time flood monitoring and alert system using FIWARE Orion-LD context broker.

## Overview

FloodWatchX is a comprehensive flood monitoring solution that integrates various data sources including water level sensors, CCTV cameras, crowd reports, and weather data to provide real-time flood risk assessment and alerts.

## Quick Start

1. Clone the repository
2. Install Docker and Docker Compose
3. Run `docker-compose up -d`
4. Access the dashboard at `http://localhost:3000`

## Architecture

- **Simulation**: Mock data generators for water levels, camera streams, and weather data
- **Orion-LD**: FIWARE Context Broker for managing context information
- **Processor**: Flood risk calculation engine and alerting system
- **Dashboard**: Real-time visualization and monitoring interface

## License

MIT License - See [LICENSE](LICENSE) for details.
