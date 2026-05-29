#!/bin/bash
# Build script for Vercel deployment
set -e

# Install dependencies
pip install -r requirements.txt

# Run collectstatic
python manage.py collectstatic --noinput

# Run migrations
python manage.py migrate --noinput
