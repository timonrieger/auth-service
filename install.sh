#!/bin/bash


# Install requirements
pip install -r requirements.txt

# Check if GITHUB_TOKEN environment variable is set
if [ -z "$GITHUB_TOKEN" ]; then
  echo "Error: GITHUB_TOKEN environment variable is not set."
  exit 1
fi

# Install the package from GitHub
pip install git+https://$GITHUB_TOKEN@github.com/timonrieger/database-service.git
