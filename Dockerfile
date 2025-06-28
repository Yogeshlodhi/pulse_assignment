FROM python:3.10-slim

# Set the working directory
WORKDIR /app

# Install basic dependencies (no GUI, no Chromium)
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    wget \
    unzip \
    && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY . .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Set default command
CMD ["python", "main.py"]
