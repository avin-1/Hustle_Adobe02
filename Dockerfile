# Use a slim, specific Python base image for reproducibility
FROM --platform=linux/amd64 python:3.9-slim

# Set the working directory inside the container
WORKDIR /app

# Copy the requirements file first to leverage Docker layer caching
# This step is only re-run if requirements.txt changes
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the pre-downloaded model into the container
# Assumes you have a 'model' folder in your project root
COPY model/ ./model/

# Copy the source code into the container
# This includes main.py and utils.py
COPY src/ ./src/

# Define the command to run the application
# This will execute /app/src/main.py
CMD ["python", "src/main.py"]