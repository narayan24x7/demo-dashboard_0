FROM python:3.12-slim
WORKDIR /app
COPY requirements-deploy.txt .
RUN pip install --no-cache-dir -r requirements-deploy.txt && useradd --create-home appuser
COPY --chown=appuser:appuser . .
RUN mkdir -p /app/data && chown appuser:appuser /app/data
USER appuser
ENV FRANCHISEOPS_DB=/app/data/franchiseops.db
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/healthz', timeout=3)"
CMD ["sh", "-c", "python run.py --run-once && exec gunicorn --bind 0.0.0.0:8000 --workers 1 --threads 4 --timeout 90 wsgi:application"]
