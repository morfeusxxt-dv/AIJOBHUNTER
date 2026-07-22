# AI Job Hunter

AI Job Hunter is a commercial-grade, autonomic job crawling, filtering, and applying assistant. 
It follows **Clean Architecture** patterns strictly and uses **Playwright** to execute automated LinkedIn applications, matching profiles with high compatibility criteria.

## Core Features

- **Decoupled Architecture**: Fully decoupled controller, service, repository, and provider layers following SOLID principles.
- **Provider Plugin System**: Contract interfaces defined in `AuthenticationProvider`, `JobProvider`, `ApplyProvider`, and `ResumeProvider` allow extending the application to Gupy, Greenhouse, Lever, etc., without modifications to the core logic.
- **Autonomic Crawling**: Periodically scrapes jobs based on target keywords and locations.
- **Secure Authentication**: Playwright logs in securely and serializes cookies symmetrically using cryptography (Fernet) in PostgreSQL to avoid repetitive log-ins.
- **Asynchronous Analysis Webhook**: Automatically notifies an `n8n` workflow containing job data, waiting for suitability score, custom resume, and cover letters.
- **Human-like Applier**: Submits applications with random human intervals (30-180 seconds, larger breaks every 5 applications) and enforces a limit of 15 applications/day.
- **Live Premium Panel**: Interactive glassmorphic React dashboard, queue monitor, settings manager, and logs console.

---

## Directory Structure

```text
├── docker-compose.yml         # Container Orchestration
├── README.md                  # Documentation
├── .env.example               # Configuration template
├── backend/
│   ├── Dockerfile
│   ├── pyproject.toml
│   └── app/
│       ├── main.py            # FastAPI Entrypoint
│       ├── core/              # Config, Logger, Encryption, Providers Interfaces
│       ├── models/            # SQLAlchemy Database Models
│       ├── repositories/      # Repository Pattern Implementation
│       ├── schemas/           # Pydantic Schemas
│       ├── services/          # Decoupled Business Logic
│       ├── linkedin/          # LinkedIn Playwright crawler & applier
│       ├── routers/           # FastAPI Controllers
│       ├── scheduler/         # APScheduler background automation tasks
│       └── tests/             # Pytest Unit & Integration testing suite
└── frontend/
    ├── Dockerfile
    ├── index.html
    ├── package.json
    └── src/                   # React dashboard, settings editor, terminal logs
```

---

## How to Run

1. Clone or navigate to the workspace.
2. Build and launch all services with Docker Compose:
   ```bash
   docker compose up --build -d
   ```
3. Open the Premium Dashboard in your browser:
   `http://localhost:3000`
4. Inspect active FastAPI Swagger documentation:
   `http://localhost:8000/docs`
