FROM python:3.11-slim

WORKDIR /app

RUN pip install poetry
COPY pyproject.toml poetry.lock .env ./
COPY src/ ./src/
COPY alembic/ ./alembic/
COPY alembic.ini .
RUN poetry config virtualenvs.create false && poetry install --only main --no-interaction --no-ansi

CMD ["poetry", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"] 