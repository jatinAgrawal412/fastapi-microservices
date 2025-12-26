FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY payment payment

CMD ["uvicorn", "payment.app.main:app", "--host", "0.0.0.0", "--port", "8001"]