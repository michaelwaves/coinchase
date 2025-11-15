#!/bin/bash

# Setup script for Dispute Service
echo "=================================="
echo "Dispute Service Setup"
echo "=================================="

# Check if .env exists
if [ ! -f .env ]; then
    echo "⚠️  .env file not found!"
    echo "📝 Creating .env from template..."
    cp ENV_TEMPLATE .env
    echo "✅ .env file created. Please edit it and add your ANTHROPIC_API_KEY"
    echo ""
    read -p "Press enter to open .env in nano editor (or Ctrl+C to skip)..."
    nano .env
fi

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.11 or higher."
    exit 1
fi

echo ""
echo "🐍 Python version:"
python3 --version

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed. Please install Node.js to use Claude Code."
    exit 1
fi

echo "📦 Node.js version:"
node --version

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo ""
    echo "🔨 Creating Python virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔌 Activating virtual environment..."
source venv/bin/activate

# Install Python dependencies
echo ""
echo "📦 Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Install Claude Code
echo ""
echo "🤖 Installing Claude Code..."
npm install -g @anthropic-ai/claude-code

echo ""
echo "=================================="
echo "✅ Setup Complete!"
echo "=================================="
echo ""
echo "To run the service:"
echo "  1. Make sure .env has your ANTHROPIC_API_KEY"
echo "  2. Activate virtual environment: source venv/bin/activate"
echo "  3. Run: python main.py"
echo ""
echo "Or use Docker:"
echo "  docker-compose up --build"
echo ""
echo "API Documentation will be available at:"
echo "  - http://localhost:8000/docs (Swagger)"
echo "  - http://localhost:8000/redoc (ReDoc)"
echo ""

