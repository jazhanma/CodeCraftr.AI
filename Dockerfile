# Use an official Python runtime
FROM python:3.10

# Set the working directory
WORKDIR /app

# Copy all files
COPY . /app/

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose the port
EXPOSE 8000

# Use Gunicorn for production
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:8000", "app:app"]

