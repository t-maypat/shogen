# Shogen: Multi-Agent Marketing Orchestration & Synthetic Evaluation Platform

![Shogen](https://img.shields.io/badge/Status-Active-brightgreen)
![React](https://img.shields.io/badge/Frontend-React%2018-blue)
![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688)
![Docker](https://img.shields.io/badge/Deployment-Docker%20Compose-2496ED)

Shogen is a comprehensive **Multi-Agent Marketing Orchestration & Synthetic Evaluation Platform** designed for planning, reviewing, approving, and adapting personalized cross-channel marketing campaigns.

It includes a complete NestWise fintech demo featuring multiple personas, various communication channels, policy-readiness review, synthetic pre-flight scoring, and an adaptive recommendation loop.

## Features

## Key Features

- **Human-in-the-Loop Briefing:** Marketers outline strict guardrails—such as brand voice, mandatory claims, and "danger zones"—prior to the generation phase.
- **Agentic Cross-Channel Generation:** Specialized AI agents produce tailored, tone-adjusted copy across multiple channels (Google Search, LinkedIn, Email, SMS) based on synthetic personas.
- **Automated Policy Review:** A dual-layer process ensures compliance through deterministic checks (character limits, mandatory links) alongside a semantic AI review featuring revision trails.
- **AI-Powered Pre-Flight Evaluation:** Leveraging LangGraph and OpenAI, the platform tests creative variants against KPIs and suggests campaign reallocations based on synthetic intent signals before any budget is spent.
- **Interactive Campaign Workspace:** A dynamic, visual interface built with React, Vite, Recharts, and React Flow for seamlessly designing and managing complex campaigns.

---

## Project Architecture

This is a full-stack application divided into a modern React frontend and a robust Python FastAPI backend.

```
shogen/
├── frontend/             # React 18, Vite, TailwindCSS 4, React Router
├── backend/              # FastAPI, Python 3.11+, LangGraph, SQLAlchemy, Alembic
├── docker-compose.yml    # Container orchestration for Backend & Postgres
└── .env.example          # Template for environment variables
```

---

## Getting Started

### Prerequisites

To run the project locally, ensure you have the following installed:

- [Node.js](https://nodejs.org/) (v18+ recommended)
- [Python](https://www.python.org/) 3.11+
- [uv](https://github.com/astral-sh/uv) (Extremely fast Python package installer)
- [Docker & Docker Compose](https://www.docker.com/) (For database and containerized backend)

### 1. Environment Setup

Copy the environment template and configure your local settings:

```bash
# In the root directory
cp .env.example .env
```

_Note: The default `.env.example` is configured to work out-of-the-box for local development. By default, it uses a `fake` model provider, but you can add your Azure OpenAI credentials to enable real AI workflows._

---

### 2. Running the Application

You can run the application in a few different ways depending on your needs.

#### Option A: Full Stack via Docker + Local Frontend (Recommended)

1. **Start the backend and database:**

   ```bash
   # In the root directory
   docker-compose up -d
   ```

   This will spin up the PostgreSQL database and the FastAPI backend on port `8000`.

2. **Start the frontend:**
   ```bash
   cd frontend
   npm install
   npm run dev
   ```
   The frontend will be available at `http://localhost:5173`.

#### Option B: Local Backend Development

If you want to actively develop the backend without Docker (though you'll still need the Postgres DB):

1. **Start the database only:**

   ```bash
   docker-compose up -d postgres
   ```

2. **Run the backend locally:**
   ```bash
   cd backend
   # uv will automatically manage your virtual environment and dependencies
   uv run fastapi dev app/main.py
   ```
   The backend API docs will be available at `http://localhost:8000/docs`.

#### Option C: Frontend Only (Mock Mode)

The frontend can be run entirely independently using a local replay experience.

```bash
cd frontend
npm install
npm run dev
```

---

## Technology Stack

### Frontend

- **Framework**: React 18 & Vite
- **Styling**: Tailwind CSS v4
- **Routing**: React Router
- **Data Visualization**: Recharts, React Flow (`@xyflow/react`)
- **Icons**: Lucide React

### Backend

- **Framework**: FastAPI (Python 3.11+)
- **Database**: PostgreSQL & SQLAlchemy (psycopg)
- **Migrations**: Alembic
- **AI & Workflows**: LangGraph, OpenAI
- **Tooling**: `uv` for dependency management

---
