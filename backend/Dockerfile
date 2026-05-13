FROM python:3.12-slim

LABEL org.opencontainers.image.title="KubeWise API"
LABEL org.opencontainers.image.description="KubeWise backend — advisory-only Kubernetes optimization platform"

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN addgroup --system kubewise && adduser --system --ingroup kubewise kubewise
RUN mkdir -p /data && chown kubewise:kubewise /data
USER kubewise

ENV DATABASE_URL=sqlite:////data/kubewise.db
ENV SEED_DEMO_DATA=true
ENV CORS_ORIGINS=http://localhost:3000

VOLUME ["/data"]

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
