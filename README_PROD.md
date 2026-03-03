# CredenceAI: Production & Vercel Deployment Guide

This guide details how to move CredenceAI from local development to a production-grade deployment on Vercel with PostgreSQL persistence.

## 1. Database Setup (PostgreSQL)
Since Vercel is stateless, SQLite data will be lost on every deployment. We have integrated **PostgreSQL** support for permanent session storage.

1.  **Create a Postgres Instance**: Use a provider like **[Neon.tech](https://neon.tech/)**, **[Railway.app](https://railway.app/)**, or **[Vercel Postgres](https://vercel.com/storage/postgres)**.
2.  **Get the Connection String**: It should look like `postgres://user:password@host:port/dbname`.

## 2. Vercel Configuration
The project is already pre-configured for Vercel using the `vercel.json` and a root `api/index.py` shim.

### Deployment Steps:
1.  **Connect Repo**: Import your repo into Vercel.
2.  **Environment Variables**: Add these critical keys in the Vercel Dashboard:
    *   `DATABASE_URL`: Your PostgreSQL connection string.
    *   `OPENAI_API_KEY`: For the Five Cs Reasoning.
    *   `GOOGLE_API_KEY`: For Gemini document parsing.
    *   `TAVILY_API_KEY`: For the Research Agent.
3.  **Deploy**: Vercel will automatically build the Vite frontend and deploy the FastAPI backend as serverless functions.

## 3. Local Development with Postgres
If you want to test Postgres locally:
1.  Add `DATABASE_URL` to your local `.env`.
2.  Install dependencies: `pip install psycopg2-binary`.
3.  The app will automatically sense the `postgres://` prefix and switch from SQLite to the Postgres engine.

## 4. Troubleshooting
*   **Static Assets**: If images or PDFs aren't loading, ensure the `ALLOWED_ORIGINS` is set correctly or left as `*`.
*   **Cold Starts**: The first API call after a period of inactivity might take 2-3 seconds as the serverless function spins up.
*   **Storage**: In-memory storage and temporary files (`/tmp/`) are wiped after each request. Use the database for all persistence.

---
**CredenceAI** — *Bridging the Intelligence Gap in Corporate Lending.*
