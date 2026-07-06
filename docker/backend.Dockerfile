FROM python:3.12-slim

WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app/backend

COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install --no-cache-dir -r /app/backend/requirements.txt

COPY backend /app/backend
COPY scenarios /app/scenarios
COPY evidence /app/evidence

EXPOSE 8000
CMD ["uvicorn", "ptis_api:app", "--host", "0.0.0.0", "--port", "8000", "--app-dir", "/app/backend"]
