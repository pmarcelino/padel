#!/bin/bash

echo "🎾 Setting up Algarve Padel Market Research Tool"
echo "================================================"

# Check Python version
python_version=$(python3 --version 2>&1 | awk '{print $2}')
required_version="3.10"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "❌ Error: Python 3.10+ required, found $python_version"
    exit 1
fi

echo "✓ Python $python_version detected"

# Create virtual environment
echo ""
echo "Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
echo ""
echo "Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo ""
echo "Installing dependencies..."
pip install -r requirements.txt

# Create directory structure
echo ""
echo "Creating directory structure..."
mkdir -p data/{raw,processed,cache,exports}
mkdir -p tests/{test_models,test_collectors,test_processors,test_analyzers,test_utils,test_integration}
mkdir -p src/{models,collectors,enrichers,processors,analyzers,utils}
mkdir -p app/components
mkdir -p docs/images

# Create .gitkeep files for empty directories
touch data/cache/.gitkeep
touch data/exports/.gitkeep

# Copy environment template
if [ ! -f .env ]; then
    echo ""
    echo "Creating .env file from template..."
    cp .env.example .env
    echo "⚠️  IMPORTANT: Edit .env and add your GOOGLE_API_KEY"
else
    echo ""
    echo "✓ .env file already exists"
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Activate virtual environment: source venv/bin/activate"
echo "2. Edit .env and add your GOOGLE_API_KEY"
echo "3. Verify setup: python -c 'from src.config import settings; print(settings.project_root)'"
echo "4. Run tests: pytest tests/"
echo "5. Collect data: python scripts/collect_data.py"
echo "6. Process data: python scripts/process_data.py"
echo "7. Launch app: streamlit run app/app.py"

