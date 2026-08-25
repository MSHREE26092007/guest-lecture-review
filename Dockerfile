FROM python:3.12-slim
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
# uploads dir
RUN mkdir -p uploads app/uploads
EXPOSE 8000 8501
# Start both: FastAPI on 8000, Streamlit on 8501 (API_BASE_URL must point to public backend URL - set via env)
CMD sh -c "uvicorn app.api.main:app --host 0.0.0.0 --port 8000 & streamlit run app/ui/app.py --server.port 8501 --server.address 0.0.0.0 --server.headless true"
