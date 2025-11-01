# Story 0.0: Development Setup

## Overview

**Priority**: P0 (Blocker)  
**Dependencies**: None  
**Estimated Effort**: Small (2-3 hours)  
**Layer**: 0 (Foundation)

## Description

Create the foundational development environment setup including directory structure, dependency management, version control configuration, and automated setup scripts. This story ensures that developers can quickly bootstrap the project and start contributing with a consistent, reproducible environment.

## Business Value

- Reduces onboarding time for new developers
- Ensures consistent development environments
- Automates repetitive setup tasks
- Prevents common configuration errors
- Establishes project standards from the start

## Input Contract

- Fresh git clone or empty project directory
- Python 3.10+ installed on system
- Git installed

## Output Contract

A fully configured development environment including:
- Project directory structure
- Python virtual environment
- All dependencies installed
- Configuration templates
- Version control setup
- Ready to run development commands

## Deliverables

### 1. setup.sh Script

Automated setup script for Unix-based systems (macOS, Linux):

```bash
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
```

### 2. .gitignore

Comprehensive gitignore for Python projects:

```gitignore
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
share/python-wheels/
*.egg-info/
.installed.cfg
*.egg
MANIFEST

# Virtual Environment
venv/
env/
ENV/
env.bak/
venv.bak/

# IDEs
.vscode/
.idea/
*.swp
*.swo
*~
.DS_Store

# Environment variables
.env
.env.local

# Data files (keep structure, ignore data)
data/raw/*.csv
data/processed/*.csv
data/cache/*.pkl
data/cache/*.json
data/exports/*.csv
data/exports/*.xlsx

# Keep directory structure
!data/raw/.gitkeep
!data/processed/.gitkeep
!data/cache/.gitkeep
!data/exports/.gitkeep

# Testing
.coverage
htmlcov/
.pytest_cache/
.tox/
coverage.xml
*.cover

# Jupyter
.ipynb_checkpoints/
*.ipynb

# Logs
*.log

# Streamlit
.streamlit/secrets.toml
```

### 3. pyproject.toml

Project metadata and configuration:

```toml
[build-system]
requires = ["setuptools>=68.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "padel-research"
version = "0.1.0"
description = "Algarve Padel Field Market Research Tool"
readme = "README.md"
requires-python = ">=3.10"
authors = [
    {name = "Your Name", email = "your.email@example.com"}
]
classifiers = [
    "Development Status :: 3 - Alpha",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
]

dependencies = [
    "pandas>=2.1.0",
    "numpy>=1.25.0",
    "googlemaps>=4.10.0",
    "pytrends>=4.9.0",
    "requests>=2.31.0",
    "requests-cache>=1.1.0",
    "geopy>=2.3.0",
    "folium>=0.14.0",
    "plotly>=5.16.0",
    "streamlit>=1.27.0",
    "streamlit-folium>=0.15.0",
    "pydantic>=2.3.0",
    "pydantic-settings>=2.0.0",
    "openai>=1.12.0",
    "anthropic>=0.18.0",
    "python-dotenv>=1.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.4.0",
    "pytest-cov>=4.1.0",
    "pytest-benchmark>=4.0.0",
    "pytest-mock>=3.11.0",
    "black>=23.7.0",
    "mypy>=1.5.0",
    "ruff>=0.0.285",
]

[tool.black]
line-length = 100
target-version = ["py310", "py311", "py312"]

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_functions = ["test_*"]
addopts = "-v --cov=src --cov-report=term-missing --cov-report=html"

[tool.mypy]
python_version = "3.10"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = false
ignore_missing_imports = true

[tool.ruff]
line-length = 100
select = ["E", "F", "I", "N", "W"]
ignore = ["E501"]
```

### 4. requirements.txt

Dependency specification:

```txt
# Core Dependencies
pandas==2.1.0
numpy==1.25.0

# Google APIs
googlemaps==4.10.0
pytrends==4.9.0

# HTTP & Caching
requests==2.31.0
requests-cache==1.1.0

# Geospatial
geopy==2.3.0
folium==0.14.0

# Visualization
plotly==5.16.0
streamlit==1.27.0
streamlit-folium==0.15.0

# Data Validation
pydantic==2.3.0
pydantic-settings==2.0.0

# LLM APIs (optional)
openai==1.12.0
anthropic==0.18.0

# Environment
python-dotenv==1.0.0

# Development (optional)
pytest==7.4.0
pytest-cov==4.1.0
pytest-benchmark==4.0.0
pytest-mock==3.11.0
black==23.7.0
mypy==1.5.0
ruff==0.0.285
```

### 5. README.md (Basic Template)

Placeholder README to be enhanced in Story 7.2:

```markdown
# Algarve Padel Market Research Tool

A Python-based data collection and analysis tool for identifying optimal locations for new padel facilities in Algarve, Portugal.

## Quick Start

```bash
# Clone repository
git clone <repository-url>
cd padel-research

# Run setup script
chmod +x setup.sh
./setup.sh

# Configure API key
# Edit .env and add your GOOGLE_API_KEY

# Run data collection
python scripts/collect_data.py

# Process data
python scripts/process_data.py

