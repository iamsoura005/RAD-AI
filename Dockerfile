FROM python:3.10

WORKDIR /app

COPY backend/ ./backend/
COPY model_files/ ./model_files/

RUN pip install --no-cache-dir -r backend/requirements.txt

ENV MODEL_ROOT=/app

EXPOSE 7860

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "7860", "--app-dir", "backend"]
