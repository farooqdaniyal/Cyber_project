FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY rag/requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY rag/ ./rag/
COPY ml_models/ ./ml_models/

WORKDIR /app/rag
EXPOSE 8501

CMD ["streamlit", "run", "streamlit_app.py", "--server.port=8501", "--server.address=0.0.0.0"]