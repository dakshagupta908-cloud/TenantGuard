# TenantGuard

TenantGuard is an educational, full-stack legal-information application for tenants. It uses retrieval-augmented generation (RAG) to search a sample housing-law corpus, show supporting excerpts, highlight superseded provisions, and draft editable repair demand letters.

> **Important:** TenantGuard is not a law firm and does not provide legal advice. Its sample content may be incomplete or out of date. Verify the law with official sources and consult a qualified legal professional before acting.

## Features

- Tenant accounts, authentication, and per-user complaint isolation.
- Jurisdiction-filtered retrieval over indexed housing-law excerpts.
- Citation-ID validation after generation; unverified citations are removed, and answers without valid citations abstain.
- Superseded-source warnings and exclusion of inactive provisions from demand-letter citations.
- Editable repair demand letters and text export.
- Optional email (SMTP) and SMS (Twilio) notice delivery, with explicit confirmation.
- Admin-only ingestion of shared statutory sources.
- Offline mock AI provider for local development, with an optional OpenAI-compatible provider.
- SQLite for local development and PostgreSQL 16 for Docker Compose.

The included corpus is sample data for New York City, California, and Bengaluru. It is not a complete or authoritative legal database.

## Requirements

For local development:

- Python 3.11
- Node.js 20+ and npm

For Docker:

- Docker Desktop or Docker Engine with Docker Compose

## Run locally

### 1. Configure the environment

From the project root, copy `.env.example` to `.env`. On Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

The default configuration uses SQLite and the offline `mock` AI provider. No API key is required. Review `SECRET_KEY` before deploying anywhere other than local development.

The account registered with the email in `ADMIN_EMAIL` receives administrator access to source-ingestion endpoints. The default is `admin@example.com`.

### 2. Start the backend

From the project root, in a PowerShell terminal:

```powershell
cd backend
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

If PowerShell prevents virtual-environment activation, use `.\.venv\Scripts\python.exe -m pip install -r requirements.txt` and `.\.venv\Scripts\uvicorn.exe app.main:app --reload --port 8000`.

On startup, the backend creates the database and seeds the sample corpus.

### 3. Start the frontend

In a second terminal, from the project root:

```powershell
cd frontend
npm install
npm run dev
```

Open the URL printed by Vite (normally http://localhost:5173). If that port is already in use, Vite selects another available port.

The API is available at http://localhost:8000, its readiness endpoint is http://localhost:8000/api/v1/ready, and FastAPI's interactive API documentation is at http://localhost:8000/docs.

## Run with Docker Compose

From the project root:

```powershell
docker compose up --build
```

Compose starts PostgreSQL, the backend, and the frontend:

| Service | URL |
| --- | --- |
| Frontend | http://localhost:5173 |
| Backend readiness | http://localhost:8000/api/v1/ready |
| PostgreSQL | localhost:5432 |

The compose defaults are intended for local development only. Replace development secrets and database credentials before any deployment.

## Configuration

All supported settings are documented in `.env.example`. The most commonly used options are:

| Variable | Purpose | Default |
| --- | --- | --- |
| `APP_ENV` | Application environment | `development` |
| `SECRET_KEY` | JWT signing key | Development placeholder |
| `ADMIN_EMAIL` | Email granted administrator access at registration | `admin@example.com` |
| `DATABASE_URL` | SQLAlchemy database connection | `sqlite:///./tenantguard.db` |
| `AI_PROVIDER` | `mock` or `openai_compatible` | `mock` |
| `OPENAI_API_BASE` | OpenAI-compatible API base URL | `https://api.openai.com/v1` |
| `OPENAI_API_KEY` | Provider key (keep private) | Empty |
| `VITE_API_BASE_URL` | Frontend API base URL | `http://localhost:8000/api/v1` |

For email delivery, configure `SMTP_HOST`, `SMTP_PORT`, `SMTP_USERNAME`, `SMTP_PASSWORD`, `SMTP_FROM_EMAIL`, and `SMTP_USE_TLS`. For SMS, configure `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, and `TWILIO_FROM_NUMBER`. Keep credentials in an untracked `.env` file and never publish them.

## Tests and build

Backend tests, from the `backend` directory with the virtual environment active:

```powershell
pytest -v
```

Frontend TypeScript check and production build, from the `frontend` directory:

```powershell
npm run build
```

## Project layout

```text
backend/    FastAPI application, SQLAlchemy models, RAG services, and tests
frontend/   React + TypeScript web application
docs/       Architecture and security documentation
```

## Security

Do not commit `.env`, provider credentials, production secrets, database files, virtual environments, or dependency build output. The repository's `.gitignore` excludes these local files. See [docs/SECURITY.md](docs/SECURITY.md) for additional security notes.

## License

This project is distributed under the MIT License. See [LICENSE](LICENSE).
