#!/usr/bin/env bash
# build.sh - Custom build script for Render

# Exit on error
set -o errexit

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

# Try to install the rest of the requirements
echo "Installing remaining packages..."
pip install --no-deps qdrant-client==1.6.0 || true
pip install -r requirements.txt --no-build-isolation || true

# Make sure the app can run even if some packages fail to install
echo "Installation completed with some packages possibly missing."
