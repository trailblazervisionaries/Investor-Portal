# Investment Portal Backend Architecture

## Overview
This repository contains the FastAPI backend for the Investment Portal. The backend is designed as a layered architecture with clearly separated concerns:
- `routes/`: HTTP API endpoints
- `services/`: business logic and operations
- `models/`: SQLAlchemy ORM entities and data access methods
- `schemas/`: Pydantic request/response validation models
- `config/`: database and environment configuration
- `core/`: reusable helpers such as authentication, hashing, and utilities
- `backgroundTasks/`: Celery asynchronous task configuration and task dispatch
- `templates/`: email template tasks and notification workflows

## High-Level Architecture

### 1. Application Entry Point
- `app/main.py` is the FastAPI application entry point.
- It configures middlewares, CORS, rate limiting, static file mounting, startup hooks, and API routers.
- The application mounts `uploads/` as a static file path, making uploaded files available under `/uploads`.
- On startup it calls `create_tables()` to ensure ORM models are created in the database.

### 2. HTTP Routing
- Each domain has its own router file inside `app/routes/`.
- Example routes and prefixes registered in `app/main.py`:
  - `/api/users` -> `user_routes`
  - `/api/admin` -> `admin_routes`
  - `/api/fund-assist` -> `fund_assist_routes`
  - `/api/investor-assist` -> `investor_assist_routes`
  - `/api/investor` -> `investor_routes`
  - `/api/lead` -> `leads_routes`
  - `/api/property` -> `property_routes`
  - `/api/property-type` -> `property_type_routes`
  - `/api/loan-amortz` -> `loan_amort_routes`
  - `/api/investor-assist-assign` -> `investor_assist_assign_routes`
  - `/api/investment` -> `investor_investment_routes`
  - `/api/income` -> `income_routes`
  - `/api/expense` -> `expense_routes`
  - `/api/property-proforma` -> `property_proforma_routes`
  - `/api/file-handle` -> `file_img_routes`
  - `/api/audit-data` -> `audit_routes`

### 3. Middleware
- `app/routes/APIMiddleware` is a custom FastAPI middleware.
- It enforces JWT-based authentication for most routes.
- It skips auth for public endpoints such as login, forgot-password, static assets, docs, and health checks.
- It reads JWT tokens from `Authorization: Bearer <token>` headers or from `auth` cookies.
- It verifies tokens using `jose.jwt` and loads the user from the database.
- If verification fails, the middleware returns a JSON error response.

### 4. Database Layer
- `app/config/database.py` configures SQLAlchemy with an asynchronous Postgres engine.
- It expects the environment variable `POSTGRES_URL`.
- It converts a standard `postgresql://` URL into `postgresql+asyncpg://` for async usage.
- `Base` is the declarative base used by all ORM models.
- `get_db()` yields an async database session for FastAPI dependencies.
- `create_tables()` imports model modules and creates database tables automatically.

### 5. Models and ORM
- Models are defined with SQLAlchemy declarative classes.
- Example: `app/models/user_model.py` defines:
  - `Users`
  - `OtpModel`
  - `UploadedDocument`
- Each model contains static async helper methods for common queries like `get_by_email` and `get_by_id`.
- Models define relationships between users and related entities such as admin, investor, fund assistant, and investor assistant.

### 6. Service Layer
- `app/services/` contains business logic separated from route definitions.
- Example: `app/services/user_service.py` performs:
  - user registration checks and creation
  - login password verification
  - JWT issuance and secure auth cookie creation
  - password reset and OTP management
  - logout
- Services call model methods, core helpers, and background task dispatchers.

### 7. Schema Validation
- `app/schemas/` contains Pydantic models used for request validation.
- Schemas enforce expected input for operations like login, password reset, entity creation, and updates.
- This layer ensures clean API contracts and typed request bodies.

