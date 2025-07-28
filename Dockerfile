# Use a slim, specific Python base image for reproducibility
FROM --platform=linux/amd64 python:3.9-slim

# Set working directory
WORKDIR /app

# Copy requirements first (for Docker caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy model and source code
COPY src/ ./src/
COPY download_model.py .

# Run download_model.py before starting the main app
RUN python download_model.py

# Final command to run your main app
CMD ["python", "src/main.py"]
