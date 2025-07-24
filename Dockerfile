# Use the official Python image
FROM python:3.10-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set work directory
WORKDIR /app

# Install system dependencies (for audio, TTS support, and git)
RUN apt-get update && \
    apt-get install -y git ffmpeg portaudio19-dev python3-pyaudio python3-dev build-essential espeak && \
    rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Copy project files
COPY . .

# Expose the port Streamlit uses
EXPOSE 8501

# Streamlit-specific config (optional, but recommended for Render)
ENV STREAMLIT_SERVER_HEADLESS=true
ENV STREAMLIT_SERVER_PORT=8501
ENV STREAMLIT_SERVER_ENABLECORS=false

# Command to run the Streamlit app on the correct port/address for Railway
CMD ["sh", "-c", "streamlit run app/web.py --server.port=$PORT --server.address=0.0.0.0"]