# Launch web app
streamlit run app/app.py
```

## Documentation

- [API Setup Guide](docs/API_SETUP.md) - Coming in Story 7.2
- [Usage Guide](docs/USAGE.md) - Coming in Story 7.2
- [Technical Design](technical-design.md)

## Requirements

- Python 3.10+
- Google Places API key

See [requirements.txt](requirements.txt) for full dependency list.

## License

MIT License (or your preferred license)
```

## Acceptance Criteria

### Setup Script
- [ ] `setup.sh` is executable and runs without errors
- [ ] Checks for Python 3.10+ before proceeding
- [ ] Creates virtual environment successfully
- [ ] Installs all dependencies from requirements.txt
- [ ] Creates complete directory structure
- [ ] Creates .env from .env.example if not exists
- [ ] Provides clear next steps to user
- [ ] Handles errors gracefully (e.g., missing Python)
- [ ] Works on macOS and Linux
- [ ] Completes in < 5 minutes

### .gitignore
- [ ] Excludes all Python bytecode and cache files
- [ ] Excludes virtual environment directories
- [ ] Excludes .env file (but keeps .env.example)
- [ ] Excludes data files (CSV, cache) but keeps directory structure
- [ ] Excludes IDE-specific files
- [ ] Includes .gitkeep files for empty directories
- [ ] Tested: No sensitive files committed

### pyproject.toml
- [ ] Contains correct project metadata
- [ ] Lists all required dependencies
- [ ] Includes dev dependencies separately
- [ ] Configures Black, pytest, mypy, ruff
- [ ] Python version constraint correct (>=3.10)

### requirements.txt
- [ ] Lists all production dependencies with versions
- [ ] Includes development dependencies
- [ ] Versions are compatible with each other
- [ ] Can be installed with `pip install -r requirements.txt`
- [ ] No conflicting package versions

### Directory Structure
- [ ] All required directories created by setup script
- [ ] .gitkeep files in empty directories
- [ ] Structure matches technical design document

### Documentation
- [ ] Basic README.md created (enhanced in Story 7.2)
- [ ] README includes quick start instructions
- [ ] README links to other documentation

## Files to Create

```
setup.sh                    # Unix setup script
.gitignore                  # Git ignore rules
pyproject.toml              # Project metadata and tool configuration
requirements.txt            # Python dependencies
README.md                   # Basic project README (template)
.env.example                # Environment variable template (expanded from Story 0.2)
```

## Testing Requirements

### Automated Tests
- [ ] Test directory creation works
- [ ] Test .env creation from template
- [ ] Test requirements.txt is parseable
- [ ] Test pyproject.toml is valid TOML

### Manual Testing
- [ ] Fresh clone → run setup.sh → verify success
- [ ] Test on macOS
- [ ] Test on Linux (Ubuntu/Debian)
- [ ] Verify virtual environment activates correctly
- [ ] Verify all dependencies install without conflicts
- [ ] Test that git ignores correct files

## Technical Notes

### Python Version Requirements

Minimum Python 3.10 required for:
- Modern type hints (`X | Y` union syntax)
- Structural pattern matching (if used)
- Better error messages
- Performance improvements

### Virtual Environment

Use built-in `venv` module (no external dependency):
- Creates isolated environment
- Prevents system Python pollution
- Easy to recreate if corrupted

### Dependency Pinning Strategy

Pin exact versions in requirements.txt for reproducibility:
- Major.Minor.Patch format
- Update periodically for security patches
- Test compatibility before updating

### Platform Support

**Primary Support**:
- macOS (Apple Silicon and Intel)
- Linux (Ubuntu 20.04+, Debian 11+)

**Secondary Support** (manual setup):
- Windows 10/11 (users must adapt setup script)

## Windows Alternative

Since setup.sh is for Unix, provide Windows instructions in README:

```powershell
# Windows Setup (PowerShell)
python -m venv venv
.\venv\Scripts\Activate
pip install --upgrade pip
pip install -r requirements.txt
# Create directories manually or use provided setup script
```

## Edge Cases

1. **Python 2.x installed as `python`**: Script uses `python3` explicitly
2. **No Python installed**: Script exits with error message
3. **Insufficient permissions**: User may need sudo for some operations
4. **Existing venv**: Script should detect and ask before overwriting
5. **Missing pip**: Suggest installing via get-pip.py

## Success Criteria

This story is complete when:
- [ ] Fresh clone can be set up in < 5 minutes
- [ ] All dependencies install without errors
- [ ] Directory structure matches technical design
- [ ] Git ignores sensitive and generated files
- [ ] Developer can immediately run tests
- [ ] Setup script provides helpful error messages
- [ ] Works on both macOS and Linux

## Related Stories

**Enables All Other Stories**: This is the foundation that must be completed before any implementation work begins.

**Blocked By**: None

**Blocks**: All stories (0.1-7.2) depend on having the environment set up

## Future Enhancements

- Docker containerization (Story 8.1)
- Windows batch script equivalent
- Automated dependency updates
- Pre-commit hooks configuration
- CI/CD pipeline setup
- Development database seeding

## Definition of Done

- [ ] All files created and tested
- [ ] Setup script runs successfully on fresh clone
- [ ] Manual testing completed on macOS and Linux
- [ ] .gitignore prevents committing sensitive files
- [ ] Dependencies install without conflicts
- [ ] Virtual environment works correctly
- [ ] Documentation in README explains setup process
- [ ] New developer can onboard in < 10 minutes

---

**Note**: This story should be completed FIRST before any other story. It's the foundation for all development work.

