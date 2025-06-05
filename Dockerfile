# Use Python 3.11 slim image (similar to using a base .NET runtime image)
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy requirements first (for better Docker layer caching - like .csproj in .NET)
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port 5000
EXPOSE 5000

# Set environment variables
ENV FLASK_APP=app.py
ENV FLASK_ENV=production

# Run the application
CMD ["python", "app.py"]
