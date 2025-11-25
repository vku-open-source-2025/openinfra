# Infrastructure Management System - Walkthrough

This document provides instructions on how to set up, run, and verify the Infrastructure Management System.

## Prerequisites
- Docker & Docker Compose
- Python 3.10+ (for local development)
- Node.js 18+ (for local development)

## Quick Start (Docker)

1. **Navigate to the infra directory:**
   ```bash
   cd infra
   ```

2. **Start the services:**
   ```bash
   docker-compose up --build
   ```
   This will start:
   - MongoDB (port 27017)
   - Backend API (port 8000)
   - Frontend (port 5173)
   - Nginx (port 80)

3. **Seed the data:**
   Open a new terminal and run:
   ```bash
   cd infra
   python3 seed_data.py
   ```
   This will upload the `sample_data.csv` to the backend, which will parse and store it in MongoDB.

4. **Access the application:**
   - **Frontend:** [http://localhost](http://localhost) (via Nginx) or [http://localhost:5173](http://localhost:5173) (direct)
   - **Backend API Docs:** [http://localhost/docs](http://localhost/docs) or [http://localhost:8000/docs](http://localhost:8000/docs)

## Features

### Dashboard
- **Map View:** Displays infrastructure assets (Power Stations, Charging Stations, etc.) on an interactive map.
- **Asset List:** Shows a table of assets. Click on a row to view details and locate it on the map.
- **Maintenance History:** Select an asset to view its maintenance logs.

### API Endpoints
- `GET /api/assets/`: List assets with filtering.
- `POST /api/assets/`: Create a new asset.
- `POST /api/ingest/csv`: Upload CSV data.
- `POST /api/maintenance/`: Create a maintenance log.
- `GET /api/maintenance/asset/{id}`: Get logs for an asset.

## Development

### Backend
1. Navigate to `backend/`.
2. Create a virtual environment and install dependencies:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```
3. Run the server:
   ```bash
   uvicorn app.main:app --reload
   ```

### Frontend
1. Navigate to `frontend/`.
2. Install dependencies:
   ```bash
   npm install
   ```
3. Run the dev server:
   ```bash
   npm run dev
   ```

## Verification Results
- **Backend Structure:** Verified FastAPI setup with Routers, Models, and Services.
- **Frontend Structure:** Verified React + Vite setup with Leaflet map and Tailwind CSS.
- **Data Ingestion:** Implemented CSV parsing with WKT geometry support.
- **Docker:** Created Dockerfiles and Compose configuration.
