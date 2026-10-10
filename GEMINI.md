# Project Rules

## General
- Python 3.11+ with type hints everywhere.
- Pydantic v2 models for all request/response schemas.
- FastAPI for the web layer.

## Charting
- Always call `matplotlib.use("Agg")` before importing `pyplot` to avoid GUI backend issues.
- Use dark themes for all charts.
- Close every matplotlib figure after saving to prevent memory leaks.

## Testing
- Use pytest with httpx.AsyncClient (or TestClient) for endpoint tests.
- Never weaken assertions to make tests pass; fix root causes instead.

## Docker
- Multi-stage builds on python:3.11-slim.
- Run as non-root user in production.
- Do not run tests inside Docker images.

## CI/CD
- Cloud Build with pytest, docker build, push, and Cloud Run deploy.
- Use $BUILD_ID for image tags (manual `gcloud builds submit`).
- Never hardcode project numbers or service account emails.
