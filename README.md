# Formula E Driver Performance Dashboard

![Formula E Dashboard](https://raw.githubusercontent.com/ASHWINPPILLAI/formula-e-dashboard/main/static/img/hero.jpg)

> A 10/10 Enterprise-grade, 3D interactive telemetry analyzer for Formula E pit-walls.

🟢 **Live Demo:** [View the Dashboard on Vercel](https://formula-e-dashboard-git-main-ashwin-p-pillais-projects.vercel.app/dashboard)

## Features
- **Obsidian & Crimson Bento Grid UI**: High-end glassmorphism design with procedural noise textures.
- **Client-Side GPU Rendering**: Highly interactive Chart.js visualizations that offload server CPU.
- **Cinematic 3D Environment**: A Three.js "Digital Twin" featuring fiber-optic laser tracks, pulsing energy data nodes, and slow-orbit drone cameras.
- **Real-Time Websockets**: Instant telemetry updates synced directly to the holographic environment.
- **Serverless Ready**: Built with FastAPI and perfectly configured for Vercel deployment.

## Tech Stack
- **Backend:** Python, FastAPI, SQLite
- **Frontend:** Vanilla JS, Three.js, Chart.js, HTML5/CSS3
- **Deployment:** Vercel (Serverless Python Runtime)

## Local Development
```bash
# Clone the repository
git clone https://github.com/ASHWINPPILLAI/formula-e-dashboard.git
cd formula-e-dashboard

# Create a virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows use: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the server locally
uvicorn main:app --reload --port 8080
```
*Navigate to `http://localhost:8080` in your browser.*
