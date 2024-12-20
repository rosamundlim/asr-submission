# Adapted template from https://fastapi.tiangolo.com/deployment/docker/#create-the-fastapi-code

# Define base image, I used python 3.11.11 for this project
FROM python:3.11.11-slim

# Set /app as the working directory of the container
WORKDIR /app

# Send requirements.txt to container's working directory
COPY ./requirements.txt /app/requirements.txt

# Install dependencies in container
RUN pip install --no-cache-dir --upgrade -r /app/requirements.txt

# Copy ./asr folder into docker's /app folder (working directory)
COPY ./asr /app/asr

# Make port 8001 available
EXPOSE 8001

# Run asr_api.py when container launches
CMD ["uvicorn", "asr.asr_api:app", "--host", "0.0.0.0", "--port", "8001"]

