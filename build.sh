#!/usr/bin/env bash
# build.sh - Custom build script for Render

# Don't exit on error so we can continue and identify the problematic package
set +o errexit

# Install system dependencies for building Python packages
apt-get update
apt-get install -y build-essential python3-dev

# Install Python dependencies
pip install --upgrade pip
pip install wheel setuptools

# Install grpcio separately to avoid issues
pip install grpcio==1.54.0 --no-build-isolation

# Install packages that might depend on grpcio first
pip install protobuf==3.20.3

# Explicitly avoid grpcio-tools
export GRPC_PYTHON_BUILD_SYSTEM_OPENSSL=1
export GRPC_PYTHON_BUILD_WITH_CYTHON=1

# Install minimal requirements first
pip install -r requirements-minimal.txt --no-build-isolation

# Try to install packages one by one to identify which one requires grpcio-tools
echo "Installing packages one by one to identify which requires grpcio-tools..."

# Function to check if a package requires grpcio-tools
check_package() {
  echo "Checking $1..."
  pip install $1 --no-build-isolation --no-deps
  if [ $? -ne 0 ]; then
    echo "ERROR: Failed to install $1"
  else
    echo "Successfully installed $1"
  fi
  echo ""
}

# Check each package individually
check_package "alembic==1.13.3"
check_package "beautifulsoup4==4.12.3"
check_package "cohere==5.13.4"
check_package "faiss_cpu==1.8.0"
check_package "fitz==0.0.1.dev2"
check_package "Flask_SocketIO==5.3.6"
check_package "google_api_python_client==2.149.0"
check_package "google_auth_oauthlib==1.2.1"
# Commented out groq as it might be the culprit
# check_package "groq==0.17.0"
check_package "huggingface_hub==0.26.3"
check_package "nltk==3.8.1"
check_package "numpy==1.23.5"
check_package "pymongo==4.10.1"
check_package "pymupdf==1.25.1"
check_package "qdrant-client==1.6.0"
check_package "rank_bm25==0.2.2"
check_package "scikit_learn==1.1.3"
check_package "sentence_transformers==3.0.1"
check_package "SpeechRecognition==3.8.1"
check_package "torch==2.5.1"
check_package "transformers==4.46.3"

# Now try to install the full requirements
echo "Installing full requirements..."
pip install -r requirements.txt --no-build-isolation || {
  echo "Failed to install full requirements, trying with reduced set..."
  pip install -r requirements-no-grpc.txt --no-build-isolation
}

# Make sure the app can run even if some packages fail to install
echo "Installation completed with some packages possibly missing."

# Use the minimal app.py if needed
if [ $? -ne 0 ]; then
  echo "Using minimal app.py due to installation issues"
  cp app_minimal.py app.py
fi
