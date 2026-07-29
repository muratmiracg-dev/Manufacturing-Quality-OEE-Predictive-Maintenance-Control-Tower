FROM python:3.12.13-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    MODEL_BUNDLE_PATH=/app/artifacts/model/champion_bundle.joblib

WORKDIR /app

RUN groupadd --gid 10001 appgroup \
    && useradd --uid 10001 --gid appgroup --no-create-home --shell /usr/sbin/nologin appuser

COPY pyproject.toml README.md ./
COPY src ./src
COPY artifacts/model ./artifacts/model

RUN python -m pip install --upgrade pip \
    && python -m pip install .

USER 10001:10001

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=3s --start-period=20s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=2)"

CMD ["uvicorn", "manufacturing_ct.api:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]

