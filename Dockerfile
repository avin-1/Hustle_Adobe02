# Use a slim Python base image
FROM --platform=linux/amd64 python:3.9-slim

# Set the working directory inside the container
WORKDIR /app

# Copy dependency list and install them
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all your project files into the container
# This includes the 'src' directory, and the 'model' directory with the downloaded model.
COPY src/ ./src/
COPY model/ ./model/

# The command to run your solution.
# It processes all PDFs from /app/input and writes to /app/output
# The judging environment will mount the input/output directories.
CMD ["python", "src/main.py"]