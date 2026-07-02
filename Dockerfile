# Build the React Frontend
FROM node:18 AS frontend-builder
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm install
COPY frontend/ ./
# We need to build with a relative API URL so it uses the same host
ENV VITE_API_URL=""
RUN npm run build

# Build the Python Backend
FROM python:3.11-slim
WORKDIR /app

# Install backend dependencies
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY backend/ ./backend/

# Copy built frontend from the previous stage
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist

# Expose port
EXPOSE 7860

# Set environment variables for Hugging Face compatibility
ENV PORT=7860
ENV HOST=0.0.0.0

# Start the FastAPI server (which now also serves the frontend!)
CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "7860"]
