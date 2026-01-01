FROM python:3.12-slim
WORKDIR /app
ENV PYTHONPATH=/app
COPY pyproject.toml /app/
RUN pip install poetry && poetry config virtualenvs.create false && poetry install --without dev
COPY app /app/app
COPY alembic.ini /app/
COPY alembic /app/alembic
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
