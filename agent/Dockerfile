FROM python:3.12-slim

LABEL org.opencontainers.image.title="KubeWise Agent"
LABEL org.opencontainers.image.description="KubeWise read-only Kubernetes cluster collector"

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY collector.py .

RUN addgroup --system kubewise && adduser --system --ingroup kubewise kubewise \
    && mkdir -p /home/kubewise/.kube \
    && chown -R kubewise:kubewise /home/kubewise
USER kubewise

ENV BACKEND_URL=http://kubewise-api:8000
ENV CLUSTER_NAME=my-cluster
ENV POLL_INTERVAL_SECONDS=300
ENV IN_CLUSTER=true

CMD ["python", "collector.py"]
