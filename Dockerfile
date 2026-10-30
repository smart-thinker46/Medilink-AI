FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
ENV MEDILINK_AUDIT_DB=/app/data/audit.db
CMD ["uvicorn", "medilink_ai.app:create_app", "--factory", "--host", "0.0.0.0", "--port", "8088"]
