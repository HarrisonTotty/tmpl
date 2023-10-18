FROM python:3.11 as poetry

ENV PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_NO_CACHE_DIR=false \
    POETRY_VIRTUALENVS_CREATE=false \
    PYTHONFAULTHANDLER=1 \
    PYTHONHASHSEED=random \
    PYTHONUNBUFFERED=1

RUN pip install poetry


FROM poetry as build

ADD . /project

WORKDIR /project

RUN poetry install \
    --no-ansi \
    --no-dev \
    --no-interaction \
    --no-root \
    && poetry build \
    --format wheel \
    && pip install dist/*.whl


FROM build as test

ENV MYPY_CACHE_DIR=/tmp/mypy-cache

RUN poetry install --no-ansi --no-interaction --no-root && \
    mypy --install-types --non-interactive && \
    pytest
