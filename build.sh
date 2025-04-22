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
pip install -r requirements.txt
