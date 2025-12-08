
FROM python:3.11-slim

WORKDIR /app

RUN pip install --no-cache-dir requests prometheus-client

COPY exporter.py .

CMD ["python", "-u", "exporter.py"]
