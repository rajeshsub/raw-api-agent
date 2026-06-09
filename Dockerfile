FROM python:3.12-slim

# Create non-root user
RUN useradd --create-home --shell /bin/bash appuser

WORKDIR /app

# Install deps as root, then hand off
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app source
COPY app/ ./app/

# Create workspace dir owned by appuser
RUN mkdir -p /app/workspace && chown appuser:appuser /app/workspace

USER appuser

ENV AGENT_WORKSPACE=/app/workspace

EXPOSE 7860

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "7860"]
