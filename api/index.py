import sys
import os

# Agregar raíz al sys.path para importaciones en entornos serverless
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.app.main import app

# Vercel Serverless Function Entry Point
app = app
