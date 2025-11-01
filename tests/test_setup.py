"""
Test suite for development setup validation.

Tests verify that all required files and directories are created correctly
by the setup process.
"""

import os
from pathlib import Path
import toml
import pytest


class TestDirectoryStructure:
    """Test that all required directories exist."""
    
    def test_data_directories_exist(self):
        """Verify data directory structure is created."""
        base_path = Path(__file__).parent.parent
        required_dirs = [
            "data",
            "data/raw",
            "data/processed",
            "data/cache",
            "data/exports",
        ]
        
        for dir_path in required_dirs:
            full_path = base_path / dir_path
            assert full_path.exists(), f"Directory {dir_path} should exist"
            assert full_path.is_dir(), f"{dir_path} should be a directory"
    
    def test_test_directories_exist(self):
        """Verify test directory structure is created."""
        base_path = Path(__file__).parent.parent
        required_dirs = [
            "tests",
            "tests/test_models",
            "tests/test_collectors",
            "tests/test_processors",
            "tests/test_analyzers",
            "tests/test_utils",
            "tests/test_integration",
        ]
        
        for dir_path in required_dirs:
            full_path = base_path / dir_path
            assert full_path.exists(), f"Directory {dir_path} should exist"
            assert full_path.is_dir(), f"{dir_path} should be a directory"
    
    def test_src_directories_exist(self):
        """Verify src directory structure is created."""
        base_path = Path(__file__).parent.parent
        required_dirs = [
            "src",
            "src/models",
            "src/collectors",
            "src/enrichers",
            "src/processors",
            "src/analyzers",
            "src/utils",
        ]
        
        for dir_path in required_dirs:
            full_path = base_path / dir_path
            assert full_path.exists(), f"Directory {dir_path} should exist"
            assert full_path.is_dir(), f"{dir_path} should be a directory"
    
    def test_app_directories_exist(self):
        """Verify app directory structure is created."""
        base_path = Path(__file__).parent.parent
        required_dirs = [
            "app",
            "app/components",
        ]
        
        for dir_path in required_dirs:
            full_path = base_path / dir_path
            assert full_path.exists(), f"Directory {dir_path} should exist"
            assert full_path.is_dir(), f"{dir_path} should be a directory"
    
    def test_docs_directories_exist(self):
        """Verify docs directory structure is created."""
        base_path = Path(__file__).parent.parent
        required_dirs = [
            "docs",
            "docs/images",
        ]
        
        for dir_path in required_dirs:
            full_path = base_path / dir_path
            assert full_path.exists(), f"Directory {dir_path} should exist"
            assert full_path.is_dir(), f"{dir_path} should be a directory"
    
    def test_gitkeep_files_exist(self):
        """Verify .gitkeep files in empty directories."""
        base_path = Path(__file__).parent.parent
        gitkeep_files = [
            "data/cache/.gitkeep",
            "data/exports/.gitkeep",
        ]
        
        for gitkeep_path in gitkeep_files:
            full_path = base_path / gitkeep_path
            assert full_path.exists(), f"File {gitkeep_path} should exist"
            assert full_path.is_file(), f"{gitkeep_path} should be a file"


