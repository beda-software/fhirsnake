FROM python:3.11-slim

WORKDIR /app

COPY pyproject.toml poetry.lock /app/

RUN pip install poetry

RUN poetry install --no-root --no-dev

COPY fhirsnake /app

EXPOSE 8000

ENTRYPOINT ["poetry", "run", "python3", "cli.py"]

CMD ["server"]
