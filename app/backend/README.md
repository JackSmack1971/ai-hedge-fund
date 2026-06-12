# AI Hedge Fund - Backend
This backend serves the web application and CLI workflows in this repository. It exposes REST and SSE endpoints for flows, runs, API-key storage, Ollama status, and the hedge-fund execution pipeline.

## Overview

This backend project is a FastAPI application that serves as the server-side component of the AI Hedge Fund system. It exposes endpoints for running the hedge fund trading system and backtester.

This backend is paired with the React/Vite frontend in `app/frontend/`.

## Installation

### Using Poetry

1. Clone the repository:
```bash
git clone https://github.com/JackSmack1971/ai-hedge-fund-forked.git
cd ai-hedge-fund-forked
```

2. Install Poetry (if not already installed):
```bash
curl -sSL https://install.python-poetry.org | python3 -
```

3. Install dependencies:
```bash
# From the root directory
poetry install
```

4. Set up your environment variables:
```bash
# Create .env file for your API keys (in the root directory)
cp .env.example .env
```

5. Edit the .env file to add your API keys:
```bash
# For running LLMs hosted by openai (gpt-4o, gpt-4o-mini, etc.)
OPENAI_API_KEY=your-openai-api-key

# For running LLMs hosted by groq (deepseek, llama3, etc.)
GROQ_API_KEY=your-groq-api-key

# For getting financial data to power the hedge fund
FINANCIAL_DATASETS_API_KEY=your-financial-datasets-api-key
```

## Running the Server

To run the development server:

```bash
# Navigate to the backend directory
cd app/backend

# Start the FastAPI server with uvicorn
poetry run uvicorn main:app --reload
```

This will start the FastAPI server with hot-reloading enabled.

The API will be available at:
- API Endpoint: http://localhost:8000
- API Documentation: http://localhost:8000/docs

## Database Schema

Schema changes are managed by Alembic migrations in `app/backend/alembic/`.
Run `alembic upgrade head` before starting a deployment so the database schema matches the code.
The FastAPI lifespan only runs `Base.metadata.create_all()` when `AUTO_CREATE_TABLES=true`, which is intended for local/dev bootstrap only.

## API Endpoints

- `POST /hedge-fund/run`: Run the hedge-fund workflow
- `GET /ping`: SSE ping stream used for connectivity checks

## Project Structure

```
app/backend/
├── database/                 # Engine, Base, and ORM models
├── models/                   # Pydantic schema and event models
├── repositories/             # Database access helpers
├── routes/                   # FastAPI routers
├── services/                 # Business logic and orchestration
├── tasks/                    # Celery app and async task wiring
└── main.py                   # FastAPI application entry point
```

## Disclaimer

This project is for **educational and research purposes only**.

- Not intended for real trading or investment
- No warranties or guarantees provided
- Creator assumes no liability for financial losses
- Consult a financial advisor for investment decisions

By using this software, you agree to use it solely for learning purposes.
