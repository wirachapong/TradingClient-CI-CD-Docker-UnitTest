# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set the working directory
WORKDIR /app

# Set the PYTHONPATH
ENV PYTHONPATH=/app

# Copy the requirements file and install dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt


# Copy the rest of the application code
COPY . .

# Set up environment variables for the .env file
COPY .env .env

# Run the tests when the container starts
CMD ["pytest", "tests"]