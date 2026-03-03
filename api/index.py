import sys
import os

# Add the root directory and backend directory to the sys.path
# This allows importing 'backend.main' or other modules from the project structure
path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if path not in sys.path:
    sys.path.append(path)

path_backend = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend'))
if path_backend not in sys.path:
    sys.path.append(path_backend)

# Import the FastAPI app instance from our main backend file
from backend.main import app

# Vercel expects a 'handler' or the app instance itself at the top level of index.py
# Reference: https://vercel.com/docs/functions/runtimes/python
handler = app
