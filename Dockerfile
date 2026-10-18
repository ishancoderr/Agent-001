# Agent-1 — FastAPI on :8000. In the repository that holds the evaluator
# (evaluator/, Agent-001), the workbench's Evaluation tab also starts it inside
# this container (python -m evaluator, :8002).
# Built and run by docker-compose.yml in the kqml-deploy folder; settings and
# secrets come from that folder's .env, never from this image.
FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# git: requirements.txt installs kqml-messaging from GitHub.
RUN apt-get update \
    && apt-get install -y --no-install-recommends git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

# Run as an ordinary user. /app/var holds what must survive a rebuild (the
# login accounts, USERS_FILE); evaluator/data the evaluation results — both
# are volumes in docker-compose.yml.
RUN useradd --create-home --uid 1000 agent \
    && mkdir -p /app/var \
    && if [ -d evaluator ]; then mkdir -p evaluator/data; fi \
    && chown -R agent /app
USER agent

EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=4)"

CMD ["uvicorn", "agent1.main:app", "--host", "0.0.0.0", "--port", "8000", \
     "--proxy-headers", "--forwarded-allow-ips", "*"]
