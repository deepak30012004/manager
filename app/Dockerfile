

# Use an official Python image
FROM python:3.10

# Set working directory inside container
WORKDIR /app

# Copy backend code to container
COPY . .

# Install Python libraries
RUN pip install --no-cache-dir -r requirements.txt

# Expose Flask port
EXPOSE 5000

# Run Flask server
CMD ["python", "app.py"]
