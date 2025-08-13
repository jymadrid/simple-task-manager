# Simple Dockerfile for TaskForge
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY pyproject.toml README.md ./
COPY taskforge/ taskforge/

# Create version file
RUN echo '__version__ = "1.0.0"' > taskforge/_version.py

# Install Python dependencies
RUN pip install --upgrade pip && \
    pip install -e ".[dev]"

# Create non-root user
RUN useradd -m -u 1000 taskforge && \
    chown -R taskforge:taskforge /app

USER taskforge

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Expose port
EXPOSE 8000

# Run the application
CMD ["python", "-m", "uvicorn", "taskforge.api.main:app", "--host", "0.0.0.0", "--port", "8000"]