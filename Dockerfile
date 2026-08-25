FROM python:3.12-slim
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
# uploads dir
RUN mkdir -p uploads app/uploads
EXPOSE 8000 8501
# HF Spaces expects 7860, Render/Railway use $PORT. Single container: UI calls API via 127.0.0.1:8000 (server-side), so no public API URL needed.
CMD sh -c "uvicorn app.api.main:app --host 0.0.0.0 --port 8000 & streamlit run app/ui/app.py --server.port ${PORT:-8501} --server.address 0.0.0.0 --server.headless true"
