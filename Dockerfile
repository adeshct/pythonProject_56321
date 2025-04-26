# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED True  # Ensures logs are sent straight to Cloud Logging
ENV APP_HOME /app
WORKDIR $APP_HOME

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy local code to the container image
COPY . .

# Specify the command to run on container start
# Replace main:app with your module:app instance
# The PORT environment variable is automatically set by Cloud Run.
CMD ["gunicorn", "--bind", "0.0.0.0:$PORT", "main:app"]