### 8. Security and Authentication
- `app/core/auth.py` creates and verifies JWT tokens.
- Tokens include claims such as `sub`, `user_id`, and `role`.
- Tokens are signed with `SECRET_KEY` and algorithm `HS256`.
- `app/core/hash.py` is used for password hashing and verification.
- `APIMiddleware` uses token verification to authorize protected routes.

### 9. Background Tasks
- `app/backgroundTasks/MonitorAsync.py` configures the Celery app.
- Celery uses Redis as broker and backend, configured through `REDIS_URL` or detailed Redis environment variables.
- It registers an asynchronous queue called `ip_app_queue`.
- `MonitorAsync.deferred(function, *args)` dispatches tasks by name to Celery.
- `app/backgroundTasks/celery_worker.py` starts the worker process.

### 10. Email Templates and Notifications
- `app/templates/send_template_mail.py` defines Celery tasks for email notifications.
- It sends:
  - credential emails
  - OTP codes
  - password change notifications
  - investment confirmation emails
- These tasks call `app.core.mail_service.MailService.send_mail()` via async wrappers.

### 11. Logging
- `app/logging_config.py` sets up a colored terminal logger.
- It configures `logging.StreamHandler` to emit console logs with timestamp and log level.
- The application initializes logging in `app/main.py`.

## Application Flow Chart
```mermaid
flowchart TD
    A[Client / Frontend] -->|HTTP Request| B[FastAPI app/main.py]
    B --> C[APIMiddleware]
    C -->|auth required| D{Public or Protected?}
    D -->|Public| E[Route Handler]
    D -->|Protected| F[verify JWT token]
    F -->|valid| E[Route Handler]
    F -->|invalid| G[HTTP 401 / error response]
    E --> H[Schema Validation (Pydantic)]
    H --> I[Service Layer]
    I --> J[Database Layer / SQLAlchemy AsyncSession]
    J --> K[Postgres Database]
    I --> L[BackgroundTasks MonitorAsync]
    L --> M[Celery / Redis]
    M --> N[Email / Notification Tasks]
    E --> O[JSON Response]
    O --> A
    B -->|startup| P[create_tables()]
    P --> K
```

## Runtime Flow
1. `uvicorn app.main:app --reload` starts the API.
2. FastAPI loads middleware, routers, CORS, and Celery rate-limiter.
3. Startup event triggers `create_tables()` and ensures the DB schema exists.
4. Client requests arrive via route-specific endpoints.
5. Requests pass through `APIMiddleware` for auth unless whitelisted.
6. Routes validate payloads using Pydantic schemas.
7. Routes call service methods for business logic.
8. Services interact with async DB sessions and ORM methods.
9. Asynchronous notifications may be queued using `MonitorAsync.deferred()`.
10. Celery workers process email and background tasks independently.

## Core Environment Variables
- `POSTGRES_URL` — PostgreSQL connection URL.
- `SECRET_KEY` — JWT signing secret.
- `ALGORITHM` — JWT algorithm (default `HS256`).
- `DOMAIN` — domain used when setting cookies.
- `ACCESS_TOKEN_EXPIRE_HOURS` — token lifetime in hours.
- `REDIS_URL` — Redis broker/backend URL for Celery.
- `REDIS_PROTOCOL`, `REDIS_PASSWORD`, `REDIS_HOST`, `REDIS_PORT` — alternate Redis connection settings.

## Important Notes
- The backend is asynchronous: SQLAlchemy async sessions, FastAPI async routes, and Celery tasks.
- Most API routes rely on token auth, while some routes are marked public.
- Uploaded files are served from the `uploads/` directory via FastAPI static mount.
- The codebase uses a modular structure intended to keep routing, business logic, persistence, and utilities distinct.

## Recommended Documentation Links
- `app/main.py` — application wiring and router registration
- `app/config/database.py` — DB setup and table creation
- `app/routes/APIMiddleware.py` — auth enforcement
- `app/models/user_model.py` — example ORM model and query helpers
- `app/services/user_service.py` — example business logic flow
- `app/backgroundTasks/MonitorAsync.py` — async task dispatching
- `app/templates/send_template_mail.py` — email notification tasks


