FROM python:3.11-slim

WORKDIR /app

COPY pyproject.toml poetry.lock /app/

RUN pip install poetry

RUN poetry install --no-root --no-dev

COPY fhirsnake /app
COPY entrypoint.sh /app

EXPOSE 8000

ENTRYPOINT ["/app/entrypoint.sh"]

CMD ["server"]
