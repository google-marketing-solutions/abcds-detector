# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file and install dependencies
# This is done in a separate step to leverage Docker layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code into the container
COPY . .

# Expose the port the app runs on
# Cloud Run expects the container to listen on the port defined by the PORT env var, which defaults to 8080
EXPOSE 8080

# Define the command to run the application
# Use uvicorn to run the FastAPI app.
# --host 0.0.0.0 makes the server accessible from outside the container.
# --port 8080 matches the EXPOSE instruction.
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8080"]
