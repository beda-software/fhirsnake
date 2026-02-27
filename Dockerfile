FROM python:3.11-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends jq \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY pyproject.toml poetry.lock /app/

RUN pip install poetry

RUN poetry install --no-root --without dev

COPY fhirsnake /app
COPY entrypoint.sh /app

EXPOSE 8000

ENTRYPOINT ["/app/entrypoint.sh"]

CMD ["server"]
