FROM python:3.14-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 MPLBACKEND=Agg MPLCONFIGDIR=/tmp/matplotlib
WORKDIR /app
COPY pyproject.toml requirements-lock.txt ./
COPY src ./src
COPY config ./config
RUN python -m pip install --no-cache-dir -c requirements-lock.txt ".[gcp]" \
    && useradd --create-home --uid 10001 demo
USER demo
ENTRYPOINT ["python", "-m", "finance_tracker.pipeline"]
CMD ["--cloud", "--input-dir", "/tmp/finance-input", "--output-dir", "/tmp/finance-output", "--config", "/app/config/demo.json"]