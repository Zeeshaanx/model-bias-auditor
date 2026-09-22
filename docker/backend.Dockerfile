FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /srv

COPY backend/pyproject.toml /srv/pyproject.toml
COPY backend/app /srv/app
# scripts/ ships too, so calibration can be run inside the container:
#   docker compose exec backend python scripts/calibrate.py
COPY backend/scripts /srv/scripts

RUN pip install --no-cache-dir --upgrade pip && pip install --no-cache-dir .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
