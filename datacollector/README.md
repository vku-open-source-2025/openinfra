# OpenInfra GISTool

A tool to collect, contribute and visualize infrastructure data on a map.

## Tech Stack

- **Backend:** FastAPI (Python)
- **Frontend:** React (Vite)
- **Database:** PostgreSQL + PostGIS
- **Map:** Leaflet.js

## Setup

### 1. Start the Database

Make sure you have Docker and Docker Compose installed and running. Then, start the PostGIS database service from the root of the project:

```bash
docker-compose up -d
```
This will start a PostgreSQL database with the PostGIS extension on port 5432.

### 2. Backend Setup

Navigate to the `backend` directory and set up the Python environment.

```bash
cd backend

# Create a virtual environment
python -m venv venv

# Activate the virtual environment
# On Windows
venv\\Scripts\\activate
# On macOS/Linux
source venv/bin/activate

# Install the required packages
pip install -r requirements.txt

# Start the FastAPI server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```
The backend API will be running at `http://127.0.0.1:8000`.

### 3. Frontend Setup

Open a new terminal, navigate to the `frontend` directory, and set up the React application.

```bash
cd frontend

# Install dependencies
npm install

# Start the development server
npm run dev
```
The frontend application will be running at `http://127.0.0.1:3000` or `http://localhost:3000`. Open this URL in your browser to use the tool.
