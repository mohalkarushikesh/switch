# --- Custodian API image ---
FROM python:3.13-slim

# Don't buffer stdout/stderr (logs appear immediately) and don't write .pyc files.
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app/src

WORKDIR /app

# Install dependencies first so this layer caches unless requirements change.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application source and sample data.
COPY src/ ./src/
COPY data/ ./data/

EXPOSE 8000

# Serve the FastAPI app.
CMD ["uvicorn", "custodian.api:app", "--host", "0.0.0.0", "--port", "8000"]
