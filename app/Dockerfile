FROM python:3.11-slim

# Install curl for health checks
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

#create a non-root user for security
RUN useradd -m appuser 

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

#copy the app code
COPY . .

#switch to non root user
USER appuser

#tell docker to run your app in port 3000
EXPOSE 3000

#stat the app
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "3000"]
