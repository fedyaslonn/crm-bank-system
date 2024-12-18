FROM python:3.10-slim

WORKDIR /app

RUN pip install poetry

COPY pyproject.toml poetry.lock ./

RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi

COPY . .

ENV PYTHONPATH=/app/crm_bank_system

CMD ["python", "crm_bank_system/manage.py", "runserver", "0.0.0.0:8000"]