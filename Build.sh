#!/bin/bash
set -e

echo "Starting build process..."

# Upgrade core pip tools first
echo "Upgrading pip, setuptools, and wheel..."
python -m pip install --upgrade pip setuptools wheel

# Clear pip cache to avoid corrupted packages
echo "Clearing pip cache..."
pip cache purge

# Install build dependencies
echo "Installing build dependencies..."
pip install build

# Install project dependencies
echo "Installing project dependencies from requirements.txt..."
pip install -r requirements.txt

echo "Build completed successfully!"