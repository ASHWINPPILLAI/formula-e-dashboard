# ── Builder stage ──────────────────────────────────────────────────────────
FROM python:3.11-slim AS builder

WORKDIR /build

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ── Runtime stage ─────────────────────────────────────────────────────────
FROM python:3.11-slim AS runtime

# Non-root user
RUN groupadd -r appuser && useradd -r -g appuser -s /sbin/nologin appuser

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /install /usr/local

# Copy application code and templates
COPY main.py models.py ./
COPY templates/ templates/
COPY static/ static/

# Switch to non-root
USER appuser

# Port configuration (Cloud Run sets PORT; default to 8080)
ENV PORT=8080
EXPOSE ${PORT}

CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT}"]
