# Use an official Python runtime
FROM python:3.10

# Set the working directory inside the container
WORKDIR /app

# Copy all files
COPY . /app/

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Ensure database file exists inside the container
RUN touch /app/database.db

# Expose the port Flask runs on
EXPOSE 8000

# Run the Flask app
CMD ["python", "app.py"]
