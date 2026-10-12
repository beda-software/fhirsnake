FROM python:3.11-slim AS base

RUN apt-get update \
    && apt-get upgrade -y \
    && apt-get install -y --no-install-recommends jq \
    && rm -rf /var/lib/apt/lists/*

ENV VIRTUAL_ENV=/opt/venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

FROM base AS build

ENV POETRY_VIRTUALENVS_CREATE=false

RUN pip install poetry \
    && python -m venv $VIRTUAL_ENV

WORKDIR /app

COPY pyproject.toml poetry.lock ./

RUN poetry install --only main --no-root \
    && pip uninstall -y pip setuptools

FROM base AS runtime

RUN pip uninstall -y pip setuptools

COPY --from=build --chown=root:root $VIRTUAL_ENV $VIRTUAL_ENV

WORKDIR /app

COPY fhirsnake /app
COPY entrypoint.sh /app

EXPOSE 8000

ENTRYPOINT ["/app/entrypoint.sh"]

CMD ["server"]