class TestConfigurationFiles:
    """Test that configuration files are created and valid."""
    
    def test_env_example_exists(self):
        """Verify .env.example file exists."""
        base_path = Path(__file__).parent.parent
        env_example = base_path / ".env.example"
        assert env_example.exists(), ".env.example should exist"
        assert env_example.is_file(), ".env.example should be a file"
    
    def test_env_example_contains_required_keys(self):
        """Verify .env.example contains required configuration keys."""
        base_path = Path(__file__).parent.parent
        env_example = base_path / ".env.example"
        
        if env_example.exists():
            content = env_example.read_text()
            assert "GOOGLE_API_KEY" in content, ".env.example should contain GOOGLE_API_KEY"
    
    def test_requirements_txt_exists(self):
        """Verify requirements.txt file exists."""
        base_path = Path(__file__).parent.parent
        requirements = base_path / "requirements.txt"
        assert requirements.exists(), "requirements.txt should exist"
        assert requirements.is_file(), "requirements.txt should be a file"
    
    def test_requirements_txt_parseable(self):
        """Verify requirements.txt is parseable and contains dependencies."""
        base_path = Path(__file__).parent.parent
        requirements = base_path / "requirements.txt"
        
        if requirements.exists():
            content = requirements.read_text()
            lines = [line.strip() for line in content.split('\n') 
                    if line.strip() and not line.strip().startswith('#')]
            
            # Should have multiple dependencies
            assert len(lines) > 5, "requirements.txt should contain multiple dependencies"
            
            # Check for key dependencies
            required_packages = ['pandas', 'pydantic', 'streamlit', 'googlemaps']
            for package in required_packages:
                assert any(package in line for line in lines), \
                    f"requirements.txt should contain {package}"
    
    def test_pyproject_toml_exists(self):
        """Verify pyproject.toml file exists."""
        base_path = Path(__file__).parent.parent
        pyproject = base_path / "pyproject.toml"
        assert pyproject.exists(), "pyproject.toml should exist"
        assert pyproject.is_file(), "pyproject.toml should be a file"
    
    def test_pyproject_toml_valid(self):
        """Verify pyproject.toml is valid TOML format."""
        base_path = Path(__file__).parent.parent
        pyproject = base_path / "pyproject.toml"
        
        if pyproject.exists():
            try:
                config = toml.load(pyproject)
                assert 'project' in config, "pyproject.toml should have [project] section"
                assert 'name' in config['project'], "pyproject.toml should have project.name"
                assert config['project']['name'] == 'padel-research', \
                    "Project name should be 'padel-research'"
            except Exception as e:
                pytest.fail(f"pyproject.toml is not valid TOML: {e}")
    
    def test_pyproject_python_version(self):
        """Verify pyproject.toml specifies correct Python version."""
        base_path = Path(__file__).parent.parent
        pyproject = base_path / "pyproject.toml"
        
        if pyproject.exists():
            config = toml.load(pyproject)
            if 'project' in config and 'requires-python' in config['project']:
                requires_python = config['project']['requires-python']
                assert '3.10' in requires_python, \
                    "pyproject.toml should require Python 3.10+"
    
    def test_gitignore_exists(self):
        """Verify .gitignore file exists."""
        base_path = Path(__file__).parent.parent
        gitignore = base_path / ".gitignore"
        assert gitignore.exists(), ".gitignore should exist"
        assert gitignore.is_file(), ".gitignore should be a file"
    
    def test_gitignore_excludes_sensitive_files(self):
        """Verify .gitignore excludes sensitive and generated files."""
        base_path = Path(__file__).parent.parent
        gitignore = base_path / ".gitignore"
        
        if gitignore.exists():
            content = gitignore.read_text()
            
            # Should exclude common patterns
            required_patterns = [
                '__pycache__',
                'venv/',
                '.env',
                '.coverage',
            ]
            
            for pattern in required_patterns:
                assert pattern in content, \
                    f".gitignore should contain pattern: {pattern}"
            
            # Should exclude Python compiled files (*.pyc or *.py[cod])
            assert '*.pyc' in content or '*.py[cod]' in content, \
                ".gitignore should exclude Python compiled files"
            
            # Should NOT exclude .env.example
            assert '.env.example' not in content or '!.env.example' in content, \
                ".gitignore should not exclude .env.example"
    
    def test_readme_exists(self):
        """Verify README.md file exists."""
        base_path = Path(__file__).parent.parent
        readme = base_path / "README.md"
        assert readme.exists(), "README.md should exist"
        assert readme.is_file(), "README.md should be a file"
    
    def test_readme_has_basic_content(self):
        """Verify README.md has basic project information."""
        base_path = Path(__file__).parent.parent
        readme = base_path / "README.md"
        
        if readme.exists():
            content = readme.read_text()
            assert len(content) > 100, "README.md should have substantial content"
            assert "Padel" in content or "padel" in content, \
                "README.md should mention padel"


class TestSetupScript:
    """Test the setup.sh script."""
    
    def test_setup_script_exists(self):
        """Verify setup.sh file exists."""
        base_path = Path(__file__).parent.parent
        setup_script = base_path / "setup.sh"
        assert setup_script.exists(), "setup.sh should exist"
        assert setup_script.is_file(), "setup.sh should be a file"
    
    def test_setup_script_executable(self):
        """Verify setup.sh is executable."""
        base_path = Path(__file__).parent.parent
        setup_script = base_path / "setup.sh"
        
        if setup_script.exists():
            # Check if file has execute permission
            is_executable = os.access(setup_script, os.X_OK)
            assert is_executable, "setup.sh should have execute permissions"
    
    def test_setup_script_has_shebang(self):
        """Verify setup.sh has proper shebang."""
        base_path = Path(__file__).parent.parent
        setup_script = base_path / "setup.sh"
        
        if setup_script.exists():
            content = setup_script.read_text()
            lines = content.split('\n')
            assert lines[0].startswith('#!'), "setup.sh should start with shebang"
            assert 'bash' in lines[0], "setup.sh should use bash"

