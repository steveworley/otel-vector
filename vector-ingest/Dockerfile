FROM python

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Pre-download the model to avoid doing it at runtime start
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"

COPY main.py .
COPY agent.py .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
