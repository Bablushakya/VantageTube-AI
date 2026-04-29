#!/bin/bash
# VantageTube AI - Backend Startup Script (macOS/Linux)

echo "========================================"
echo "  VantageTube AI - Backend Server"
echo "========================================"
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "[ERROR] Virtual environment not found!"
    echo ""
    echo "Please run setup first:"
    echo "  python3 -m venv venv"
    echo "  source venv/bin/activate"
    echo "  pip install -r requirements.txt"
    echo ""
    exit 1
fi

# Activate virtual environment
echo "[1/3] Activating virtual environment..."
source venv/bin/activate

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "[ERROR] .env file not found!"
    echo ""
    echo "Please create .env file with your Supabase credentials."
    echo "You can copy from .env.example"
    echo ""
    exit 1
fi

# Test connection
echo "[2/3] Testing connections..."
python test_connection.py
if [ $? -ne 0 ]; then
    echo ""
    echo "[ERROR] Connection tests failed!"
    echo "Please fix the issues above before starting the server."
    echo ""
    exit 1
fi

# Start server
echo ""
echo "[3/3] Starting FastAPI server..."
echo ""
echo "Server will start at: http://localhost:8000"
echo "API Documentation: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
