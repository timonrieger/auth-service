#!/bin/bash

# Check if GITHUB_TOKEN environment variable is set
if [ -z "$GITHUB_TOKEN" ]; then
  echo "Error: GITHUB_TOKEN environment variable is not set."
  exit 1
fi

# Install requirements
pip install -r requirements.txt

# Install the package from GitHub
pip install git+https://$GITHUB_TOKEN@github.com/timonrieger/database-service.git