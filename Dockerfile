# Use an official Python runtime as a parent image
FROM python:3.12

# Set the working directory
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app/

# Install dependencies **without creating a virtual environment**
RUN pip install --no-cache-dir -r requirements.txt

# Expose the application port (change if necessary)
EXPOSE 8000

# Command to run the application (update if needed)
CMD ["python", "app.py"]
