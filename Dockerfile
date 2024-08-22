FROM python:3.11-slim

WORKDIR /app

COPY pyproject.toml poetry.lock /app/

RUN pip install poetry

RUN poetry install --no-root --no-dev

COPY . /app

EXPOSE 8000

CMD ["poetry", "run", "uvicorn", "coralsnake.main:app", "--host", "0.0.0.0", "--port", "8000"]
