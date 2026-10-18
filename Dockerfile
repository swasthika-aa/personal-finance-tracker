FROM python:3.14-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 MPLBACKEND=Agg \
    MPLCONFIGDIR=/tmp/matplotlib IPYTHONDIR=/tmp/ipython \
    JUPYTER_RUNTIME_DIR=/tmp/jupyter-runtime JUPYTER_DATA_DIR=/tmp/jupyter-data \
    JUPYTER_CONFIG_DIR=/tmp/jupyter-config
WORKDIR /app
COPY pyproject.toml requirements-lock.txt ./
COPY src ./src
COPY config ./config
COPY notebooks ./notebooks
COPY scripts ./scripts
RUN python -m pip install --no-cache-dir -c requirements-lock.txt . \
    && useradd --create-home --uid 10001 demo \
    && mkdir -p /app/data /app/outputs \
    && chown -R demo:demo /app
USER demo
EXPOSE 8888
CMD ["python", "-m", "jupyterlab", "--ip=0.0.0.0", "--port=8888", "--no-browser", "--ServerApp.root_dir=/app", "--ServerApp.default_url=/lab/tree/notebooks/finance_demo.ipynb"]