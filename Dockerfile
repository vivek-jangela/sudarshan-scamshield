# Builds the React frontend, then runs FastAPI which serves both the API and the website.
FROM node:20-alpine AS web
WORKDIR /web
COPY frontend/package*.json ./
RUN npm install
COPY frontend/ ./
RUN npm run build

FROM python:3.12-slim
WORKDIR /app
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY backend/ .
COPY --from=web /web/dist ./static
# seed demo cases (offline), then start. Render sets $PORT; Hugging Face Spaces uses 7860.
CMD ["sh", "-c", "python scripts/seed_demo.py && uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-7860}"]
