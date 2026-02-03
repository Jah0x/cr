FROM python:3.12-slim
WORKDIR /app
ENV PYTHONPATH=/app
COPY pyproject.toml /app/
COPY poetry.lock* /app/
RUN pip install "poetry==2.2.1" && poetry config virtualenvs.create false && poetry install --without dev
COPY app /app/app
COPY alembic.ini /app/
COPY alembic /app/alembic
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--no-access-log"]
