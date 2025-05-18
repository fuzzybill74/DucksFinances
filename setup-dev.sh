#!/bin/bash
set -e

echo "Setting up DucksFinances development environment..."

# Create virtual environment
echo "Creating virtual environment..."
python -m venv venv

# Activate virtual environment
if [ "$OSTYPE" == "msys" ] || [ "$OSTYPE" == "cygwin" ]; then
    # Windows
    source venv/Scripts/activate
else
    # Unix-like
    source venv/bin/activate
fi

# Install Python dependencies
echo "Installing Python dependencies..."
pip install --upgrade pip
pip install -r backend/requirements.txt

# Set up environment variables
echo "Setting up environment variables..."
if [ ! -f ".env" ]; then
    cp backend/.env.example .env
    echo "Created .env file. Please update it with your configuration."
fi

# Initialize database
echo "Initializing database..."
cd backend
flask db upgrade

# Install pre-commit hooks
echo "Setting up pre-commit hooks..."
pip install pre-commit
pre-commit install

echo ""
echo "🎉 Setup complete!"
echo "To start the development server, run:"
echo "  source venv/bin/activate  # or venv\\Scripts\\activate on Windows"
echo "  cd backend"
echo "  flask run"
echo ""
echo "The application will be available at http://localhost:5000"
