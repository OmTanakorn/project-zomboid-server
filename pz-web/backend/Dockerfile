FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Set default env vars
ENV PZ_CONFIG_PATH=/home/steam/Zomboid
ENV PZ_DATA_PATH=/home/steam/pzserver
ENV SERVER_NAME=b42coop

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
