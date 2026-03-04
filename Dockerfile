FROM python:3.10-slim

# Install necessary system libraries for OpenCV and PaddleOCR
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    libgl1-mesa-glx \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Set up a new user named "user" with user ID 1000
# (Hugging Face Spaces runs containers as a non-root user for security)
RUN useradd -m -u 1000 user

# Switch to the "user" user
USER user
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH

# Set the working directory to the user's home directory
WORKDIR $HOME/app

# Copy the requirements file into the container
COPY --chown=user requirements.txt $HOME/app/

# Install pip dependencies
# We use the --extra-index-url flag to install CPU-only versions of PyTorch
# This is crucial because Hugging Face's Free Tier runs on CPU and CUDA binaries are massive
RUN pip install --no-cache-dir -r requirements.txt --extra-index-url https://download.pytorch.org/whl/cpu

# Copy the rest of your application code
COPY --chown=user . $HOME/app/

# Ensure the temp and data directories exist so the app doesn't crash on upload
RUN mkdir -p $HOME/app/temp && mkdir -p $HOME/app/data

# Hugging Face Spaces route internet traffic to port 7860 by default
EXPOSE 7860

# Command to run your FastAPI application using Uvicorn
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "7860"]
